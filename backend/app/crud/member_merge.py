"""Merge one member record into another: the cure for a duplicate.

``merge_members(keep, drop)`` moves everything that points at ``drop`` onto
``keep`` and deletes ``drop``, in one transaction. ``dry_run`` does all of it
and rolls back, so the preview the UI shows is the real merge, not a guess.

What moves, and how a clash is settled (``keep`` always wins a clash, so the
record a researcher chose as canonical is never silently rewritten):

- incident participations: moved; if both were in the same incident, ``keep``'s
  row stays and ``drop``'s is dropped (reported as a conflict). Each incident
  gets a ``participants`` link-change audit row, so its History shows the swap.
- set spells: moved; an open spell in a set ``keep`` already has an open spell
  in is dropped (one open spell per member and set is a unique index), and a
  moved spell loses ``is_primary`` when ``keep`` already has an open primary.
- source citations, business links: unioned.
- aliases (``member_alias`` rows), incarcerations, custody ids, photos: moved;
  a custody id ``keep`` already holds (same system and number) is dropped, and
  moved photos lose ``is_primary`` when ``keep`` has a primary photo.
- sets founded by ``drop``: re-pointed at ``keep``.
- family: ``drop``'s relatives are added to ``keep``'s, every other member's
  family JSON that names ``drop`` is rewritten to name ``keep``, and a link
  between the two of them disappears (nobody is their own sibling).
- columns: ``keep``'s value stands unless it is empty, then ``drop``'s fills
  it; ``prefer`` names columns where ``drop``'s value should win instead.
  ``drop``'s nickname and legal name, when they differ from ``keep``'s, are
  added to ``keep.aliases``, so the old spelling still finds the record.
  ``is_rapper`` / ``is_snitch`` are OR-ed. Status UNKNOWN counts as empty.

``drop``'s own audit history stays under its id (the DELETE snapshot at the end
holds its last state); ``keep``'s History gets a ``merged`` entry naming it.
"""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import load_link_rows, record_link_change
from app.core.enums import MemberStatus
from app.crud.member import INVERSE_REL, _family_ids, _set_family_ids
from app.models.business import BusinessMember
from app.models.gang_set import GangSet
from app.models.incident import IncidentParticipant
from app.models.media import Media
from app.models.member import (
    Member,
    MemberAlias,
    MemberCustodyId,
    MemberIncarceration,
    MemberSet,
    MemberSource,
)

# Columns a caller may ask to take from the dropped record instead of the kept one.
PREFERABLE_FIELDS = (
    "nickname",
    "legal_name",
    "nickname_unknown",
    "biography",
    "status",
    "dob",
    "date_of_death",
    "death_incident_id",
    "mdoc_number",
    "bop_register_number",
    "alliance_id",
    "gang_id",
)

_SPELL_FIELDS = ["set_id", "rank", "is_primary", "from_date", "until_date"]
_PARTICIPANT_FIELDS = ["member_id", "role", "outcome", "acquitted", "notes"]


def _empty(field: str, value) -> bool:
    if field == "status":
        return value in (None, MemberStatus.UNKNOWN, "UNKNOWN")
    if field == "nickname_unknown":
        return value is False  # never "empty": only a prefer moves it
    return value is None or value == "" or value == {} or value == []


def _merge_names(keep: Member, drop: Member) -> list[str]:
    """keep.aliases plus drop's names and aliases, case-insensitively unique."""
    seen = {(n or "").strip().lower() for n in (keep.nickname, keep.legal_name)}
    out: list[str] = []
    for name in [*(keep.aliases or []), drop.nickname, drop.legal_name, *(drop.aliases or [])]:
        if not isinstance(name, str) or not name.strip():
            continue
        k = name.strip().lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(name.strip())
    return out


async def _load(session: AsyncSession, member_id: uuid.UUID, universe_id: uuid.UUID) -> Member:
    m = (
        await session.execute(select(Member).where(Member.id == member_id, Member.universe_id == universe_id))
    ).scalar_one_or_none()
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Member {member_id} not found in this universe")
    return m


async def merge_members(
    session: AsyncSession,
    universe_id: uuid.UUID,
    keep_id: uuid.UUID,
    drop_id: uuid.UUID,
    prefer: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    if keep_id == drop_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Cannot merge a member into itself")
    bad = [f for f in (prefer or []) if f not in PREFERABLE_FIELDS]
    if bad:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"Cannot prefer {', '.join(bad)}: not a mergeable column"
        )
    keep = await _load(session, keep_id, universe_id)
    drop = await _load(session, drop_id, universe_id)
    report: dict = {
        "keep": {"id": keep.id, "display_name": keep.display_name, "slug": keep.slug},
        "drop": {"id": drop.id, "display_name": drop.display_name, "slug": drop.slug},
        "fields": [],
        "moved": {},
        "conflicts": [],
        "dry_run": dry_run,
    }
    prefer_set = set(prefer or [])

    # ── Columns ──────────────────────────────────────────────────────────────
    # Unique columns must be cleared on drop before keep can take them.
    unique_takeovers: dict[str, object] = {}
    for field in PREFERABLE_FIELDS:
        kv, dv = getattr(keep, field), getattr(drop, field)
        if dv == kv or _empty(field, dv):
            continue
        take = field in prefer_set or _empty(field, kv)
        if take:
            if field == "bop_register_number":
                unique_takeovers[field] = dv
            else:
                setattr(keep, field, dv)
        report["fields"].append({"field": field, "kept": dv if take else kv, "discarded": kv if take else dv})
    if unique_takeovers:
        drop.bop_register_number = None
        session.add(drop)
        await session.flush()
        keep.bop_register_number = unique_takeovers["bop_register_number"]

    names = _merge_names(keep, drop)
    if names != (keep.aliases or []):
        keep.aliases = names or None
    keep.is_rapper = keep.is_rapper or drop.is_rapper
    keep.is_snitch = keep.is_snitch or drop.is_snitch
    social = {**(drop.social_media or {}), **(keep.social_media or {})}
    keep.social_media = social or None

    # ── Incident participations ──────────────────────────────────────────────
    drop_parts = (
        (await session.execute(select(IncidentParticipant).where(IncidentParticipant.member_id == drop.id)))
        .scalars()
        .all()
    )
    keep_incidents = set(
        (
            await session.execute(
                select(IncidentParticipant.incident_id).where(IncidentParticipant.member_id == keep.id)
            )
        )
        .scalars()
        .all()
    )
    moved_parts = 0
    for p in drop_parts:
        cond = IncidentParticipant.incident_id == p.incident_id
        before = await load_link_rows(session, IncidentParticipant, cond, _PARTICIPANT_FIELDS)
        if p.incident_id in keep_incidents:
            report["conflicts"].append(
                {
                    "kind": "incident_participant",
                    "id": p.incident_id,
                    "message": "Both were participants in this incident; the kept member's role stays.",
                    "discarded": {"role": p.role, "outcome": p.outcome, "notes": p.notes},
                }
            )
            await session.execute(
                delete(IncidentParticipant).where(cond, IncidentParticipant.member_id == drop.id)
            )
        else:
            await session.execute(
                update(IncidentParticipant)
                .where(cond, IncidentParticipant.member_id == drop.id)
                .values(member_id=keep.id)
            )
            moved_parts += 1
        after = await load_link_rows(session, IncidentParticipant, cond, _PARTICIPANT_FIELDS)
        record_link_change(
            session,
            entity_type="incident",
            entity_id=p.incident_id,
            link="participants",
            key="member_id",
            before=before,
            after=after,
        )
    report["moved"]["incident_participations"] = moved_parts
    killed = [p for p in drop_parts if p.outcome == "KILLED" and p.incident_id not in keep_incidents]
    if killed and keep.status != MemberStatus.DEAD:
        report["conflicts"].append(
            {
                "kind": "status",
                "id": killed[0].incident_id,
                "message": "The dropped record was killed in an incident that moves over, "
                "but the kept record's status is not DEAD. Prefer the dropped status, or fix it after.",
                "discarded": None,
            }
        )

    # ── Set spells ───────────────────────────────────────────────────────────
    open_keep = MemberSet.member_id == keep.id
    sets_before = await load_link_rows(
        session, MemberSet, open_keep & MemberSet.until_date.is_(None), _SPELL_FIELDS
    )
    keep_open_sets = {r["set_id"] for r in sets_before}
    keep_has_primary = any(r["is_primary"] for r in sets_before)
    moved_spells = 0
    for spell in (
        (await session.execute(select(MemberSet).where(MemberSet.member_id == drop.id))).scalars().all()
    ):
        if spell.until_date is None and spell.set_id in keep_open_sets:
            report["conflicts"].append(
                {
                    "kind": "set_spell",
                    "id": spell.set_id,
                    "message": "Both had an open spell in this set; the kept member's spell stays.",
                    "discarded": {"rank": spell.rank, "from_date": spell.from_date},
                }
            )
            await session.execute(delete(MemberSet).where(MemberSet.id == spell.id))
            continue
        values: dict = {"member_id": keep.id}
        if spell.is_primary and spell.until_date is None and keep_has_primary:
            values["is_primary"] = False
        await session.execute(update(MemberSet).where(MemberSet.id == spell.id).values(**values))
        moved_spells += 1
    sets_after = await load_link_rows(
        session, MemberSet, open_keep & MemberSet.until_date.is_(None), _SPELL_FIELDS
    )
    record_link_change(
        session,
        entity_type="member",
        entity_id=keep.id,
        link="sets",
        key="set_id",
        before=sets_before,
        after=sets_after,
    )
    report["moved"]["set_spells"] = moved_spells

    # ── Sources (union) ──────────────────────────────────────────────────────
    src_before = await load_link_rows(session, MemberSource, MemberSource.member_id == keep.id, ["source_id"])
    have = {r["source_id"] for r in src_before}
    drop_sources = (
        (await session.execute(select(MemberSource.source_id).where(MemberSource.member_id == drop.id)))
        .scalars()
        .all()
    )
    new_sources = [s for s in drop_sources if s not in have]
    await session.execute(delete(MemberSource).where(MemberSource.member_id == drop.id))
    for sid in new_sources:
        session.add(MemberSource(member_id=keep.id, source_id=sid))
    await session.flush()
    record_link_change(
        session,
        entity_type="member",
        entity_id=keep.id,
        link="sources",
        key="source_id",
        before=src_before,
        after=src_before + [{"source_id": s} for s in new_sources],
    )
    report["moved"]["sources"] = len(new_sources)

    # ── Businesses (union) ───────────────────────────────────────────────────
    keep_biz = set(
        (await session.execute(select(BusinessMember.business_id).where(BusinessMember.member_id == keep.id)))
        .scalars()
        .all()
    )
    biz_moved = 0
    for bm in (
        (await session.execute(select(BusinessMember).where(BusinessMember.member_id == drop.id)))
        .scalars()
        .all()
    ):
        cond = (BusinessMember.business_id == bm.business_id) & (BusinessMember.member_id == drop.id)
        if bm.business_id in keep_biz:
            await session.execute(delete(BusinessMember).where(cond))
        else:
            await session.execute(update(BusinessMember).where(cond).values(member_id=keep.id))
            biz_moved += 1
    report["moved"]["businesses"] = biz_moved

    # ── Straight moves ───────────────────────────────────────────────────────
    for label, model in (("aliases", MemberAlias), ("incarcerations", MemberIncarceration)):
        res = await session.execute(update(model).where(model.member_id == drop.id).values(member_id=keep.id))
        report["moved"][label] = res.rowcount

    keep_custody = {
        (s, n)
        for s, n in (
            await session.execute(
                select(MemberCustodyId.system, MemberCustodyId.number).where(
                    MemberCustodyId.member_id == keep.id
                )
            )
        ).all()
    }
    custody_moved = 0
    for c in (
        (await session.execute(select(MemberCustodyId).where(MemberCustodyId.member_id == drop.id)))
        .scalars()
        .all()
    ):
        if (c.system, c.number) in keep_custody:
            await session.execute(delete(MemberCustodyId).where(MemberCustodyId.id == c.id))
        else:
            await session.execute(
                update(MemberCustodyId).where(MemberCustodyId.id == c.id).values(member_id=keep.id)
            )
            custody_moved += 1
    report["moved"]["custody_ids"] = custody_moved

    keep_has_photo = (
        await session.execute(
            select(Media.id).where(Media.member_id == keep.id, Media.is_primary.is_(True)).limit(1)
        )
    ).first() is not None
    photo_values: dict = {"member_id": keep.id}
    if keep_has_photo:
        photo_values["is_primary"] = False
    res = await session.execute(update(Media).where(Media.member_id == drop.id).values(**photo_values))
    report["moved"]["photos"] = res.rowcount

    res = await session.execute(
        update(GangSet).where(GangSet.founder_id == drop.id).values(founder_id=keep.id)
    )
    report["moved"]["sets_founded"] = res.rowcount

    # ── Family ───────────────────────────────────────────────────────────────
    drop_s, keep_s = str(drop.id), str(keep.id)
    family = dict(keep.family or {})
    for rel in INVERSE_REL:
        ids = (_family_ids(family, rel) | _family_ids(drop.family, rel)) - {drop_s, keep_s}
        _set_family_ids(family, rel, ids)
    keep.family = family or None
    relatives = (
        (
            await session.execute(
                select(Member).where(Member.universe_id == universe_id, Member.id.notin_([keep.id, drop.id]))
            )
        )
        .scalars()
        .all()
    )
    family_rewritten = 0
    for rel_member in relatives:
        fam = rel_member.family
        if not fam or drop_s not in str(fam):
            continue
        fam = dict(fam)
        for rel in INVERSE_REL:
            ids = _family_ids(fam, rel)
            if drop_s in ids:
                _set_family_ids(fam, rel, (ids - {drop_s}) | {keep_s})
        rel_member.family = fam or None
        rel_member.updated_at = datetime.now(UTC)
        session.add(rel_member)
        family_rewritten += 1
    report["moved"]["family_links_repointed"] = family_rewritten

    # ── Finish ───────────────────────────────────────────────────────────────
    keep.updated_at = datetime.now(UTC)
    session.add(keep)
    record_link_change(
        session,
        entity_type="member",
        entity_id=keep.id,
        link="merged",
        key="member_id",
        before=[],
        after=[{"member_id": drop.id, "display_name": drop.display_name, "slug": drop.slug}],
    )
    await session.flush()
    await session.delete(drop)
    await session.flush()

    if dry_run:
        await session.rollback()
    else:
        await session.commit()
    return report
