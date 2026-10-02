import json
import uuid
from datetime import UTC, datetime
from typing import Literal

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy import case, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.enums import SetRelationshipType, SetStatus
from app.core.fuzzy_date import FuzzyDate
from app.core.slug import slugify
from app.models.alliance import Alliance, AllianceSet
from app.models.gang import Gang
from app.models.gang_set import (
    GangSet,
    SetGang,
    SetLineage,
    SetMunicipality,
    SetRelationship,
    SetSource,
)
from app.models.member import Member, MemberSet
from app.models.municipality import Municipality
from app.models.source import Source
from app.schemas.gang_set import SetCreate, SetLineageCreate, SetUpdate

SortKey = Literal["name", "status", "member_count", "updated_at", "created_at"]
SortOrder = Literal["asc", "desc"]
NoneSentinel = Literal["none"]
# A filter value can be a UUID, the literal "none" (match NULL), or None (no filter).
FilterId = uuid.UUID | NoneSentinel | None


def _slugify(name: str) -> str:
    return slugify(name, "set")


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
        select(Municipality.id, Municipality.parent_id).where(Municipality.id.in_(territory_ids))
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
    """Replace the set's *current* allies and enemies.

    Closed links (until_date set) are the historical record and are never
    touched here: ending a relationship is an explicit dated action, not a side
    effect of editing the current lists. See `end_set_relationship`.

    Reconciles by diff rather than clear-and-rebuild. Deleting every row and
    re-adding looks equivalent but is not: SQLAlchemy's unit of work flushes
    INSERTs before DELETEs, so re-adding a pair that is still wanted collides
    with the surviving row on ``uq_set_relationship_current`` and surfaces as a
    500. Diffing also leaves untouched edges on their original rows instead of
    churning an id and an audit entry for every neighbour on every save.
    """

    def _pair(other: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
        return (set_id, other) if set_id < other else (other, set_id)

    desired: dict[tuple[uuid.UUID, uuid.UUID], SetRelationshipType] = {}
    for fid in friend_ids:
        desired[_pair(fid)] = SetRelationshipType.FRIEND
    for eid in enemy_ids:
        # An id in both lists is contradictory; enemy wins, matching the
        # precedence the API already applies elsewhere.
        desired[_pair(eid)] = SetRelationshipType.ENEMY
    desired.pop((set_id, set_id), None)

    existing = await session.execute(
        select(SetRelationship).where(
            (SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id),
            SetRelationship.until_date.is_(None),
        )
    )

    seen: set[tuple[uuid.UUID, uuid.UUID]] = set()
    stale = False
    for rel in existing.scalars().all():
        key = (rel.set_a_id, rel.set_b_id)
        want = desired.get(key)
        if want is not None and want == rel.relationship_type and key not in seen:
            seen.add(key)
            continue
        await session.delete(rel)
        stale = True

    if stale:
        # Land the deletes before any insert, so a pair whose type changed does
        # not race its own replacement.
        await session.flush()

    for (a, b), rel_type in desired.items():
        if (a, b) in seen:
            continue
        session.add(SetRelationship(set_a_id=a, set_b_id=b, relationship_type=rel_type))


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


async def _sync_set_gangs(session: AsyncSession, obj: GangSet, gang_ids: list[uuid.UUID]) -> None:
    """Make `set_gang` hold exactly `gang_ids`, in order, and mirror the first
    into `sets.gang_id`.

    Every gang must belong to the set's universe: a gang card is per universe,
    and a foreign one would render on the set page and never on any gang page.
    """
    if gang_ids:
        found = set(
            (
                await session.execute(
                    select(Gang.id).where(
                        Gang.id.in_(gang_ids), Gang.universe_id == obj.universe_id
                    )
                )
            ).scalars()
        )
        missing = [str(g) for g in gang_ids if g not in found]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"gang_ids not in this universe: {', '.join(missing)}",
            )
    await session.execute(delete(SetGang).where(SetGang.set_id == obj.id))
    await session.flush()
    for position, gang_id in enumerate(gang_ids):
        session.add(SetGang(set_id=obj.id, gang_id=gang_id, position=position))
    primary = gang_ids[0] if gang_ids else None
    # Assign only on change: an unconditional write is an UPDATE in audit_log
    # for every create and every unrelated edit.
    if obj.gang_id != primary:
        obj.gang_id = primary
    object.__setattr__(obj, "gang_ids", list(gang_ids))


async def _sync_set_alliances(
    session: AsyncSession, obj: GangSet, alliance_ids: list[uuid.UUID]
) -> list[uuid.UUID]:
    """Make `alliance_set` hold exactly `alliance_ids`, in order, and mirror the
    first into `sets.alliance_id`. Returns the alliances the set newly joined, so
    the caller can give it its allies there.

    Every alliance must belong to the set's universe, for the reason gangs must.
    """
    if alliance_ids:
        found = set(
            (
                await session.execute(
                    select(Alliance.id).where(
                        Alliance.id.in_(alliance_ids), Alliance.universe_id == obj.universe_id
                    )
                )
            ).scalars()
        )
        missing = [str(a) for a in alliance_ids if a not in found]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"alliance_ids not in this universe: {', '.join(missing)}",
            )
    before = set(await list_set_alliance_ids(session, obj.id))
    await session.execute(delete(AllianceSet).where(AllianceSet.set_id == obj.id))
    await session.flush()
    for position, alliance_id in enumerate(alliance_ids):
        session.add(AllianceSet(alliance_id=alliance_id, set_id=obj.id, position=position))
    primary = alliance_ids[0] if alliance_ids else None
    # Assign only on change, as for gang_id: otherwise every edit is an UPDATE.
    if obj.alliance_id != primary:
        obj.alliance_id = primary
    object.__setattr__(obj, "alliance_ids", list(alliance_ids))
    return [a for a in alliance_ids if a not in before]


async def list_set_alliance_ids(session: AsyncSession, set_id: uuid.UUID) -> list[uuid.UUID]:
    """The set's alliances, primary first."""
    rows = await session.execute(
        select(AllianceSet.alliance_id)
        .where(AllianceSet.set_id == set_id)
        .order_by(AllianceSet.position)
    )
    return list(rows.scalars())


async def list_set_alliances(
    session: AsyncSession, set_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[dict]]:
    """Every alliance of each set in `set_ids`, primary first, as summary dicts."""
    if not set_ids:
        return {}
    rows = await session.execute(
        select(AllianceSet.set_id, Alliance.id, Alliance.name, Alliance.slug)
        .join(Alliance, Alliance.id == AllianceSet.alliance_id)
        .where(AllianceSet.set_id.in_(set_ids))
        .order_by(AllianceSet.set_id, AllianceSet.position)
    )
    out: dict[uuid.UUID, list[dict]] = {}
    for set_id, aid, name, slug in rows:
        out.setdefault(set_id, []).append({"id": aid, "name": name, "slug": slug})
    return out


def _alliance_ids_from(
    fields_set: set[str], alliance_ids, legacy, current: list[uuid.UUID]
) -> list[uuid.UUID] | None:
    """The complete alliance list a create or update asks for, or None to keep.

    `alliance_ids` wins. A legacy single `alliance_id` makes that alliance the
    primary and keeps the others, and null clears them all, as for gangs.
    """
    if "alliance_ids" in fields_set:
        return list(alliance_ids or [])
    if "alliance_id" in fields_set:
        if legacy is None:
            return []
        return [legacy] + [a for a in current if a != legacy]
    return None


async def list_set_gang_ids(session: AsyncSession, set_id: uuid.UUID) -> list[uuid.UUID]:
    """The set's gangs, primary first."""
    rows = await session.execute(
        select(SetGang.gang_id).where(SetGang.set_id == set_id).order_by(SetGang.position)
    )
    return list(rows.scalars())


async def list_set_gangs(
    session: AsyncSession, set_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[dict]]:
    """Every gang of each set in `set_ids`, primary first, as summary dicts."""
    if not set_ids:
        return {}
    rows = await session.execute(
        select(SetGang.set_id, Gang.id, Gang.name, Gang.slug, Gang.color)
        .join(Gang, Gang.id == SetGang.gang_id)
        .where(SetGang.set_id.in_(set_ids))
        .order_by(SetGang.set_id, SetGang.position)
    )
    out: dict[uuid.UUID, list[dict]] = {}
    for set_id, gid, name, slug, color in rows:
        out.setdefault(set_id, []).append({"id": gid, "name": name, "slug": slug, "color": color})
    return out


async def attach_gang_ids(session: AsyncSession, obj: GangSet) -> GangSet:
    """Put `gang_ids` and `alliance_ids` on a single ORM row for SetRead."""
    object.__setattr__(obj, "gang_ids", await list_set_gang_ids(session, obj.id))
    object.__setattr__(obj, "alliance_ids", await list_set_alliance_ids(session, obj.id))
    return obj


_RESERVED_NAMES = {"civilian", "police", "unknown"}


async def _sync_set_sources(
    session: AsyncSession, set_id: uuid.UUID, universe_id: uuid.UUID, source_ids: list[uuid.UUID]
) -> None:
    """Replace a set's citations with `source_ids`.

    Each must belong to the set's universe: `set_source` has no universe column,
    so without this check it would accept a source from another universe.
    """
    wanted = list(dict.fromkeys(source_ids))
    if wanted:
        found = set(
            (
                await session.execute(
                    select(Source.id).where(
                        Source.id.in_(wanted), Source.universe_id == universe_id
                    )
                )
            )
            .scalars()
            .all()
        )
        missing = [str(i) for i in wanted if i not in found]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Sources not found in this universe: {', '.join(missing)}",
            )
    await session.execute(delete(SetSource).where(SetSource.set_id == set_id))
    for sid in wanted:
        session.add(SetSource(set_id=set_id, source_id=sid))


async def list_set_source_ids(session: AsyncSession, set_id: uuid.UUID) -> list[uuid.UUID]:
    rows = await session.execute(select(SetSource.source_id).where(SetSource.set_id == set_id))
    return list(rows.scalars().all())


async def list_set_sources(session: AsyncSession, set_id: uuid.UUID) -> list[Source]:
    rows = await session.execute(
        select(Source)
        .join(SetSource, SetSource.source_id == Source.id)
        .where(SetSource.set_id == set_id)
        .order_by(Source.title)
    )
    return list(rows.scalars().all())


async def create_gang_set(session: AsyncSession, data: SetCreate, actor_id: uuid.UUID) -> GangSet:
    if data.name.strip().lower() in _RESERVED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{data.name}' is a reserved system set name and cannot be used.",
        )
    await _validate_territory_ids(session, data.municipality_id, data.territory_ids)
    if data.gang_ids is not None:
        gang_ids = data.gang_ids
    else:
        gang_ids = [data.gang_id] if data.gang_id else []
    # As for gangs: the list when sent, else the legacy single id. SetCreate's
    # validator touches alliance_ids, so model_fields_set cannot tell them apart.
    if data.alliance_ids is not None:
        alliance_ids = data.alliance_ids
    else:
        alliance_ids = [data.alliance_id] if data.alliance_id else []
    dump = data.model_dump(
        exclude={
            "territory_ids",
            "friend_ids",
            "enemy_ids",
            "gang_ids",
            "alliance_ids",
            "source_ids",
        }
    )
    # The mirrors go in with the INSERT, so a create is one audit row, not two.
    dump["gang_id"] = gang_ids[0] if gang_ids else None
    dump["alliance_id"] = alliance_ids[0] if alliance_ids else None
    slug = await _unique_slug(session, data.universe_id, data.name)
    obj = GangSet(**dump, slug=slug, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_set_gangs(session, obj, gang_ids)
    joined = await _sync_set_alliances(session, obj, alliance_ids)
    await _sync_set_municipalities(session, obj.id, data.territory_ids)
    await _sync_set_relationships(session, obj.id, data.friend_ids, data.enemy_ids)
    await _sync_set_sources(session, obj.id, obj.universe_id, data.source_ids)
    for alliance_id in joined:
        await _sync_alliance_auto_allies(session, obj.id, alliance_id)
    await session.commit()
    await session.refresh(obj)
    return await attach_gang_ids(session, obj)


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
    reserved: bool | None = None,
):
    stmt = stmt.where(GangSet.universe_id == universe_id)
    # None: everything. False: the real sets only. True: the system sets only.
    if reserved is not None:
        stmt = stmt.where(GangSet.is_reserved.is_(reserved))
    if q and len(q.strip()) >= 2:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            GangSet.name.ilike(pattern) | sa.cast(GangSet.name_variants, sa.Text).ilike(pattern)
        )
    if status_filter is not None:
        stmt = stmt.where(GangSet.status == status_filter)
    if alliance_id == "none":
        # alliance_id mirrors the primary, so NULL there means no alliance at all.
        stmt = stmt.where(GangSet.alliance_id.is_(None))
    elif alliance_id is not None:
        # Any of the set's alliances, not only the primary.
        stmt = stmt.where(
            sa.exists().where(
                AllianceSet.set_id == GangSet.id, AllianceSet.alliance_id == alliance_id
            )
        )
    if gang_id == "none":
        # gang_id mirrors the primary, so NULL there means no set_gang row at all.
        stmt = stmt.where(GangSet.gang_id.is_(None))
    elif gang_id is not None:
        # Any of the set's gangs, not only the primary.
        stmt = stmt.where(
            sa.exists().where(SetGang.set_id == GangSet.id, SetGang.gang_id == gang_id)
        )
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
    reserved: bool | None = None,
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
        reserved=reserved,
    )
    total = (await session.execute(count_stmt)).scalar_one()

    member_count_sq = (
        select(
            MemberSet.set_id, func.count(func.distinct(MemberSet.member_id)).label("member_count")
        )
        # Current roster: members who have left keep their row but are not counted.
        .where(MemberSet.until_date.is_(None))
        .group_by(MemberSet.set_id)
        .subquery()
    )

    stmt = (
        select(
            GangSet,
            func.coalesce(member_count_sq.c.member_count, 0).label("member_count"),
            Alliance.name.label("alliance_name"),
            Gang.name.label("gang_name"),
            Gang.color.label("gang_color"),
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
        reserved=reserved,
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
        object.__setattr__(obj, "_gang_color", row[4])
        object.__setattr__(obj, "_municipality_name", row[5])
        items.append(obj)
    gangs = await list_set_gangs(session, [o.id for o in items])
    alliances = await list_set_alliances(session, [o.id for o in items])
    for obj in items:
        object.__setattr__(obj, "_gangs", gangs.get(obj.id, []))
        object.__setattr__(obj, "_alliances", alliances.get(obj.id, []))
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
            obj.updated_at = datetime.now(UTC)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
        return obj
    dump = data.model_dump(
        exclude_unset=True,
        exclude={
            "territory_ids",
            "friend_ids",
            "enemy_ids",
            "gang_ids",
            "alliance_ids",
            "source_ids",
        },
    )
    # gang_id and alliance_id are never written directly: each mirrors
    # position 0 of its join table.
    legacy_sent = "gang_id" in dump
    legacy_gang = dump.pop("gang_id", None)
    dump.pop("alliance_id", None)
    old_name = obj.name
    for k, v in dump.items():
        setattr(obj, k, v)
    if "name_variants" in dump:
        sa.orm.attributes.flag_modified(obj, "name_variants")
    if "gang_ids" in data.model_fields_set:
        await _sync_set_gangs(session, obj, data.gang_ids or [])
    elif legacy_sent:
        # A caller that knows only the single field: that gang becomes the
        # primary and the others stay; null clears the lot.
        if legacy_gang is None:
            await _sync_set_gangs(session, obj, [])
        else:
            current = await list_set_gang_ids(session, obj.id)
            await _sync_set_gangs(
                session, obj, [legacy_gang] + [g for g in current if g != legacy_gang]
            )
    # SQLModel/SQLAlchemy doesn't auto-detect mutations on JSONB dicts assigned
    # via setattr; flag_modified ensures a polygon update actually gets flushed.
    if "emojis" in dump:
        sa.orm.attributes.flag_modified(obj, "emojis")
    if "territory_polygon" in dump:
        sa.orm.attributes.flag_modified(obj, "territory_polygon")
    if "territory_point" in dump:
        sa.orm.attributes.flag_modified(obj, "territory_point")
    # name is re-derived on every variants edit; only a real rename re-slugs,
    # so a link to the set survives an edit that leaves its name alone.
    if obj.name != old_name:
        obj.slug = await _unique_slug(session, obj.universe_id, obj.name, exclude_id=obj.id)
    obj.updated_at = datetime.now(UTC)
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
    if data.source_ids is not None:
        await _sync_set_sources(session, obj.id, obj.universe_id, data.source_ids)
    wanted = _alliance_ids_from(
        data.model_fields_set,
        data.alliance_ids,
        data.alliance_id,
        await list_set_alliance_ids(session, obj.id),
    )
    if wanted is not None:
        for alliance_id in await _sync_set_alliances(session, obj, wanted):
            await _sync_alliance_auto_allies(session, obj.id, alliance_id)
    await session.commit()
    await session.refresh(obj)
    return await attach_gang_ids(session, obj)


async def delete_gang_set(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_gang_set(session, id, universe_id)
    if obj is None:
        return False
    if obj.is_reserved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reserved sets (Civilian, Police, Unknown) cannot be deleted.",
        )
    # These join tables reference sets without ON DELETE, so any row in them
    # blocked the delete with a foreign-key error. The rest (member_set, media,
    # business_set, incident_set_participant, alliance_relationship) cascade.
    await session.execute(
        delete(SetRelationship).where(
            (SetRelationship.set_a_id == id) | (SetRelationship.set_b_id == id)
        )
    )
    await session.execute(
        delete(SetLineage).where((SetLineage.parent_id == id) | (SetLineage.child_id == id))
    )
    await session.execute(delete(SetSource).where(SetSource.set_id == id))
    await session.execute(delete(SetMunicipality).where(SetMunicipality.set_id == id))
    await session.execute(delete(AllianceSet).where(AllianceSet.set_id == id))  # cascades too
    await session.delete(obj)
    await session.commit()
    return True


# Unknown is the holding pen: a member whose set is not yet known sits here
# rather than nowhere, so the gap is a queue to work through and not an absence.
_RESERVED_SETS = [("Civilian", "civilian"), ("Police", "police"), ("Unknown", "unknown")]


async def seed_reserved_sets(session: AsyncSession, universe_id: uuid.UUID) -> None:
    for name, slug in _RESERVED_SETS:
        obj = GangSet(universe_id=universe_id, name=name, slug=slug, is_reserved=True)
        session.add(obj)
    await session.commit()


async def list_set_polygons(
    session: AsyncSession,
    universe_id: uuid.UUID,
    municipality_id: uuid.UUID | None = None,
) -> list[dict]:
    """Return all sets in `universe_id` that have a non-null territory_polygon or territory_point.
    Optionally narrow to those anchored at `municipality_id`."""
    # Exclude both SQL NULL and JSONB null for each spatial field.
    polygon_present = GangSet.territory_polygon.isnot(None) & (
        sa.cast(GangSet.territory_polygon, sa.Text) != "null"
    )
    point_present = GangSet.territory_point.isnot(None) & (
        sa.cast(GangSet.territory_point, sa.Text) != "null"
    )
    stmt = (
        select(
            GangSet.id,
            GangSet.name,
            GangSet.slug,
            GangSet.status,
            GangSet.municipality_id,
            GangSet.alliance_id,
            GangSet.gang_id,
            Gang.color,
            Gang.color_secondary,
            GangSet.territory_polygon,
            GangSet.territory_point,
        )
        .select_from(GangSet)
        .join(Gang, Gang.id == GangSet.gang_id, isouter=True)
        .where(GangSet.universe_id == universe_id)
        .where(polygon_present | point_present)
    )
    if municipality_id is not None:
        stmt = stmt.where(GangSet.municipality_id == municipality_id)
    rows = (await session.execute(stmt)).all()
    gangs = await list_set_gangs(session, [r[0] for r in rows])
    alliances = await list_set_alliances(session, [r[0] for r in rows])
    return [
        {
            "id": r[0],
            "name": r[1],
            "slug": r[2],
            "status": r[3],
            "municipality_id": r[4],
            "alliance_id": r[5],
            # Every alliance, primary first: the alliance view draws the set's
            # zone into each of them.
            "alliance_ids": [a["id"] for a in alliances.get(r[0], [])],
            "gang_id": r[6],
            "gang_color": r[7],
            "gang_color_secondary": r[8],
            # Each gang's main colour, primary first, for a set claiming several:
            # the map stripes those instead of the primary's own two colours.
            "gang_colors": [g["color"] for g in gangs.get(r[0], []) if g["color"]],
            "territory_polygon": r[9],
            "territory_point": r[10],
        }
        for r in rows
    ]


async def list_set_territory_ids(session: AsyncSession, set_id: uuid.UUID) -> list[uuid.UUID]:
    result = await session.execute(
        select(SetMunicipality.municipality_id).where(SetMunicipality.set_id == set_id)
    )
    return result.scalars().all()


async def batch_load_set_territory_ids(
    session: AsyncSession, set_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[uuid.UUID]]:
    if not set_ids:
        return {}
    result = await session.execute(
        select(SetMunicipality.set_id, SetMunicipality.municipality_id).where(
            SetMunicipality.set_id.in_(set_ids)
        )
    )
    out: dict[uuid.UUID, list[uuid.UUID]] = {sid: [] for sid in set_ids}
    for row in result.all():
        out[row.set_id].append(row.municipality_id)
    return out


async def list_set_relationships(
    session: AsyncSession, set_id: uuid.UUID, universe_id: uuid.UUID
) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    result = await session.execute(
        select(SetRelationship).where(
            (SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id),
            # Current allies and enemies only; past ones live in the history.
            SetRelationship.until_date.is_(None),
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
    from_date: FuzzyDate | None = None,
) -> None:
    """Open a relationship spell between two sets.

    `from_date` is when the link began, which for a beef is usually the
    incident that started it and is often known only to the year. Left null it
    reads as "for as long as anyone recorded", which is a different claim from
    a dated start, so it is worth setting when the date is known.
    """
    a, b = (set_a_id, set_b_id) if set_a_id < set_b_id else (set_b_id, set_a_id)
    existing = await session.execute(
        select(SetRelationship).where(
            SetRelationship.set_a_id == a,
            SetRelationship.set_b_id == b,
            SetRelationship.until_date.is_(None),
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
    session.add(
        SetRelationship(
            set_a_id=a,
            set_b_id=b,
            relationship_type=rel_type,
            # The column is plain JSONB, not the FuzzyDate TypeDecorator, so
            # the object has to be dumped here as it is for member_set.
            from_date=from_date.model_dump() if from_date is not None else None,
        )
    )
    await session.commit()


async def remove_set_relationship(
    session: AsyncSession, set_a_id: uuid.UUID, set_b_id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    """Delete the *current* link outright, for correcting a mistaken entry.

    To record that a real relationship ended, use `end_set_relationship`, which
    keeps the spell. Scoped to the open row because a pair can now hold several
    and scalar_one_or_none() would raise on the closed ones.
    """
    a, b = (set_a_id, set_b_id) if set_a_id < set_b_id else (set_b_id, set_a_id)
    result = await session.execute(
        select(SetRelationship).where(
            SetRelationship.set_a_id == a,
            SetRelationship.set_b_id == b,
            SetRelationship.until_date.is_(None),
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def end_set_relationship(
    session: AsyncSession,
    set_id: uuid.UUID,
    relationship_id: uuid.UUID,
    until_date: dict | None,
) -> bool:
    """Close an open link as of a date, keeping it as history.

    Only open links can be closed: re-closing a closed one would rewrite the
    record rather than state that the relationship ended.
    """
    row = (
        await session.execute(
            select(SetRelationship).where(
                SetRelationship.id == relationship_id,
                (SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id),
                SetRelationship.until_date.is_(None),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    row.until_date = until_date
    await session.commit()
    return True


async def list_set_relationship_history(session: AsyncSession, set_id: uuid.UUID) -> list[dict]:
    """Every link this set has held, current first, then most recently ended."""
    rows = (
        await session.execute(
            select(
                SetRelationship.id,
                SetRelationship.set_a_id,
                SetRelationship.set_b_id,
                SetRelationship.relationship_type,
                SetRelationship.from_date,
                SetRelationship.until_date,
                GangSet.name,
                GangSet.slug,
            )
            .join(
                GangSet,
                GangSet.id
                == case(
                    (SetRelationship.set_a_id == set_id, SetRelationship.set_b_id),
                    else_=SetRelationship.set_a_id,
                ),
            )
            .where((SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id))
            .order_by(
                SetRelationship.until_date.is_(None).desc(),
                SetRelationship.until_date.desc().nullslast(),
                SetRelationship.from_date.desc().nullslast(),
            )
        )
    ).all()
    return [
        {
            "id": rel_id,
            "other_id": b if a == set_id else a,
            "other_name": name,
            "other_slug": slug,
            "type": rel_type,
            "from_date": from_date,
            "until_date": until_date,
            "is_current": until_date is None,
        }
        for rel_id, a, b, rel_type, from_date, until_date, name, slug in rows
    ]


async def list_set_territories_detail(session: AsyncSession, set_id: uuid.UUID) -> list[dict]:
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
    rels = (
        (
            await session.execute(
                select(SetRelationship).where(
                    (SetRelationship.set_a_id == set_id) | (SetRelationship.set_b_id == set_id),
                    SetRelationship.until_date.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    if not rels:
        return [], []

    by_other: dict[uuid.UUID, SetRelationshipType] = {}
    for r in rels:
        other = r.set_b_id if r.set_a_id == set_id else r.set_a_id
        by_other[other] = r.relationship_type

    member_count_sq = (
        select(MemberSet.set_id, func.count(func.distinct(MemberSet.member_id)).label("c"))
        .where(MemberSet.until_date.is_(None))
        .group_by(MemberSet.set_id)
        .subquery()
    )
    rows = (
        await session.execute(
            select(
                GangSet.id,
                GangSet.name,
                GangSet.slug,
                GangSet.status,
                func.coalesce(member_count_sq.c.c, 0),
            )
            .select_from(GangSet)
            .join(member_count_sq, member_count_sq.c.set_id == GangSet.id, isouter=True)
            .where(GangSet.id.in_(by_other.keys()), GangSet.universe_id == universe_id)
            .order_by(GangSet.name.asc())
        )
    ).all()

    allies, enemies = [], []
    for r in rows:
        item = {
            "id": r[0],
            "name": r[1],
            "slug": r[2],
            "status": r[3],
            "member_count": int(r[4] or 0),
        }
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
        .join(MemberSet, (MemberSet.member_id == Member.id) & (MemberSet.set_id == set_id))
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
    rows = (
        await session.execute(
            select(distinct_sq.c.year, func.count())
            .where(distinct_sq.c.year >= since_year)
            .group_by(distinct_sq.c.year)
            .order_by(distinct_sq.c.year.asc())
        )
    ).all()
    return [{"year": int(r[0]), "count": int(r[1])} for r in rows]


async def list_set_activity(
    session: AsyncSession, set_id: uuid.UUID, *, limit: int = 20
) -> list[dict]:
    """Audit-log feed scoped to this set + its members. Returns dicts ready
    for SetActivityEntry, with actor email and target label denormalized."""
    from app.models.auth import AuditLog, User

    # Fetch the set's current member ids in one query.
    member_ids = (
        (
            await session.execute(
                select(MemberSet.member_id).where(
                    MemberSet.set_id == set_id, MemberSet.until_date.is_(None)
                )
            )
        )
        .scalars()
        .all()
    )

    # audit_log.entity_type is the table name (see app/core/audit.py), so a set's
    # own rows are "sets"; the feed reports them as "set", its public name.
    cond = (AuditLog.entity_type == "sets") & (AuditLog.entity_id == set_id)
    if member_ids:
        cond = cond | ((AuditLog.entity_type == "member") & (AuditLog.entity_id.in_(member_ids)))

    rows = (
        await session.execute(
            select(
                AuditLog.id,
                AuditLog.entity_type,
                AuditLog.entity_id,
                AuditLog.action,
                AuditLog.diff_json,
                AuditLog.created_at,
                User.email,
            )
            .select_from(AuditLog)
            .outerjoin(User, User.id == AuditLog.user_id)
            .where(cond)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
    ).all()

    if not rows:
        return []

    # Batched label/slug lookups: which set ids and member ids do we need?
    set_ids_to_label: set[uuid.UUID] = set()
    member_ids_to_label: set[uuid.UUID] = set()
    for r in rows:
        if r[1] == "sets":
            set_ids_to_label.add(r[2])
        else:
            member_ids_to_label.add(r[2])

    set_labels: dict[uuid.UUID, tuple[str, str | None]] = {}
    if set_ids_to_label:
        srows = (
            await session.execute(
                select(GangSet.id, GangSet.name, GangSet.slug).where(
                    GangSet.id.in_(set_ids_to_label)
                )
            )
        ).all()
        set_labels = {s[0]: (s[1], s[2]) for s in srows}

    member_labels: dict[uuid.UUID, tuple[str, str | None]] = {}
    if member_ids_to_label:
        mrows = (
            await session.execute(
                select(
                    Member.id,
                    Member.nickname,
                    Member.legal_name,
                    Member.nickname_unknown,
                    Member.slug,
                ).where(Member.id.in_(member_ids_to_label))
            )
        ).all()
        for m in mrows:
            mid, nick, legal, nick_unknown, mslug = m
            display = (legal or "Unknown") if (nick_unknown or not nick) else nick
            member_labels[mid] = (display, mslug)

    out: list[dict] = []
    for r in rows:
        log_id, ent_type, ent_id, action, diff_json, created_at, email = r
        if ent_type == "sets":
            ent_type = "set"
            label, slug = set_labels.get(ent_id, (None, None))
        else:
            label, slug = member_labels.get(ent_id, (None, None))
        diff_keys = sorted(list(diff_json.keys())) if isinstance(diff_json, dict) else []
        out.append(
            {
                "id": log_id,
                "entity_type": ent_type,
                "entity_id": ent_id,
                "action": action.value if hasattr(action, "value") else str(action),
                "actor_email": email,
                "target_label": label,
                "target_slug": slug,
                "diff_keys": diff_keys,
                "created_at": created_at,
            }
        )
    return out


async def get_set_max_updated_at(session: AsyncSession, set_id: uuid.UUID) -> datetime | None:
    """Newest updated_at across the set + its members. Used for ETag."""
    set_ts = (
        await session.execute(select(GangSet.updated_at).where(GangSet.id == set_id))
    ).scalar_one_or_none()
    member_ts = (
        await session.execute(
            select(func.max(Member.updated_at)).join(
                MemberSet,
                (MemberSet.member_id == Member.id)
                & (MemberSet.set_id == set_id)
                & MemberSet.until_date.is_(None),
            )
        )
    ).scalar_one_or_none()
    candidates = [t for t in (set_ts, member_ts) if t is not None]
    return max(candidates) if candidates else None


async def search_gang_sets(session: AsyncSession, universe_id: uuid.UUID, q: str) -> list[GangSet]:
    pattern = f"%{q}%"
    result = await session.execute(
        select(GangSet).where(
            GangSet.universe_id == universe_id,
            GangSet.name.ilike(pattern) | sa.cast(GangSet.name_variants, sa.Text).ilike(pattern),
        )
    )
    return result.scalars().all()


# ── Set lineage ───────────────────────────────────────────────────────────────
#
# Directional descent, kept out of set_relationships for the reasons on the
# SetLineage model. Everything here works on *current* rows (until_date IS NULL)
# unless it says otherwise; closed rows are history and are never rewritten.


async def _lineage_would_cycle(
    session: AsyncSession, parent_id: uuid.UUID, child_id: uuid.UUID
) -> bool:
    """True if making `parent_id` the parent of `child_id` closes a loop.

    Walks the current lineage upward from `parent_id`: if `child_id` is already
    an ancestor, the new edge would make each set its own ancestor. A recursive
    CTE does the walk in one round trip and terminates on cycles that somehow
    already exist, because UNION (not UNION ALL) drops nodes it has seen.

    Self-parenting is caught by the ck_set_lineage_no_self CHECK, but is tested
    here too so the caller gets a 409 with a sentence rather than a 500 from the
    constraint.
    """
    if parent_id == child_id:
        return True
    rows = await session.execute(
        sa.text("""
            WITH RECURSIVE ancestors(id) AS (
                SELECT parent_id FROM set_lineage
                 WHERE child_id = :parent_id AND until_date IS NULL
                UNION
                SELECT l.parent_id FROM set_lineage l
                  JOIN ancestors a ON l.child_id = a.id
                 WHERE l.until_date IS NULL
            )
            SELECT 1 FROM ancestors WHERE id = :child_id LIMIT 1
        """),
        {"parent_id": str(parent_id), "child_id": str(child_id)},
    )
    return rows.first() is not None


async def add_set_lineage(
    session: AsyncSession, set_id: uuid.UUID, data: SetLineageCreate, universe_id: uuid.UUID
) -> SetLineage:
    """Open a descent spell between `set_id` and `data.other_id`.

    `direction` is read from the viewed set's point of view: "parent" means the
    other set is the one this set came out of. Both sets must be in the same
    universe - lineage across universes would be a data-entry slip, not a claim
    anyone means to make.
    """
    other = await get_gang_set(session, data.other_id, universe_id)
    if other is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Other set not found in this universe"
        )
    if data.direction == "parent":
        parent_id, child_id = data.other_id, set_id
    else:
        parent_id, child_id = set_id, data.other_id

    if await _lineage_would_cycle(session, parent_id, child_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That would make a set its own ancestor",
        )

    existing = (
        await session.execute(
            select(SetLineage).where(
                SetLineage.parent_id == parent_id,
                SetLineage.child_id == child_id,
                SetLineage.until_date.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.kind != data.kind:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="These sets already have an open lineage link of a different kind",
            )
        return existing

    row = SetLineage(
        parent_id=parent_id,
        child_id=child_id,
        kind=data.kind,
        # Plain JSONB, not the FuzzyDate TypeDecorator, so dump it here the way
        # add_set_relationship does.
        from_date=data.from_date.model_dump() if data.from_date else None,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_set_lineage(
    session: AsyncSession, set_id: uuid.UUID, include_ended: bool = True
) -> list[dict]:
    """Every descent edge touching this set, current first.

    Returned from the viewed set's point of view: `direction` says where the
    *other* set sits, so the caller never has to work out which column it came
    from.
    """
    parent_side = sa.orm.aliased(GangSet)
    child_side = sa.orm.aliased(GangSet)
    stmt = (
        select(
            SetLineage.id,
            SetLineage.parent_id,
            SetLineage.child_id,
            SetLineage.kind,
            SetLineage.from_date,
            SetLineage.until_date,
            parent_side.name.label("parent_name"),
            parent_side.slug.label("parent_slug"),
            child_side.name.label("child_name"),
            child_side.slug.label("child_slug"),
        )
        .join(parent_side, parent_side.id == SetLineage.parent_id)
        .join(child_side, child_side.id == SetLineage.child_id)
        .where((SetLineage.parent_id == set_id) | (SetLineage.child_id == set_id))
        .order_by(SetLineage.until_date.is_(None).desc(), SetLineage.id)
    )
    if not include_ended:
        stmt = stmt.where(SetLineage.until_date.is_(None))

    out = []
    for r in (await session.execute(stmt)).all():
        other_is_parent = r.child_id == set_id
        out.append(
            {
                "id": r.id,
                "kind": r.kind,
                "direction": "parent" if other_is_parent else "child",
                "other_id": r.parent_id if other_is_parent else r.child_id,
                "other_name": r.parent_name if other_is_parent else r.child_name,
                "other_slug": r.parent_slug if other_is_parent else r.child_slug,
                "from_date": r.from_date,
                "until_date": r.until_date,
                "is_current": r.until_date is None,
            }
        )
    return out


async def end_set_lineage(
    session: AsyncSession, set_id: uuid.UUID, lineage_id: uuid.UUID, until_date: dict | None
) -> bool:
    """Close an open descent spell, keeping it as history.

    Only open rows can be closed, matching end_set_relationship: re-closing a
    closed one would rewrite the record rather than state that it ended.
    """
    row = (
        await session.execute(
            select(SetLineage).where(
                SetLineage.id == lineage_id,
                (SetLineage.parent_id == set_id) | (SetLineage.child_id == set_id),
                SetLineage.until_date.is_(None),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    row.until_date = until_date
    await session.commit()
    return True


async def delete_set_lineage(
    session: AsyncSession, set_id: uuid.UUID, lineage_id: uuid.UUID
) -> bool:
    """Remove a descent row outright, for when it was entered in error.

    Ending is the right move when the link really stopped; this is for typos.
    """
    row = (
        await session.execute(
            select(SetLineage).where(
                SetLineage.id == lineage_id,
                (SetLineage.parent_id == set_id) | (SetLineage.child_id == set_id),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    await session.delete(row)
    await session.commit()
    return True


async def sets_by_emoji(session: AsyncSession, universe_id: uuid.UUID, emoji: str) -> list[GangSet]:
    """Every set that claims this emoji, in any position.

    The research direction: a glyph seen in a handle or bio, resolved back to
    the sets that use it. Several sets can share one, so this returns a list and
    the caller decides.
    """
    stmt = (
        select(GangSet)
        .where(
            GangSet.universe_id == universe_id,
            sa.text("sets.emojis @> :needle").bindparams(
                sa.bindparam("needle", value=json.dumps([emoji]), type_=sa.Text)
            ),
        )
        .order_by(GangSet.name)
    )
    return list((await session.execute(stmt)).scalars().all())
