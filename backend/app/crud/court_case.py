import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import CaseDisposition
from app.core.slug import slugify
from app.models.court_case import (
    CourtCase,
    CourtCaseDefendant,
    CourtCaseIncident,
    CourtCaseSet,
    CourtCaseSource,
)
from app.models.gang_set import GangSet
from app.models.incident import Incident, IncidentParticipant
from app.models.member import Member, MemberIncarceration
from app.models.source import Source
from app.schemas.court_case import (
    CourtCaseCreate,
    CourtCaseListItem,
    CourtCaseUpdate,
    DefendantCreate,
    DefendantUpdate,
)

# A defendant is cleared of an incident only by an acquittal no other case
# contradicts: acquitted by the state and convicted federally of the same
# killing is not cleared.
_GUILTY = (CaseDisposition.CONVICTED.value, CaseDisposition.PLEADED.value)


def _fuzzy(fd) -> dict | None:
    return fd.model_dump() if fd is not None else None


async def _unique_slug(
    session: AsyncSession, universe_id: uuid.UUID, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug, n = base, 2
    while True:
        q = select(CourtCase.id).where(CourtCase.universe_id == universe_id, CourtCase.slug == slug)
        if exclude_id:
            q = q.where(CourtCase.id != exclude_id)
        if (await session.execute(q)).first() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def _check_links(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    set_ids: list[uuid.UUID] | None = None,
    source_ids: list[uuid.UUID] | None = None,
    incident_ids: list[uuid.UUID] | None = None,
    parent_case_id: uuid.UUID | None = None,
) -> None:
    """Refuse links a case cannot hold, with a 422 naming them.

    Sets and sources must be in the case's universe: a set is local to its
    streets, and sources are scoped per universe. Incidents and a parent case
    may be in any universe, as a case's defendants may: a Michigan case can
    cover an Ohio shooting.
    """
    for ids, model, label, scoped in (
        (set_ids, GangSet, "sets", True),
        (source_ids, Source, "sources", True),
        (incident_ids, Incident, "incidents", False),
    ):
        if not ids:
            continue
        q = select(model.id).where(model.id.in_(ids))
        if scoped:
            q = q.where(model.universe_id == universe_id)
        found = set((await session.execute(q)).scalars())
        if missing := [str(i) for i in dict.fromkeys(ids) if i not in found]:
            where = "in this case's universe" if scoped else ""
            raise HTTPException(422, detail=f"{label} not found {where}: {', '.join(missing)}")
    if parent_case_id is not None:
        if parent_case_id == case_id:
            raise HTTPException(422, detail="a case cannot be its own parent")
        if await session.get(CourtCase, parent_case_id) is None:
            raise HTTPException(422, detail="parent_case_id is not a court case")
        # Walk up from the proposed parent: reaching this case again means the
        # new link would close a loop.
        seen: set[uuid.UUID] = set()
        cursor: uuid.UUID | None = parent_case_id
        while cursor is not None and cursor not in seen:
            if cursor == case_id:
                raise HTTPException(422, detail="parent_case_id would make a loop of cases")
            seen.add(cursor)
            cursor = (
                await session.execute(
                    select(CourtCase.parent_case_id).where(CourtCase.id == cursor)
                )
            ).scalar_one_or_none()


async def _replace(session: AsyncSession, model, case_id: uuid.UUID, column: str, ids) -> None:
    await session.execute(model.__table__.delete().where(model.court_case_id == case_id))
    for i in dict.fromkeys(ids):
        session.add(model(court_case_id=case_id, **{column: i}))


async def _incident_ids(session: AsyncSession, case_id: uuid.UUID) -> set[uuid.UUID]:
    rows = await session.execute(
        select(CourtCaseIncident.incident_id).where(CourtCaseIncident.court_case_id == case_id)
    )
    return set(rows.scalars())


# --- the acquitted mirror -------------------------------------------------------


async def _verdicts(
    session: AsyncSession, incident_ids: set[uuid.UUID]
) -> dict[tuple[uuid.UUID, uuid.UUID], bool]:
    """(member, incident) -> cleared, for every member a case covering the
    incident has as a defendant. Cleared means acquitted in some case and
    convicted or pleaded in none."""
    if not incident_ids:
        return {}
    acquitted = func.bool_or(CourtCaseDefendant.disposition == CaseDisposition.ACQUITTED.value)
    guilty = func.bool_or(CourtCaseDefendant.disposition.in_(_GUILTY))
    rows = await session.execute(
        select(CourtCaseDefendant.member_id, CourtCaseIncident.incident_id, acquitted, guilty)
        .join(
            CourtCaseIncident,
            CourtCaseIncident.court_case_id == CourtCaseDefendant.court_case_id,
        )
        .where(
            CourtCaseIncident.incident_id.in_(incident_ids),
            CourtCaseDefendant.member_id.is_not(None),
        )
        .group_by(CourtCaseDefendant.member_id, CourtCaseIncident.incident_id)
    )
    return {(m, i): bool(a) and not bool(g) for m, i, a, g in rows.all()}


async def _governed(
    session: AsyncSession, case_id: uuid.UUID, member_id: uuid.UUID | None = None
) -> set[tuple[uuid.UUID, uuid.UUID]]:
    """(member, incident) pairs a case's verdicts speak to: each of its named
    defendants (or the one given) against each incident it covers."""
    q = (
        select(CourtCaseDefendant.member_id, CourtCaseIncident.incident_id)
        .join(
            CourtCaseIncident,
            CourtCaseIncident.court_case_id == CourtCaseDefendant.court_case_id,
        )
        .where(
            CourtCaseDefendant.court_case_id == case_id,
            CourtCaseDefendant.member_id.is_not(None),
        )
    )
    if member_id is not None:
        q = q.where(CourtCaseDefendant.member_id == member_id)
    return {(m, i) for m, i in (await session.execute(q)).all()}


async def sync_acquitted(
    session: AsyncSession,
    incident_ids: set[uuid.UUID],
    released: set[tuple[uuid.UUID, uuid.UUID]] = frozenset(),
) -> None:
    """Keep `incident_participant.acquitted` in step with the cases.

    A participant some case speaks to (defendant in a case covering the
    incident) gets the verdict: cleared only by an acquittal nothing
    contradicts. A participant no case speaks to keeps whatever flag it has,
    because 18 flags were set by hand before cases existed and most still have
    no case behind them. `released` names pairs a case stopped speaking to in
    this write (a defendant or an incident removed, a case deleted): those had
    their flag from the case, so with no verdict left they go back to False.

    The column stays the one `member_stats` reads, so the stats views are
    untouched. Like the other mirrors (`sets.gang_id`), nothing else writes it
    once a case covers the incident.
    """
    incidents = set(incident_ids) | {i for _, i in released}
    if not incidents:
        return
    verdicts = await _verdicts(session, incidents)
    rows = await session.execute(
        select(IncidentParticipant).where(IncidentParticipant.incident_id.in_(incidents))
    )
    for p in rows.scalars():
        key = (p.member_id, p.incident_id)
        if key in verdicts:
            wanted = verdicts[key]
        elif key in released:
            wanted = False
        else:
            continue
        if p.acquitted != wanted:
            p.acquitted = wanted
            session.add(p)


# --- cases ----------------------------------------------------------------------


async def get_court_case(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> CourtCase | None:
    result = await session.execute(
        select(CourtCase).where(CourtCase.id == id, CourtCase.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_court_case_by_slug(
    session: AsyncSession, slug: str, universe_id: uuid.UUID
) -> CourtCase | None:
    result = await session.execute(
        select(CourtCase).where(CourtCase.slug == slug, CourtCase.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


_CONFLICTS = {
    "uq_court_case_court_docket": "a case with this court and docket exists",
    "uq_court_case_defendant_case_member": "this member is already a defendant in the case",
}


async def _write(session: AsyncSession, *, commit: bool) -> None:
    """Flush or commit, turning the two unique indexes into a 409.

    Either can fire at the first flush, before any commit, so every flush that
    can insert a case or a defendant goes through here; the session is rolled
    back so the caller's request leaves nothing half-written.
    """
    try:
        await (session.commit() if commit else session.flush())
    except IntegrityError as e:
        await session.rollback()
        for index, message in _CONFLICTS.items():
            if index in str(e.orig):
                raise HTTPException(409, detail=message) from None
        raise


async def create_court_case(
    session: AsyncSession, data: CourtCaseCreate, actor_id: uuid.UUID
) -> CourtCase:
    await _check_links(
        session,
        data.universe_id,
        set_ids=data.set_ids,
        source_ids=data.source_ids,
        incident_ids=data.incident_ids,
        parent_case_id=data.parent_case_id,
    )
    dump = data.model_dump(
        exclude={"filed_at", "closed_at", "incident_ids", "set_ids", "source_ids"}
    )
    dump["filed_at"] = _fuzzy(data.filed_at)
    dump["closed_at"] = _fuzzy(data.closed_at)
    dump["jurisdiction"] = data.jurisdiction.value
    dump["kind"] = data.kind.value
    dump["slug"] = await _unique_slug(session, data.universe_id, slugify(data.name, "case"))
    obj = CourtCase(**dump, created_by_id=actor_id)
    session.add(obj)
    await _write(session, commit=False)
    await _replace(session, CourtCaseIncident, obj.id, "incident_id", data.incident_ids)
    await _replace(session, CourtCaseSet, obj.id, "set_id", data.set_ids)
    await _replace(session, CourtCaseSource, obj.id, "source_id", data.source_ids)
    await _write(session, commit=True)
    await session.refresh(obj)
    return obj


async def update_court_case(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: CourtCaseUpdate
) -> CourtCase | None:
    obj = await get_court_case(session, id, universe_id)
    if obj is None:
        return None
    sent = data.model_fields_set
    await _check_links(
        session,
        obj.universe_id,
        case_id=obj.id,
        set_ids=data.set_ids,
        source_ids=data.source_ids,
        incident_ids=data.incident_ids,
        parent_case_id=data.parent_case_id if "parent_case_id" in sent else None,
    )
    for field in ("name", "court", "jurisdiction", "kind"):
        if field in sent and getattr(data, field) is None:
            raise HTTPException(422, detail=f"{field} cannot be cleared")
    for field in (
        "name",
        "court",
        "docket",
        "docket_aliases",
        "parent_case_id",
        "judge",
        "summary",
        "courtlistener_ids",
    ):
        if field in sent:
            value = getattr(data, field)
            if field in ("docket_aliases", "courtlistener_ids") and value is None:
                value = []
            setattr(obj, field, value)
    for field in ("jurisdiction", "kind"):
        if field in sent:
            setattr(obj, field, getattr(data, field).value)
    for field in ("filed_at", "closed_at"):
        if field in sent:
            setattr(obj, field, _fuzzy(getattr(data, field)))
    # Only a real rename re-slugs, as for sets: an old link keeps working until
    # the name actually changes.
    if "name" in sent:
        base = slugify(obj.name, "case")
        if not (obj.slug == base or (obj.slug or "").startswith(f"{base}-")):
            obj.slug = await _unique_slug(session, obj.universe_id, base, exclude_id=obj.id)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    # Flushed here, not by the next query's autoflush, so a docket edit that
    # collides with another case is a 409 rather than a 500.
    await _write(session, commit=False)
    if data.incident_ids is not None:
        before = await _incident_ids(session, obj.id)
        governed = await _governed(session, obj.id)
        await _replace(session, CourtCaseIncident, obj.id, "incident_id", data.incident_ids)
        await session.flush()
        after = set(data.incident_ids)
        released = {(m, i) for m, i in governed if i not in after}
        await sync_acquitted(session, before | after, released)
    if data.set_ids is not None:
        await _replace(session, CourtCaseSet, obj.id, "set_id", data.set_ids)
    if data.source_ids is not None:
        await _replace(session, CourtCaseSource, obj.id, "source_id", data.source_ids)
    await _write(session, commit=True)
    await session.refresh(obj)
    return obj


async def delete_court_case(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_court_case(session, id, universe_id)
    if obj is None:
        return False
    released = await _governed(session, obj.id)
    # The links and defendants cascade, and spells and child cases are SET NULL,
    # in the schema; the defendants go through the ORM so the audit log sees them.
    for d in (
        await session.execute(
            select(CourtCaseDefendant).where(CourtCaseDefendant.court_case_id == obj.id)
        )
    ).scalars():
        await session.delete(d)
    # Flushed first, or the unit of work may delete the case before them and
    # the cascade leaves these deletes matching nothing.
    await session.flush()
    await session.delete(obj)
    await session.flush()
    await sync_acquitted(session, set(), released)
    await session.commit()
    return True


def _list_query():
    defendants = (
        select(func.count())
        .where(CourtCaseDefendant.court_case_id == CourtCase.id)
        .correlate(CourtCase)
        .scalar_subquery()
    )
    incidents = (
        select(func.count())
        .where(CourtCaseIncident.court_case_id == CourtCase.id)
        .correlate(CourtCase)
        .scalar_subquery()
    )
    return select(CourtCase, defendants, incidents)


def _order(q):
    filed = CourtCase.filed_at["year"].astext
    return q.order_by(filed.desc().nullslast(), CourtCase.name)


async def _items(
    session: AsyncSession, q, viewer_member_id: uuid.UUID | None = None
) -> list[CourtCaseListItem]:
    from app.crud.incident import universe_slugs

    rows = (await session.execute(q)).all()
    slugs = await universe_slugs(session, {c.universe_id for c, _, _ in rows})
    viewer: dict[uuid.UUID, CourtCaseDefendant] = {}
    if viewer_member_id is not None and rows:
        found = await session.execute(
            select(CourtCaseDefendant).where(
                CourtCaseDefendant.member_id == viewer_member_id,
                CourtCaseDefendant.court_case_id.in_([c.id for c, _, _ in rows]),
            )
        )
        viewer = {d.court_case_id: d for d in found.scalars()}
    out = []
    for case, n_def, n_inc in rows:
        item = CourtCaseListItem.model_validate(case)
        item.universe_slug = slugs.get(case.universe_id)
        item.defendant_count, item.incident_count = n_def, n_inc
        if d := viewer.get(case.id):
            item.viewer_disposition = CaseDisposition(d.disposition)
            item.viewer_sentence_months = d.sentence_months
            item.viewer_life_sentence = d.life_sentence
        out.append(item)
    return out


async def list_court_cases(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 100
) -> tuple[list[CourtCaseListItem], int]:
    total = (
        await session.execute(
            select(func.count()).select_from(CourtCase).where(CourtCase.universe_id == universe_id)
        )
    ).scalar_one()
    q = (
        _order(_list_query().where(CourtCase.universe_id == universe_id))
        .offset(offset)
        .limit(limit)
    )
    return await _items(session, q), total


# The three lists below are scoped by the member, set or incident alone, never by
# the case's universe: a member can be a defendant in another universe's case,
# and each row carries its own universe_slug to link it there.


async def list_court_cases_by_member(
    session: AsyncSession, member_id: uuid.UUID
) -> list[CourtCaseListItem]:
    ids = select(CourtCaseDefendant.court_case_id).where(CourtCaseDefendant.member_id == member_id)
    return await _items(
        session, _order(_list_query().where(CourtCase.id.in_(ids))), viewer_member_id=member_id
    )


async def list_court_cases_by_set(
    session: AsyncSession, set_id: uuid.UUID
) -> list[CourtCaseListItem]:
    ids = select(CourtCaseSet.court_case_id).where(CourtCaseSet.set_id == set_id)
    return await _items(session, _order(_list_query().where(CourtCase.id.in_(ids))))


async def list_court_cases_by_incident(
    session: AsyncSession, incident_id: uuid.UUID
) -> list[CourtCaseListItem]:
    ids = select(CourtCaseIncident.court_case_id).where(
        CourtCaseIncident.incident_id == incident_id
    )
    return await _items(session, _order(_list_query().where(CourtCase.id.in_(ids))))


async def search_court_cases(
    session: AsyncSession, universe_id: uuid.UUID, q: str, limit: int = 20
) -> list[CourtCaseListItem]:
    """By name, docket, or any other spelling of the docket on file."""
    like = f"%{q.strip()}%"
    query = (
        _list_query()
        .where(
            CourtCase.universe_id == universe_id,
            or_(
                CourtCase.name.ilike(like),
                CourtCase.docket.ilike(like),
                func.array_to_string(CourtCase.docket_aliases, " ").ilike(like),
            ),
        )
        .order_by(CourtCase.name)
        .limit(limit)
    )
    return await _items(session, query)


# --- detail pieces --------------------------------------------------------------


async def list_defendants(session: AsyncSession, case_id: uuid.UUID) -> list[CourtCaseDefendant]:
    rows = await session.execute(
        select(CourtCaseDefendant)
        .where(CourtCaseDefendant.court_case_id == case_id)
        .order_by(CourtCaseDefendant.defendant_number.nullslast(), CourtCaseDefendant.created_at)
    )
    return list(rows.scalars())


async def list_case_incidents(session: AsyncSession, case_id: uuid.UUID) -> list[Incident]:
    rows = await session.execute(
        select(Incident)
        .join(CourtCaseIncident, CourtCaseIncident.incident_id == Incident.id)
        .where(CourtCaseIncident.court_case_id == case_id)
        .order_by(Incident.sortable_date.asc().nullslast(), Incident.created_at)
    )
    return list(rows.scalars())


async def list_case_sets(session: AsyncSession, case_id: uuid.UUID) -> list[GangSet]:
    rows = await session.execute(
        select(GangSet)
        .join(CourtCaseSet, CourtCaseSet.set_id == GangSet.id)
        .where(CourtCaseSet.court_case_id == case_id)
        .order_by(GangSet.name)
    )
    return list(rows.scalars())


async def list_case_sources(session: AsyncSession, case_id: uuid.UUID) -> list[Source]:
    rows = await session.execute(
        select(Source)
        .join(CourtCaseSource, CourtCaseSource.source_id == Source.id)
        .where(CourtCaseSource.court_case_id == case_id)
        .order_by(Source.title)
    )
    return list(rows.scalars())


async def list_case_spells(session: AsyncSession, case_id: uuid.UUID) -> list[MemberIncarceration]:
    rows = await session.execute(
        select(MemberIncarceration)
        .where(MemberIncarceration.court_case_id == case_id)
        .order_by(MemberIncarceration.created_at)
    )
    return list(rows.scalars())


async def related_cases(
    session: AsyncSession, case: CourtCase
) -> tuple[CourtCase | None, list[CourtCase]]:
    parent = await session.get(CourtCase, case.parent_case_id) if case.parent_case_id else None
    children = await session.execute(
        select(CourtCase).where(CourtCase.parent_case_id == case.id).order_by(CourtCase.name)
    )
    return parent, list(children.scalars())


async def members_by_id(session: AsyncSession, ids: set[uuid.UUID]) -> dict[uuid.UUID, Member]:
    if not ids:
        return {}
    rows = await session.execute(select(Member).where(Member.id.in_(ids)))
    return {m.id: m for m in rows.scalars()}


# --- defendants -----------------------------------------------------------------


async def _check_member(session: AsyncSession, member_id: uuid.UUID | None) -> None:
    # Any universe: a defendant is charged where the court sits, not where he lives.
    if member_id is not None and await session.get(Member, member_id) is None:
        raise HTTPException(422, detail="member_id is not a member")


async def add_defendant(
    session: AsyncSession, case: CourtCase, data: DefendantCreate
) -> CourtCaseDefendant:
    await _check_member(session, data.member_id)
    obj = CourtCaseDefendant(
        court_case_id=case.id,
        member_id=data.member_id,
        label=data.label,
        defendant_number=data.defendant_number,
        disposition=data.disposition.value,
        charges=[c.model_dump(mode="json") for c in data.charges],
        sentence_months=data.sentence_months,
        life_sentence=data.life_sentence,
        supervised_release_months=data.supervised_release_months,
        sentenced_at=_fuzzy(data.sentenced_at),
        cooperated=data.cooperated,
        notes=data.notes,
    )
    session.add(obj)
    await _write(session, commit=False)
    await sync_acquitted(session, await _incident_ids(session, case.id))
    await _write(session, commit=True)
    await session.refresh(obj)
    return obj


async def get_defendant(
    session: AsyncSession, case_id: uuid.UUID, defendant_id: uuid.UUID
) -> CourtCaseDefendant | None:
    result = await session.execute(
        select(CourtCaseDefendant).where(
            CourtCaseDefendant.id == defendant_id, CourtCaseDefendant.court_case_id == case_id
        )
    )
    return result.scalar_one_or_none()


async def update_defendant(
    session: AsyncSession, case: CourtCase, defendant_id: uuid.UUID, data: DefendantUpdate
) -> CourtCaseDefendant | None:
    obj = await get_defendant(session, case.id, defendant_id)
    if obj is None:
        return None
    sent = data.model_fields_set
    if "member_id" in sent:
        await _check_member(session, data.member_id)
    released: set = set()
    if "member_id" in sent and data.member_id != obj.member_id and obj.member_id is not None:
        released = await _governed(session, case.id, obj.member_id)
    for field in (
        "member_id",
        "label",
        "defendant_number",
        "sentence_months",
        "supervised_release_months",
        "notes",
    ):
        if field in sent:
            setattr(obj, field, getattr(data, field))
    for field in ("life_sentence", "cooperated"):
        if field in sent and getattr(data, field) is not None:
            setattr(obj, field, getattr(data, field))
    if "disposition" in sent and data.disposition is not None:
        obj.disposition = data.disposition.value
    if "charges" in sent:
        obj.charges = [c.model_dump(mode="json") for c in data.charges or []]
    if "sentenced_at" in sent:
        obj.sentenced_at = _fuzzy(data.sentenced_at)
    if obj.member_id is None and not obj.label:
        raise HTTPException(422, detail="a defendant needs a member_id or a label")
    session.add(obj)
    await _write(session, commit=False)
    await sync_acquitted(session, await _incident_ids(session, case.id), released)
    await _write(session, commit=True)
    await session.refresh(obj)
    return obj


async def delete_defendant(session: AsyncSession, case: CourtCase, defendant_id: uuid.UUID) -> bool:
    obj = await get_defendant(session, case.id, defendant_id)
    if obj is None:
        return False
    released = await _governed(session, case.id, obj.member_id) if obj.member_id else set()
    await session.delete(obj)
    await session.flush()
    await sync_acquitted(session, set(), released)
    await session.commit()
    return True


async def keep_defendants_of_deleted_member(session: AsyncSession, member: Member) -> None:
    """Called by `delete_member`: the court record outlives the wiki row.

    The member FK is SET NULL, and a defendant row needs a member or a label,
    so the member's name goes into `label` first where there is none.
    """
    rows = await session.execute(
        select(CourtCaseDefendant).where(CourtCaseDefendant.member_id == member.id)
    )
    for d in rows.scalars():
        if not d.label:
            d.label = member.display_name
            session.add(d)
    await session.flush()
