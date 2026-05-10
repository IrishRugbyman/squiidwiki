import re
import uuid
from datetime import datetime
from typing import Literal, Optional

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.enums import SetRelationshipType, SetStatus
from app.models.alliance import Alliance
from app.models.gang import Gang
from app.models.gang_set import GangSet, SetMunicipality, SetRelationship
from app.models.member import Member
from app.models.municipality import Municipality
from app.schemas.gang_set import SetCreate, SetUpdate

SortKey = Literal["name", "status", "member_count", "updated_at", "created_at"]
SortOrder = Literal["asc", "desc"]
NoneSentinel = Literal["none"]
# A filter value can be a UUID, the literal "none" (match NULL), or None (no filter).
FilterId = Optional[uuid.UUID | NoneSentinel]


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "set"


async def _unique_slug(
    session: AsyncSession,
    universe_id: uuid.UUID,
    name: str,
    exclude_id: uuid.UUID | None = None,
) -> str:
    base = _slugify(name)
    slug, n = base, 2
    while True:
        q = select(GangSet).where(GangSet.universe_id == universe_id, GangSet.slug == slug)
        if exclude_id is not None:
            q = q.where(GangSet.id != exclude_id)
        if (await session.execute(q)).scalar_one_or_none() is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


async def _sync_set_municipalities(
    session: AsyncSession, set_id: uuid.UUID, territory_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        SetMunicipality.__table__.delete().where(SetMunicipality.set_id == set_id)
    )
    for mid in territory_ids:
        session.add(SetMunicipality(set_id=set_id, municipality_id=mid))


async def _validate_territory_ids(
    session: AsyncSession,
    municipality_id: uuid.UUID | None,
    territory_ids: list[uuid.UUID],
) -> None:
    """Each territory must be a child of the set's primary municipality."""
    if not territory_ids:
        return
    if municipality_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="territory_ids requires a municipality_id (the parent)",
        )
    from app.models.municipality import Municipality
    rows = await session.execute(
        select(Municipality.id, Municipality.parent_id).where(
            Municipality.id.in_(territory_ids)
        )
    )
    by_id = {r[0]: r[1] for r in rows}
    bad = [str(tid) for tid in territory_ids if by_id.get(tid) != municipality_id]
    if bad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"territory_ids must be children of municipality_id; offending: {bad}",
        )


async def _sync_set_relationships(
    session: AsyncSession,
    set_id: uuid.UUID,
    friend_ids: list[uuid.UUID],
    enemy_ids: list[uuid.UUID],
) -> None:
    existing = await session.execute(
        select(SetRelationship).where(
            (SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id)
        )
    )
    for rel in existing.scalars().all():
        await session.delete(rel)

    for fid in friend_ids:
        a, b = (set_id, fid) if set_id < fid else (fid, set_id)
        session.add(SetRelationship(set_a_id=a, set_b_id=b, relationship_type=SetRelationshipType.FRIEND))

    for eid in enemy_ids:
        a, b = (set_id, eid) if set_id < eid else (eid, set_id)
        session.add(SetRelationship(set_a_id=a, set_b_id=b, relationship_type=SetRelationshipType.ENEMY))


async def _sync_alliance_auto_allies(
    session: AsyncSession, set_id: uuid.UUID, alliance_id: uuid.UUID
) -> None:
    """Create FRIEND relationships between set_id and all other sets in alliance_id."""
    result = await session.execute(
        select(GangSet.id).where(GangSet.alliance_id == alliance_id, GangSet.id != set_id)
    )
    sibling_ids = result.scalars().all()
    for sibling_id in sibling_ids:
        a, b = (set_id, sibling_id) if set_id < sibling_id else (sibling_id, set_id)
        existing = await session.execute(
            select(SetRelationship).where(
                SetRelationship.set_a_id == a, SetRelationship.set_b_id == b
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(SetRelationship(
                set_a_id=a, set_b_id=b, relationship_type=SetRelationshipType.FRIEND
            ))


_RESERVED_NAMES = {"civilian", "police"}


async def create_gang_set(
    session: AsyncSession, data: SetCreate, actor_id: uuid.UUID
) -> GangSet:
    if data.name.strip().lower() in _RESERVED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{data.name}' is a reserved system set name and cannot be used.",
        )
    await _validate_territory_ids(session, data.municipality_id, data.territory_ids)
    dump = data.model_dump(exclude={"territory_ids", "friend_ids", "enemy_ids"})
    slug = await _unique_slug(session, data.universe_id, data.name)
    obj = GangSet(**dump, slug=slug, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_set_municipalities(session, obj.id, data.territory_ids)
    await _sync_set_relationships(session, obj.id, data.friend_ids, data.enemy_ids)
    if obj.alliance_id:
        await _sync_alliance_auto_allies(session, obj.id, obj.alliance_id)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_gang_set(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> GangSet | None:
    result = await session.execute(
        select(GangSet).where(GangSet.id == id, GangSet.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def get_gang_set_by_slug(
    session: AsyncSession, slug: str, universe_id: uuid.UUID
) -> GangSet | None:
    result = await session.execute(
        select(GangSet).where(GangSet.slug == slug, GangSet.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


def _apply_set_filters(
    stmt,
    universe_id: uuid.UUID,
    *,
    q: str | None = None,
    status_filter: SetStatus | None = None,
    alliance_id: FilterId = None,
    gang_id: FilterId = None,
    municipality_id: FilterId = None,
):
    stmt = stmt.where(GangSet.universe_id == universe_id)
    if q and len(q.strip()) >= 2:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            GangSet.name.ilike(pattern)
            | sa.cast(GangSet.name_variants, sa.Text).ilike(pattern)
        )
    if status_filter is not None:
        stmt = stmt.where(GangSet.status == status_filter)
    if alliance_id == "none":
        stmt = stmt.where(GangSet.alliance_id.is_(None))
    elif alliance_id is not None:
        stmt = stmt.where(GangSet.alliance_id == alliance_id)
    if gang_id == "none":
        stmt = stmt.where(GangSet.gang_id.is_(None))
    elif gang_id is not None:
        stmt = stmt.where(GangSet.gang_id == gang_id)
    if municipality_id == "none":
        stmt = stmt.where(GangSet.municipality_id.is_(None))
    elif municipality_id is not None:
        stmt = stmt.where(GangSet.municipality_id == municipality_id)
    return stmt


async def list_gang_sets(
    session: AsyncSession,
    universe_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 50,
    q: str | None = None,
    status_filter: SetStatus | None = None,
    alliance_id: FilterId = None,
    gang_id: FilterId = None,
    municipality_id: FilterId = None,
    sort: SortKey = "name",
    order: SortOrder = "asc",
) -> tuple[list[GangSet], int]:
    """List sets with optional filters, joined denorm labels, and member_count.

    Returns ORM objects with three transient attrs attached: `_member_count`,
    `_alliance_name`, `_gang_name`, `_municipality_name`. The router pulls
    these onto the Pydantic ListItem.
    """
    count_stmt = _apply_set_filters(
        select(func.count()).select_from(GangSet),
        universe_id,
        q=q,
        status_filter=status_filter,
        alliance_id=alliance_id,
        gang_id=gang_id,
        municipality_id=municipality_id,
    )
    total = (await session.execute(count_stmt)).scalar_one()

    member_count_sq = (
        select(Member.set_id, func.count(Member.id).label("member_count"))
        .group_by(Member.set_id)
        .subquery()
    )

    stmt = (
        select(
            GangSet,
            func.coalesce(member_count_sq.c.member_count, 0).label("member_count"),
            Alliance.name.label("alliance_name"),
            Gang.name.label("gang_name"),
            Municipality.name.label("municipality_name"),
        )
        .select_from(GangSet)
        .join(member_count_sq, member_count_sq.c.set_id == GangSet.id, isouter=True)
        .join(Alliance, Alliance.id == GangSet.alliance_id, isouter=True)
        .join(Gang, Gang.id == GangSet.gang_id, isouter=True)
        .join(Municipality, Municipality.id == GangSet.municipality_id, isouter=True)
    )
    stmt = _apply_set_filters(
        stmt,
        universe_id,
        q=q,
        status_filter=status_filter,
        alliance_id=alliance_id,
        gang_id=gang_id,
        municipality_id=municipality_id,
    )

    sort_cols: dict[str, sa.sql.ColumnElement] = {
        "name": GangSet.name,
        "status": GangSet.status,
        "member_count": func.coalesce(member_count_sq.c.member_count, 0),
        "updated_at": GangSet.updated_at,
        "created_at": GangSet.created_at,
    }
    primary = sort_cols.get(sort, GangSet.name)
    primary = primary.desc() if order == "desc" else primary.asc()
    # Stable secondary sort so ties don't reshuffle across paginated requests.
    stmt = stmt.order_by(primary, GangSet.name.asc(), GangSet.id.asc())
    stmt = stmt.offset(offset).limit(limit)

    rows = (await session.execute(stmt)).all()
    items: list[GangSet] = []
    for row in rows:
        obj: GangSet = row[0]
        # SQLModel/Pydantic v2 rejects unknown __setattr__; bypass like attach_primary_photos.
        object.__setattr__(obj, "_member_count", int(row[1] or 0))
        object.__setattr__(obj, "_alliance_name", row[2])
        object.__setattr__(obj, "_gang_name", row[3])
        object.__setattr__(obj, "_municipality_name", row[4])
        items.append(obj)
    return items, total


async def update_gang_set(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: SetUpdate
) -> GangSet | None:
    obj = await get_gang_set(session, id, universe_id)
    if obj is None:
        return None
    if obj.is_reserved:
        dump = data.model_dump(exclude_unset=True)
        forbidden = set(dump) - {"bio"}
        if forbidden:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Reserved sets only accept bio updates; rejected fields: {sorted(forbidden)}",
            )
        if "bio" in dump:
            obj.bio = dump["bio"]
            obj.updated_at = datetime.utcnow()
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
        return obj
    dump = data.model_dump(exclude_unset=True, exclude={"territory_ids", "friend_ids", "enemy_ids"})
    for k, v in dump.items():
        setattr(obj, k, v)
    if "name" in dump:
        obj.slug = await _unique_slug(session, obj.universe_id, obj.name, exclude_id=obj.id)
    obj.updated_at = datetime.utcnow()
    session.add(obj)
    if data.territory_ids is not None:
        # Validate against the post-update municipality_id (we may be updating
        # both at the same time).
        await _validate_territory_ids(session, obj.municipality_id, data.territory_ids)
        await _sync_set_municipalities(session, obj.id, data.territory_ids)
    if data.friend_ids is not None or data.enemy_ids is not None:
        friend_ids = data.friend_ids if data.friend_ids is not None else []
        enemy_ids = data.enemy_ids if data.enemy_ids is not None else []
        await _sync_set_relationships(session, obj.id, friend_ids, enemy_ids)
    if "alliance_id" in dump and obj.alliance_id:
        await _sync_alliance_auto_allies(session, obj.id, obj.alliance_id)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_gang_set(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_gang_set(session, id, universe_id)
    if obj is None:
        return False
    if obj.is_reserved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reserved sets (Civilian, Police) cannot be deleted.",
        )
    await session.delete(obj)
    await session.commit()
    return True


_RESERVED_SETS = [("Civilian", "civilian"), ("Police", "police")]


async def seed_reserved_sets(session: AsyncSession, universe_id: uuid.UUID) -> None:
    for name, slug in _RESERVED_SETS:
        obj = GangSet(universe_id=universe_id, name=name, slug=slug, is_reserved=True)
        session.add(obj)
    await session.commit()


async def list_set_territory_ids(
    session: AsyncSession, set_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(SetMunicipality.municipality_id).where(SetMunicipality.set_id == set_id)
    )
    return result.scalars().all()


async def list_set_relationships(
    session: AsyncSession, set_id: uuid.UUID, universe_id: uuid.UUID
) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    result = await session.execute(
        select(SetRelationship).where(
            (SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id)
        )
    )
    rels = result.scalars().all()
    friend_ids = []
    enemy_ids = []
    for r in rels:
        other = r.set_b_id if r.set_a_id == set_id else r.set_a_id
        if r.relationship_type == SetRelationshipType.FRIEND:
            friend_ids.append(other)
        else:
            enemy_ids.append(other)
    return friend_ids, enemy_ids


async def add_set_relationship(
    session: AsyncSession,
    set_a_id: uuid.UUID,
    set_b_id: uuid.UUID,
    rel_type: SetRelationshipType,
    universe_id: uuid.UUID,
) -> None:
    a, b = (set_a_id, set_b_id) if set_a_id < set_b_id else (set_b_id, set_a_id)
    existing = await session.execute(
        select(SetRelationship).where(
            SetRelationship.set_a_id == a, SetRelationship.set_b_id == b
        )
    )
    ex = existing.scalar_one_or_none()
    if ex is not None:
        if ex.relationship_type != rel_type:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Relationship already exists with a different type",
            )
        return
    session.add(SetRelationship(set_a_id=a, set_b_id=b, relationship_type=rel_type))
    await session.commit()


async def remove_set_relationship(
    session: AsyncSession, set_a_id: uuid.UUID, set_b_id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    a, b = (set_a_id, set_b_id) if set_a_id < set_b_id else (set_b_id, set_a_id)
    result = await session.execute(
        select(SetRelationship).where(
            SetRelationship.set_a_id == a, SetRelationship.set_b_id == b
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def list_set_territories_detail(
    session: AsyncSession, set_id: uuid.UUID
) -> list[dict]:
    """Return [{id, name, slug}] for the set's claimed sub-municipalities."""
    rows = await session.execute(
        select(Municipality.id, Municipality.name)
        .join(SetMunicipality, SetMunicipality.municipality_id == Municipality.id)
        .where(SetMunicipality.set_id == set_id)
        .order_by(Municipality.name.asc())
    )
    # Municipality has no slug column; routes use UUID.
    return [{"id": r[0], "name": r[1], "slug": None} for r in rows]


async def list_set_relationships_detail(
    session: AsyncSession, set_id: uuid.UUID, universe_id: uuid.UUID
) -> tuple[list[dict], list[dict]]:
    """Return (allies, enemies) as lists of {id, name, slug, status, member_count}."""
    rels = (await session.execute(
        select(SetRelationship).where(
            (SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id)
        )
    )).scalars().all()
    if not rels:
        return [], []

    by_other: dict[uuid.UUID, SetRelationshipType] = {}
    for r in rels:
        other = r.set_b_id if r.set_a_id == set_id else r.set_a_id
        by_other[other] = r.relationship_type

    member_count_sq = (
        select(Member.set_id, func.count(Member.id).label("c"))
        .group_by(Member.set_id)
        .subquery()
    )
    rows = (await session.execute(
        select(
            GangSet.id, GangSet.name, GangSet.slug, GangSet.status,
            func.coalesce(member_count_sq.c.c, 0),
        )
        .select_from(GangSet)
        .join(member_count_sq, member_count_sq.c.set_id == GangSet.id, isouter=True)
        .where(GangSet.id.in_(by_other.keys()), GangSet.universe_id == universe_id)
        .order_by(GangSet.name.asc())
    )).all()

    allies, enemies = [], []
    for r in rows:
        item = {"id": r[0], "name": r[1], "slug": r[2], "status": r[3], "member_count": int(r[4] or 0)}
        if by_other[r[0]] == SetRelationshipType.FRIEND:
            allies.append(item)
        else:
            enemies.append(item)
    return allies, enemies


async def list_set_incidents_per_year(
    session: AsyncSession, set_id: uuid.UUID, since_year: int
) -> list[dict]:
    """Per-year incident counts (year ≥ since_year) for incidents involving any
    member of this set OR the set itself as an IncidentSetParticipant.
    Returns list of {year, count}, ascending by year."""
    from app.models.incident import Incident, IncidentParticipant, IncidentSetParticipant

    member_incidents = (
        select(
            sa.cast(Incident.date["year"].astext, sa.Integer).label("year"),
            Incident.id.label("inc_id"),
        )
        .select_from(Incident)
        .join(IncidentParticipant, IncidentParticipant.incident_id == Incident.id)
        .join(Member, Member.id == IncidentParticipant.member_id)
        .where(Member.set_id == set_id)
        .where(Incident.date.isnot(None))
        .where(Incident.date["year"].astext.op("~")(r"^\d+$"))
    )
    set_incidents = (
        select(
            sa.cast(Incident.date["year"].astext, sa.Integer).label("year"),
            Incident.id.label("inc_id"),
        )
        .select_from(Incident)
        .join(IncidentSetParticipant, IncidentSetParticipant.incident_id == Incident.id)
        .where(IncidentSetParticipant.set_id == set_id)
        .where(Incident.date.isnot(None))
        .where(Incident.date["year"].astext.op("~")(r"^\d+$"))
    )

    union_sq = member_incidents.union(set_incidents).subquery()
    distinct_sq = select(union_sq.c.year, union_sq.c.inc_id).distinct().subquery()
    rows = (await session.execute(
        select(distinct_sq.c.year, func.count())
        .where(distinct_sq.c.year >= since_year)
        .group_by(distinct_sq.c.year)
        .order_by(distinct_sq.c.year.asc())
    )).all()
    return [{"year": int(r[0]), "count": int(r[1])} for r in rows]


async def get_set_max_updated_at(
    session: AsyncSession, set_id: uuid.UUID
) -> Optional[datetime]:
    """Newest updated_at across the set + its members. Used for ETag."""
    set_ts = (await session.execute(
        select(GangSet.updated_at).where(GangSet.id == set_id)
    )).scalar_one_or_none()
    member_ts = (await session.execute(
        select(func.max(Member.updated_at)).where(Member.set_id == set_id)
    )).scalar_one_or_none()
    candidates = [t for t in (set_ts, member_ts) if t is not None]
    return max(candidates) if candidates else None


async def search_gang_sets(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[GangSet]:
    pattern = f"%{q}%"
    result = await session.execute(
        select(GangSet).where(
            GangSet.universe_id == universe_id,
            GangSet.name.ilike(pattern)
            | sa.cast(GangSet.name_variants, sa.Text).ilike(pattern),
        )
    )
    return result.scalars().all()
