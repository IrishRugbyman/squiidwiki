"""Internal-consistency checks over one universe: rows that contradict each other.

Each check is a plain function `check_x(data) -> list[Anomaly]` over a
`UniverseData` snapshot loaded once by `load_universe_data`, so the admin
endpoint, a CLI or a test can run any subset without a request in the way:

    data = await load_universe_data(session, universe_id)
    findings = run_checks(data)                      # every check
    findings = run_checks(data, kinds={"dead_without_death_record"})

Dates are FuzzyDates, so every comparison goes through `fuzzy_range`: a date
is the span of days it could mean (a Y date is the whole year), widened by a
year on each side when marked approximate, and two dates conflict only when
their spans do not overlap. "March 2021" vs "2021" is never a conflict;
"2021" vs "2023" is. False positives cost the owner's trust in the list, so
every check errs towards silence.
"""

import calendar
import datetime
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemberStatus, ParticipantOutcome, ParticipantRole, SetStatus
from app.models.citation import Citation
from app.models.gang_set import GangSet
from app.models.incident import Incident, IncidentParticipant, IncidentSetParticipant
from app.models.member import Member, MemberSet

# How far back an incident counts as "recent" for an extinct set.
RECENT_DAYS = 730


@dataclass
class Anomaly:
    kind: str
    entity_type: str  # member | set | incident
    entity_id: uuid.UUID
    slug: str | None
    display_name: str
    message: str
    # The other row the contradiction is with (the later incident, the set).
    related_type: str | None = None
    related_id: uuid.UUID | None = None
    related_label: str | None = None


# Every check, in the order the page lists them, with a one-line description.
CHECKS: dict[str, str] = {}


def _check(kind: str, title: str):
    def wrap(fn):
        CHECKS[kind] = title
        fn.kind = kind
        _REGISTRY.append(fn)
        return fn

    return wrap


_REGISTRY: list = []


# ---------------------------------------------------------------------------
# FuzzyDate spans
# ---------------------------------------------------------------------------


def fuzzy_range(d: dict | None) -> tuple[datetime.date, datetime.date] | None:
    """The first and last day a FuzzyDate dict could mean, or None if unknown."""
    if not d or not isinstance(d, dict):
        return None
    year = d.get("year")
    precision = d.get("precision") or ("Y" if year else "UNKNOWN")
    if not year or precision == "UNKNOWN":
        return None
    month, day = d.get("month"), d.get("day")
    try:
        if precision == "YMD" and month and day:
            lo = hi = datetime.date(year, month, day)
        elif precision in ("YM", "YMD") and month:
            lo = datetime.date(year, month, 1)
            hi = datetime.date(year, month, calendar.monthrange(year, month)[1])
        else:
            lo, hi = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
    except ValueError:  # a malformed legacy date: say nothing about it
        return None
    if d.get("approx") or d.get("circa_text"):
        lo -= datetime.timedelta(days=366)
        hi += datetime.timedelta(days=366)
    return lo, hi


def strictly_before(a: dict | None, b: dict | None) -> bool:
    """True only when every day `a` could mean is before every day `b` could."""
    ra, rb = fuzzy_range(a), fuzzy_range(b)
    return bool(ra and rb and ra[1] < rb[0])


def display(d: dict | None) -> str:
    from app.core.fuzzy_date import FuzzyDate

    try:
        return FuzzyDate(**d).display() if d else "unknown"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class UniverseData:
    members: dict[uuid.UUID, Member] = field(default_factory=dict)
    sets: dict[uuid.UUID, GangSet] = field(default_factory=dict)
    incidents: dict[uuid.UUID, Incident] = field(default_factory=dict)
    participants: list[IncidentParticipant] = field(default_factory=list)
    set_participants: list[IncidentSetParticipant] = field(default_factory=list)
    spells: list[MemberSet] = field(default_factory=list)
    sourced_members: set[uuid.UUID] = field(default_factory=set)
    sourced_incidents: set[uuid.UUID] = field(default_factory=set)
    today: datetime.date = field(default_factory=datetime.date.today)


async def load_universe_data(session: AsyncSession, universe_id: uuid.UUID) -> UniverseData:
    data = UniverseData()

    async def rows(stmt):
        return (await session.execute(stmt)).scalars().all()

    data.members = {
        m.id: m for m in await rows(select(Member).where(Member.universe_id == universe_id))
    }
    data.sets = {
        s.id: s for s in await rows(select(GangSet).where(GangSet.universe_id == universe_id))
    }
    data.incidents = {
        i.id: i for i in await rows(select(Incident).where(Incident.universe_id == universe_id))
    }
    inc_ids = list(data.incidents)
    mem_ids = list(data.members)
    if inc_ids:
        data.participants = list(
            await rows(
                select(IncidentParticipant).where(IncidentParticipant.incident_id.in_(inc_ids))
            )
        )
        data.set_participants = list(
            await rows(
                select(IncidentSetParticipant).where(
                    IncidentSetParticipant.incident_id.in_(inc_ids)
                )
            )
        )
        # A citation always lives in its record's universe.
        data.sourced_incidents = set(
            await rows(
                select(Citation.incident_id).where(
                    Citation.universe_id == universe_id, Citation.incident_id.is_not(None)
                )
            )
        )
    if mem_ids:
        data.spells = list(await rows(select(MemberSet).where(MemberSet.member_id.in_(mem_ids))))
        data.sourced_members = set(
            await rows(
                select(Citation.member_id).where(
                    Citation.universe_id == universe_id, Citation.member_id.is_not(None)
                )
            )
        )
    return data


def _member_finding(kind: str, m: Member, message: str, **related) -> Anomaly:
    return Anomaly(
        kind=kind,
        entity_type="member",
        entity_id=m.id,
        slug=m.slug,
        display_name=m.display_name,
        message=message,
        **related,
    )


def _incident_label(inc: Incident) -> str:
    kind = inc.type.value if hasattr(inc.type, "value") else str(inc.type)
    return f"{kind.title()} {display(inc.date)}"


def _incident_related(inc: Incident) -> dict:
    return {"related_type": "incident", "related_id": inc.id, "related_label": _incident_label(inc)}


def _is(value, enum_member) -> bool:
    return value == enum_member or value == enum_member.value


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


@_check("set_member_unsourced", "In a set, with nothing citing the member")
def check_set_member_unsourced(data: UniverseData) -> list[Anomaly]:
    """A member in a set (an open spell) with no source anywhere behind them.

    `member_set` has no source column, so "this link was added without a
    source" cannot be asked of the link itself. The nearest honest question is
    whether anything cites the member at all: a `member_source` row, or a
    source on any incident they are a participant in. Reserved sets (Unknown,
    Police, Civilian) are skipped: parking someone in Unknown is not a claim.
    """
    backed = set(data.sourced_members)
    for p in data.participants:
        if p.incident_id in data.sourced_incidents:
            backed.add(p.member_id)
    out = []
    seen: set[uuid.UUID] = set()
    for sp in data.spells:
        if sp.until_date is not None or sp.member_id in backed or sp.member_id in seen:
            continue
        s = data.sets.get(sp.set_id)
        m = data.members.get(sp.member_id)
        if s is None or m is None or s.is_reserved:
            continue
        seen.add(m.id)
        out.append(
            _member_finding(
                "set_member_unsourced",
                m,
                f"In {s.name}, but no source cites this member or any incident they are in.",
                related_type="set",
                related_id=s.id,
                related_label=s.name,
            )
        )
    return out


@_check("dead_without_death_record", "Dead, with no date of death and no death incident")
def check_dead_without_death_record(data: UniverseData) -> list[Anomaly]:
    return [
        _member_finding(
            "dead_without_death_record",
            m,
            "Status is DEAD but there is no date of death and no linked death incident.",
        )
        for m in data.members.values()
        if _is(m.status, MemberStatus.DEAD)
        and fuzzy_range(m.date_of_death) is None
        and not (m.date_of_death or {}).get("circa_text")
        and m.death_incident_id is None
    ]


@_check("incident_after_death", "In an incident dated after their death")
def check_incident_after_death(data: UniverseData) -> list[Anomaly]:
    """A member killed in one incident (or with a date of death) who is a
    participant in an incident unambiguously later.

    A member can carry several death records (a KILLED row, a date of death);
    the finding needs the incident to be later than ALL of them, so one record
    that could still overlap it keeps the check silent.
    """
    deaths: dict[uuid.UUID, list[tuple[dict, str]]] = defaultdict(list)
    for p in data.participants:
        if _is(p.outcome, ParticipantOutcome.KILLED):
            inc = data.incidents.get(p.incident_id)
            if inc and inc.date:
                deaths[p.member_id].append((inc.date, f"killed in the {_incident_label(inc)}"))
    for m in data.members.values():
        if m.date_of_death:
            deaths[m.id].append((m.date_of_death, f"date of death {display(m.date_of_death)}"))

    out = []
    for p in data.participants:
        m, inc = data.members.get(p.member_id), data.incidents.get(p.incident_id)
        if m is None or inc is None or m.id not in deaths:
            continue
        # The member must be dead by EVERY record we hold, not only one of them,
        # so take the death record that ends latest.
        for d, _ in deaths[m.id]:
            if not strictly_before(d, inc.date):
                break
        else:
            d, why = deaths[m.id][0]
            out.append(
                _member_finding(
                    "incident_after_death",
                    m,
                    f"Participant ({_role(p)}) in the {_incident_label(inc)}, but {why}.",
                    **_incident_related(inc),
                )
            )
    return out


@_check("incident_before_birth", "In an incident dated before their birth")
def check_incident_before_birth(data: UniverseData) -> list[Anomaly]:
    out = []
    for p in data.participants:
        m, inc = data.members.get(p.member_id), data.incidents.get(p.incident_id)
        if m is None or inc is None or not m.dob:
            continue
        if strictly_before(inc.date, m.dob):
            out.append(
                _member_finding(
                    "incident_before_birth",
                    m,
                    f"Participant ({_role(p)}) in the {_incident_label(inc)}, "
                    f"but born {display(m.dob)}.",
                    **_incident_related(inc),
                )
            )
    return out


@_check("extinct_set_recent_incident", "Extinct set with a recent incident")
def check_extinct_set_recent_incident(data: UniverseData) -> list[Anomaly]:
    """An EXTINCT set involved in an incident within the last RECENT_DAYS.

    Sets carry no extinction date, so "after it went extinct" cannot be asked;
    "recently" can. Involvement means the set itself is a participant, or a
    shooter or assist whose current primary set it is. An incident is recent
    only if its EARLIEST possible day is inside the window.
    """
    cutoff = data.today - datetime.timedelta(days=RECENT_DAYS)

    def recent(inc: Incident | None) -> bool:
        r = fuzzy_range(inc.date) if inc else None
        return bool(r and r[0] >= cutoff)

    primary_set = {
        sp.member_id: sp.set_id for sp in data.spells if sp.until_date is None and sp.is_primary
    }
    hits: dict[tuple[uuid.UUID, uuid.UUID], str] = {}
    for sp in data.set_participants:
        hits.setdefault((sp.set_id, sp.incident_id), "the set is a participant")
    for p in data.participants:
        if _is(p.role, ParticipantRole.SHOOTER) or _is(p.role, ParticipantRole.ASSISTED):
            sid = primary_set.get(p.member_id)
            if sid:
                m = data.members[p.member_id]
                hits.setdefault((sid, p.incident_id), f"{m.display_name} ({_role(p)})")

    out = []
    for (sid, iid), how in hits.items():
        s, inc = data.sets.get(sid), data.incidents.get(iid)
        if s is None or not _is(s.status, SetStatus.EXTINCT) or not recent(inc):
            continue
        out.append(
            Anomaly(
                kind="extinct_set_recent_incident",
                entity_type="set",
                entity_id=s.id,
                slug=s.slug,
                display_name=s.name,
                message=f"Marked EXTINCT, but involved in the {_incident_label(inc)}: {how}.",
                **_incident_related(inc),
            )
        )
    return out


@_check("death_incident_but_not_dead", "Linked to a death incident but not DEAD")
def check_death_incident_but_not_dead(data: UniverseData) -> list[Anomaly]:
    out = []
    for m in data.members.values():
        if m.death_incident_id and not _is(m.status, MemberStatus.DEAD):
            inc = data.incidents.get(m.death_incident_id)
            status = m.status.value if hasattr(m.status, "value") else m.status
            out.append(
                _member_finding(
                    "death_incident_but_not_dead",
                    m,
                    f"Has a death incident but status is {status}.",
                    **(_incident_related(inc) if inc else {}),
                )
            )
    return out


@_check("killed_but_not_dead", "Killed in an incident but not DEAD")
def check_killed_but_not_dead(data: UniverseData) -> list[Anomaly]:
    """The death sync sets DEAD; un-killing is manual and should also change
    the outcome. A KILLED row on a member who is not DEAD means one half of
    that edit was done."""
    out = []
    for p in data.participants:
        m, inc = data.members.get(p.member_id), data.incidents.get(p.incident_id)
        if m and inc and _is(p.outcome, ParticipantOutcome.KILLED):
            if not _is(m.status, MemberStatus.DEAD):
                status = m.status.value if hasattr(m.status, "value") else m.status
                out.append(
                    _member_finding(
                        "killed_but_not_dead",
                        m,
                        f"Outcome KILLED in the {_incident_label(inc)}, but status is {status}.",
                        **_incident_related(inc),
                    )
                )
    return out


@_check("killed_twice", "Killed in more than one incident")
def check_killed_twice(data: UniverseData) -> list[Anomaly]:
    killed: dict[uuid.UUID, list[Incident]] = defaultdict(list)
    for p in data.participants:
        inc = data.incidents.get(p.incident_id)
        if inc and _is(p.outcome, ParticipantOutcome.KILLED):
            killed[p.member_id].append(inc)
    out = []
    for mid, incs in killed.items():
        m = data.members.get(mid)
        if m is None or len(incs) < 2:
            continue
        names = ", ".join(_incident_label(i) for i in incs)
        out.append(
            _member_finding(
                "killed_twice",
                m,
                f"Outcome KILLED in {len(incs)} incidents: {names}.",
                **_incident_related(incs[-1]),
            )
        )
    return out


@_check("death_before_birth", "Date of death before date of birth")
def check_death_before_birth(data: UniverseData) -> list[Anomaly]:
    return [
        _member_finding(
            "death_before_birth",
            m,
            f"Died {display(m.date_of_death)}, but born {display(m.dob)}.",
        )
        for m in data.members.values()
        if strictly_before(m.date_of_death, m.dob)
    ]


@_check("spell_ends_before_start", "Set spell that ends before it starts")
def check_spell_ends_before_start(data: UniverseData) -> list[Anomaly]:
    out = []
    for sp in data.spells:
        m, s = data.members.get(sp.member_id), data.sets.get(sp.set_id)
        if m and s and strictly_before(sp.until_date, sp.from_date):
            out.append(
                _member_finding(
                    "spell_ends_before_start",
                    m,
                    f"Spell in {s.name} runs from {display(sp.from_date)} "
                    f"to {display(sp.until_date)}.",
                    related_type="set",
                    related_id=s.id,
                    related_label=s.name,
                )
            )
    return out


def _role(p: IncidentParticipant) -> str:
    role = p.role.value if hasattr(p.role, "value") else str(p.role)
    return role.lower()


def run_checks(data: UniverseData, kinds: set[str] | None = None) -> list[Anomaly]:
    """Run every check (or only `kinds`), in CHECKS order."""
    out: list[Anomaly] = []
    for fn in _REGISTRY:
        if kinds is None or fn.kind in kinds:
            out.extend(fn(data))
    return out
