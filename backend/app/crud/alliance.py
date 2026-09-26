import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.enums import SetRelationshipType
from app.core.slug import slugify
from app.models.alliance import Alliance, AllianceMunicipality, AllianceRelationship
from app.models.gang import Gang
from app.models.gang_set import GangSet, SetRelationship
from app.models.member import Member
from app.schemas.alliance import AllianceCreate, AllianceRelationshipCreate, AllianceUpdate


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


def _slugify(s: str) -> str:
    return slugify(s, "alliance")


async def _unique_slug(
    session: AsyncSession, universe_id: uuid.UUID, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug, n = base, 2
    while True:
        q = select(Alliance).where(Alliance.universe_id == universe_id, Alliance.slug == slug)
        if exclude_id:
            q = q.where(Alliance.id != exclude_id)
        if (await session.execute(q)).scalar_one_or_none() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def _sync_alliance_municipalities(
    session: AsyncSession, alliance_id: uuid.UUID, territory_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        AllianceMunicipality.__table__.delete().where(
            AllianceMunicipality.alliance_id == alliance_id
        )
    )
    for mid in territory_ids:
        session.add(AllianceMunicipality(alliance_id=alliance_id, municipality_id=mid))


async def _sync_alliance_sets(
    session: AsyncSession, alliance_id: uuid.UUID, set_ids: list[uuid.UUID]
) -> None:
    # Single source of truth: sets.alliance_id (direct FK on the sets table)
    # 1. Detach any sets currently linked to this alliance but not in the new list
    detach_q = (
        GangSet.__table__.update()
        .where(GangSet.alliance_id == alliance_id)
        .values(alliance_id=None)
    )
    if set_ids:
        detach_q = detach_q.where(GangSet.id.notin_(set_ids))
    await session.execute(detach_q)
    # 2. Attach all sets in the new list to this alliance
    if set_ids:
        await session.execute(
            GangSet.__table__.update()
            .where(GangSet.id.in_(set_ids))
            .values(alliance_id=alliance_id)
        )


async def _sync_alliance_friend_relationships(
    session: AsyncSession, alliance_id: uuid.UUID
) -> None:
    """Create FRIEND relationships between all sets in alliance_id (pairwise)."""
    result = await session.execute(select(GangSet.id).where(GangSet.alliance_id == alliance_id))
    set_ids = result.scalars().all()
    for i, a_id in enumerate(set_ids):
        for b_id in set_ids[i + 1 :]:
            a, b = (a_id, b_id) if a_id < b_id else (b_id, a_id)
            existing = await session.execute(
                select(SetRelationship).where(
                    SetRelationship.set_a_id == a,
                    SetRelationship.set_b_id == b,
                    # A link that was closed in the past must not block a new one.
                    SetRelationship.until_date.is_(None),
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(
                    SetRelationship(
                        set_a_id=a, set_b_id=b, relationship_type=SetRelationshipType.FRIEND
                    )
                )


async def create_alliance(
    session: AsyncSession, data: AllianceCreate, actor_id: uuid.UUID
) -> Alliance:
    dump = data.model_dump(exclude={"territory_ids", "set_ids"})
    dump["founded_at"] = _fuzzy_to_dict(data.founded_at)
    base = _slugify(data.name)
    dump["slug"] = await _unique_slug(session, data.universe_id, base)
    obj = Alliance(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_alliance_municipalities(session, obj.id, data.territory_ids)
    await _sync_alliance_sets(session, obj.id, data.set_ids)
    if data.set_ids:
        await _sync_alliance_friend_relationships(session, obj.id)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_alliance(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Alliance | None:
    result = await session.execute(
        select(Alliance).where(Alliance.id == id, Alliance.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_alliance_by_slug(
    session: AsyncSession, slug: str, universe_id: uuid.UUID
) -> Alliance | None:
    result = await session.execute(
        select(Alliance).where(Alliance.slug == slug, Alliance.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_alliances(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 50
) -> tuple[list[Alliance], int]:
    count_result = await session.execute(
        select(func.count()).select_from(Alliance).where(Alliance.universe_id == universe_id)
    )
    total = count_result.scalar_one()
    # Ordered, with a tiebreak: unordered offset pages can repeat or skip rows.
    result = await session.execute(
        select(Alliance)
        .where(Alliance.universe_id == universe_id)
        .order_by(Alliance.name, Alliance.id)
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())
    await attach_alliance_list_stats(session, universe_id, items)
    return items, total


async def attach_alliance_list_stats(
    session: AsyncSession, universe_id: uuid.UUID, items: list[Alliance]
) -> None:
    """Attach set_count, member_count, gang_name and gang_color to each alliance.

    member_count uses the same definition as the alliance's member list (see
    member CRUD's alliance filter): members tagged straight to the alliance plus
    the current members of every set in it, each person counted once.
    """
    if not items:
        return
    ids = [a.id for a in items]
    set_rows = await session.execute(
        select(GangSet.alliance_id, func.count())
        .where(GangSet.alliance_id.in_(ids))
        .group_by(GangSet.alliance_id)
    )
    set_counts = dict(set_rows.all())
    member_rows = await session.execute(
        sa.text(
            """
            SELECT alliance_id, count(DISTINCT member_id) FROM (
                SELECT m.alliance_id, m.id AS member_id
                FROM member m
                WHERE m.universe_id = :uid AND m.alliance_id IS NOT NULL
                UNION
                SELECT s.alliance_id, ms.member_id
                FROM member_set ms
                JOIN sets s ON s.id = ms.set_id
                WHERE s.universe_id = :uid AND s.alliance_id IS NOT NULL
                  AND ms.until_date IS NULL
            ) x
            GROUP BY alliance_id
            """
        ),
        {"uid": universe_id},
    )
    member_counts = dict(member_rows.all())
    gang_ids = {a.gang_id for a in items if a.gang_id}
    gangs: dict[uuid.UUID, tuple[str, str | None]] = {}
    if gang_ids:
        gang_rows = await session.execute(
            select(Gang.id, Gang.name, Gang.color).where(Gang.id.in_(gang_ids))
        )
        gangs = {gid: (name, color) for gid, name, color in gang_rows.all()}
    for a in items:
        gang = gangs.get(a.gang_id) if a.gang_id else None
        # SQLModel rejects unknown attributes through __setattr__; bypass it,
        # as attach_primary_photos does.
        object.__setattr__(a, "set_count", int(set_counts.get(a.id, 0)))
        object.__setattr__(a, "member_count", int(member_counts.get(a.id, 0)))
        object.__setattr__(a, "gang_name", gang[0] if gang else None)
        object.__setattr__(a, "gang_color", gang[1] if gang else None)


async def update_alliance(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: AllianceUpdate
) -> Alliance | None:
    obj = await get_alliance(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True, exclude={"territory_ids", "set_ids"})
    if "founded_at" in dump:
        dump["founded_at"] = _fuzzy_to_dict(data.founded_at)
    if "name" in dump:
        base = _slugify(dump["name"])
        dump["slug"] = await _unique_slug(session, universe_id, base, exclude_id=id)
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    if data.territory_ids is not None:
        await _sync_alliance_municipalities(session, obj.id, data.territory_ids)
    if data.set_ids is not None:
        await _sync_alliance_sets(session, obj.id, data.set_ids)
        if data.set_ids:
            await _sync_alliance_friend_relationships(session, obj.id)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_alliance(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_alliance(session, id, universe_id)
    if obj is None:
        return False
    # Detach what points at it first: neither FK has ON DELETE, so a set or a
    # member tagged straight to the alliance would otherwise block the delete.
    # Members were missed until 2026-09-24, and any alliance with a directly
    # tagged member could not be deleted at all.
    await session.execute(
        GangSet.__table__.update().where(GangSet.alliance_id == id).values(alliance_id=None)
    )
    await session.execute(
        Member.__table__.update().where(Member.alliance_id == id).values(alliance_id=None)
    )
    await session.delete(obj)
    await session.commit()
    return True


async def list_alliance_territory_ids(
    session: AsyncSession, alliance_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(AllianceMunicipality.municipality_id).where(
            AllianceMunicipality.alliance_id == alliance_id
        )
    )
    return result.scalars().all()


async def list_alliance_set_ids(session: AsyncSession, alliance_id: uuid.UUID) -> list[uuid.UUID]:
    result = await session.execute(select(GangSet.id).where(GangSet.alliance_id == alliance_id))
    return result.scalars().all()


async def search_alliances(session: AsyncSession, universe_id: uuid.UUID, q: str) -> list[Alliance]:
    pattern = f"%{q}%"
    result = await session.execute(
        select(Alliance).where(
            Alliance.universe_id == universe_id,
            Alliance.name.ilike(pattern) | sa.cast(Alliance.aliases, sa.Text).ilike(pattern),
        )
    )
    return result.scalars().all()


# ─── Alliance relationships ───────────────────────────────────────────────────
#
# A link held by a whole alliance, to another alliance or to one set. Read from
# either end: an alliance sees the rows it holds on either side, and a set sees
# the rows that name it plus the rows its own alliance holds (see
# list_set_alliance_relationships).


def _touches_alliance(alliance_id: uuid.UUID):
    return (AllianceRelationship.alliance_id == alliance_id) | (
        AllianceRelationship.other_alliance_id == alliance_id
    )


async def add_alliance_relationship(
    session: AsyncSession,
    alliance_id: uuid.UUID,
    universe_id: uuid.UUID,
    data: AllianceRelationshipCreate,
) -> AllianceRelationship:
    """Open a relationship spell. Idempotent when the same open link exists.

    Refuses a link to itself, to a set inside this alliance, to a reserved set,
    and anything outside the universe. An open link of the other type is a 409:
    turning allies into enemies is two facts, so the old spell is ended first.
    """
    if data.target_alliance_id is not None:
        if data.target_alliance_id == alliance_id:
            raise HTTPException(422, detail="An alliance cannot be related to itself")
        if await get_alliance(session, data.target_alliance_id, universe_id) is None:
            raise HTTPException(404, detail="Target alliance not found in this universe")
        a, b = sorted((alliance_id, data.target_alliance_id))
        match = (AllianceRelationship.alliance_id == a) & (
            AllianceRelationship.other_alliance_id == b
        )
        row = AllianceRelationship(alliance_id=a, other_alliance_id=b, relationship_type=data.type)
    else:
        target = (
            await session.execute(
                select(GangSet).where(
                    GangSet.id == data.target_set_id, GangSet.universe_id == universe_id
                )
            )
        ).scalar_one_or_none()
        if target is None:
            raise HTTPException(404, detail="Target set not found in this universe")
        if target.is_reserved:
            raise HTTPException(422, detail="Reserved sets cannot hold relationships")
        if target.alliance_id == alliance_id:
            raise HTTPException(
                422, detail=f"{target.name} is in this alliance; membership already says so"
            )
        match = (AllianceRelationship.alliance_id == alliance_id) & (
            AllianceRelationship.other_set_id == target.id
        )
        row = AllianceRelationship(
            alliance_id=alliance_id, other_set_id=target.id, relationship_type=data.type
        )

    existing = (
        await session.execute(
            select(AllianceRelationship).where(match, AllianceRelationship.until_date.is_(None))
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.relationship_type != data.type:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Relationship already exists with a different type",
            )
        return existing
    # The column is plain JSONB, not the FuzzyDate TypeDecorator.
    row.from_date = data.from_date.model_dump() if data.from_date is not None else None
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def _names(
    session: AsyncSession, alliance_ids: set[uuid.UUID], set_ids: set[uuid.UUID]
) -> tuple[dict[uuid.UUID, tuple[str, str | None]], dict[uuid.UUID, tuple[str, str | None]]]:
    alliances: dict[uuid.UUID, tuple[str, str | None]] = {}
    sets: dict[uuid.UUID, tuple[str, str | None]] = {}
    if alliance_ids:
        rows = await session.execute(
            select(Alliance.id, Alliance.name, Alliance.slug).where(Alliance.id.in_(alliance_ids))
        )
        alliances = {i: (n, s) for i, n, s in rows.all()}
    if set_ids:
        rows = await session.execute(
            select(GangSet.id, GangSet.name, GangSet.slug).where(GangSet.id.in_(set_ids))
        )
        sets = {i: (n, s) for i, n, s in rows.all()}
    return alliances, sets


def _sort_key(item: dict):
    # Current first, then ended; by name within each.
    return (not item["is_current"], item["other_name"].lower())


async def list_alliance_relationships(
    session: AsyncSession, alliance_id: uuid.UUID, include_ended: bool = True
) -> list[dict]:
    """Every link this alliance holds, read from its side."""
    q = select(AllianceRelationship).where(_touches_alliance(alliance_id))
    if not include_ended:
        q = q.where(AllianceRelationship.until_date.is_(None))
    rows = (await session.execute(q)).scalars().all()

    def far(r: AllianceRelationship) -> tuple[str, uuid.UUID]:
        if r.other_set_id is not None:
            return "set", r.other_set_id
        return "alliance", (r.other_alliance_id if r.alliance_id == alliance_id else r.alliance_id)

    fars = [far(r) for r in rows]
    alliances, sets = await _names(
        session,
        {i for k, i in fars if k == "alliance"},
        {i for k, i in fars if k == "set"},
    )
    out = []
    for r, (kind, oid) in zip(rows, fars, strict=True):
        name, slug = (alliances if kind == "alliance" else sets).get(oid, ("?", None))
        out.append(
            {
                "id": r.id,
                "type": r.relationship_type,
                "other_kind": kind,
                "other_id": oid,
                "other_name": name,
                "other_slug": slug,
                "from_date": r.from_date,
                "until_date": r.until_date,
                "is_current": r.until_date is None,
            }
        )
    return sorted(out, key=_sort_key)


async def list_set_alliance_relationships(
    session: AsyncSession,
    set_id: uuid.UUID,
    set_alliance_id: uuid.UUID | None,
    include_ended: bool = False,
) -> list[dict]:
    """Alliance-level links that bear on one set, read from the set's side.

    Two sources: rows naming the set itself as the far side (an alliance at war
    with this set), and rows held by the set's own alliance, which the set
    inherits and which carry `via_alliance_*` so the page can say why.
    """
    cond = AllianceRelationship.other_set_id == set_id
    if set_alliance_id is not None:
        cond = cond | _touches_alliance(set_alliance_id)
    q = select(AllianceRelationship).where(cond)
    if not include_ended:
        q = q.where(AllianceRelationship.until_date.is_(None))
    rows = (await session.execute(q)).scalars().all()

    def far(r: AllianceRelationship) -> tuple[str, uuid.UUID, uuid.UUID | None]:
        if r.other_set_id == set_id:
            return "alliance", r.alliance_id, None
        if r.other_set_id is not None:
            return "set", r.other_set_id, set_alliance_id
        other = r.other_alliance_id if r.alliance_id == set_alliance_id else r.alliance_id
        return "alliance", other, set_alliance_id

    fars = [far(r) for r in rows]
    alliance_ids = {i for k, i, _ in fars if k == "alliance"}
    if set_alliance_id is not None:
        alliance_ids.add(set_alliance_id)
    alliances, sets = await _names(session, alliance_ids, {i for k, i, _ in fars if k == "set"})
    out = []
    for r, (kind, oid, via) in zip(rows, fars, strict=True):
        name, slug = (alliances if kind == "alliance" else sets).get(oid, ("?", None))
        via_name, via_slug = alliances.get(via, (None, None)) if via else (None, None)
        out.append(
            {
                "id": r.id,
                "type": r.relationship_type,
                "other_kind": kind,
                "other_id": oid,
                "other_name": name,
                "other_slug": slug,
                "via_alliance_id": via,
                "via_alliance_name": via_name,
                "via_alliance_slug": via_slug,
                "from_date": r.from_date,
                "until_date": r.until_date,
                "is_current": r.until_date is None,
            }
        )
    return sorted(out, key=_sort_key)


async def _get_alliance_relationship(
    session: AsyncSession, alliance_id: uuid.UUID, relationship_id: uuid.UUID
) -> AllianceRelationship | None:
    return (
        await session.execute(
            select(AllianceRelationship).where(
                AllianceRelationship.id == relationship_id, _touches_alliance(alliance_id)
            )
        )
    ).scalar_one_or_none()


async def end_alliance_relationship(
    session: AsyncSession,
    alliance_id: uuid.UUID,
    relationship_id: uuid.UUID,
    until_date: dict | None,
) -> bool:
    """Close an open link as of a date, keeping it as history."""
    row = await _get_alliance_relationship(session, alliance_id, relationship_id)
    if row is None or row.until_date is not None:
        return False
    row.until_date = until_date
    await session.commit()
    return True


async def delete_alliance_relationship(
    session: AsyncSession, alliance_id: uuid.UUID, relationship_id: uuid.UUID
) -> bool:
    """Delete a link outright, for a mistaken entry. Use end for a real ending."""
    row = await _get_alliance_relationship(session, alliance_id, relationship_id)
    if row is None:
        return False
    await session.delete(row)
    await session.commit()
    return True
