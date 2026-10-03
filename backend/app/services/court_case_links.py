"""Tie a prison spell to the court case it was served for.

A spell carries its case as text (`member_incarceration.case_id`) and, since
2026-10-02, as a link (`court_case_id`). `link_spell` reads the text with
`app.core.dockets`, finds the case by court and docket or any other spelling of
the docket on file, creates it when the rule below allows, links the spell, and
makes sure the member is on the case as a defendant with the count the spell
records.

What gets a case of its own:

- a federal docket, always: a federal case is the research's unit, and its
  co-defendants are what make it worth a page;
- a state court file only when it is notable (decided 2026-10-03): a homicide
  or assault count, or a second defendant already holding the same file. A
  single felony-firearm count stays a spell with its court file number, so the
  case list does not fill with them.

It runs when a spell is created or its case text changes (from the member page,
the OTIS import, or the `wiki` CLI), and once over every existing spell from
`app.scripts.link_spells_to_cases`.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.dockets import (
    CaseRef,
    disposition_from_notes,
    is_notable_state_offense,
    otis_charge,
    parse_case_ref,
)
from app.core.enums import CourtJurisdiction
from app.core.slug import slugify
from app.crud.court_case import _unique_slug, sync_acquitted
from app.models.court_case import CourtCase, CourtCaseDefendant, CourtCaseIncident
from app.models.member import Member, MemberIncarceration

# How far a disposition has got, so a second spell from the same case can move
# a defendant forward (pending to convicted) and never back.
_RANK = {"PENDING": 0, "DISMISSED": 1, "ACQUITTED": 1, "DIED": 1, "PLEADED": 2, "CONVICTED": 2}


@dataclass
class LinkResult:
    """What `link_spell` did, for the backfill's report."""

    outcome: str  # linked, created, skipped
    reason: str = ""
    case: CourtCase | None = None


async def find_case(session: AsyncSession, ref: CaseRef) -> CourtCase | None:
    """The case a reference names: same court and docket, or the docket among
    the case's other spellings (in either direction)."""
    spellings = {ref.docket, *ref.aliases}
    result = await session.execute(
        select(CourtCase).where(
            CourtCase.court == ref.court,
            or_(
                CourtCase.docket.in_(spellings),
                CourtCase.docket_aliases.overlap(list(spellings)),
            ),
        )
    )
    return result.scalars().first()


_SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}


def _surname(member: Member) -> str:
    """The family name of the legal name, past any generational suffix
    ("Jr.", "III"), or the display name when no legal name is on file."""
    words = [w.rstrip(",") for w in (member.legal_name or "").split()]
    while len(words) > 1 and words[-1].lower() in _SUFFIXES:
        words.pop()
    return words[-1] if words else member.display_name


def _caption(ref: CaseRef, member: Member) -> str:
    """A working name from the defendant on hand. The research corrects it to
    the caption the court used, which may name a co-defendant."""
    if ref.jurisdiction == CourtJurisdiction.US_FEDERAL:
        return f"United States v. {_surname(member)}"
    return f"People v. {_surname(member)}"


async def _shared_with_another(
    session: AsyncSession, ref: CaseRef, spell: MemberIncarceration
) -> bool:
    """Another member's spell carries the same court file."""
    spellings = [ref.docket, *ref.aliases]
    rows = await session.execute(
        select(func.count())
        .select_from(MemberIncarceration)
        .where(
            func.upper(MemberIncarceration.case_id).in_([s.upper() for s in spellings]),
            MemberIncarceration.member_id != spell.member_id,
        )
    )
    return rows.scalar_one() > 0


def merge_charge(charges: list[dict], charge: dict) -> list[dict]:
    """`charges` with `charge` folded in: a count already listed under the same
    offense and statute gains the offence date it lacked; any other is added."""
    out = [dict(c) for c in charges]
    for c in out:
        same = (c.get("offense"), c.get("statute")) == (
            charge.get("offense"),
            charge.get("statute"),
        )
        if same and c.get("offense_date") in (None, charge.get("offense_date")):
            c["offense_date"] = charge.get("offense_date")
            return out
    return [*out, charge]


async def _ensure_defendant(
    session: AsyncSession, case: CourtCase, member: Member, spell: MemberIncarceration
) -> None:
    """Put the member on the case, or fold this spell's count into his row."""
    charge = otis_charge(spell.notes)
    disposition = charge["disposition"] if charge else disposition_from_notes(spell.notes)
    row = (
        await session.execute(
            select(CourtCaseDefendant).where(
                CourtCaseDefendant.court_case_id == case.id,
                CourtCaseDefendant.member_id == member.id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        session.add(
            CourtCaseDefendant(
                court_case_id=case.id,
                member_id=member.id,
                disposition=disposition,
                charges=[charge] if charge else [],
                life_sentence=bool(spell.life_sentence),
            )
        )
    else:
        if charge:
            row.charges = merge_charge(list(row.charges or []), charge)
        if _RANK.get(disposition, 0) > _RANK.get(row.disposition, 0):
            row.disposition = disposition
        if spell.life_sentence:
            row.life_sentence = True
        session.add(row)
    await session.flush()
    incidents = (
        await session.execute(
            select(CourtCaseIncident.incident_id).where(CourtCaseIncident.court_case_id == case.id)
        )
    ).scalars()
    await sync_acquitted(session, set(incidents))


async def link_spell(
    session: AsyncSession, spell: MemberIncarceration, *, create: bool = True
) -> LinkResult:
    """Link `spell` to its case, creating the case when the rule allows.

    Leaves a spell that already names a case alone: a link made by hand wins.
    Flushes but never commits; the caller owns the transaction.
    """
    if spell.court_case_id is not None:
        return LinkResult("skipped", "already linked")
    ref = parse_case_ref(spell.case_id, spell.notes)
    if ref is None:
        return LinkResult("skipped", "no court and docket in the case text")
    member = await session.get(Member, spell.member_id)
    if member is None:
        return LinkResult("skipped", "member missing")

    case = await find_case(session, ref)
    outcome = "linked"
    if case is None:
        if ref.jurisdiction == CourtJurisdiction.US_STATE and not (
            is_notable_state_offense(spell.notes) or await _shared_with_another(session, ref, spell)
        ):
            return LinkResult("skipped", "state court file, not notable")
        if not create:
            return LinkResult("skipped", "no case on file")
        name = _caption(ref, member)
        case = CourtCase(
            id=uuid.uuid4(),
            universe_id=member.universe_id,
            name=name,
            slug=await _unique_slug(session, member.universe_id, slugify(name, "case")),
            jurisdiction=ref.jurisdiction.value,
            kind=ref.kind.value,
            court=ref.court,
            docket=ref.docket,
            docket_aliases=list(ref.aliases),
        )
        session.add(case)
        await session.flush()
        outcome = "created"
    else:
        new = [
            a
            for a in [ref.docket, *ref.aliases]
            if a != case.docket and a not in case.docket_aliases
        ]
        if new:
            case.docket_aliases = [*case.docket_aliases, *new]
            session.add(case)

    spell.court_case_id = case.id
    session.add(spell)
    await _ensure_defendant(session, case, member, spell)
    return LinkResult(outcome, case=case)
