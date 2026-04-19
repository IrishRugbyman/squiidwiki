import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.enums import SetRelationshipType
from app.models.gang_set import GangSet, SetMunicipality, SetRelationship
from app.schemas.gang_set import SetCreate, SetUpdate


async def _sync_set_municipalities(
    session: AsyncSession, set_id: uuid.UUID, territory_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        SetMunicipality.__table__.delete().where(SetMunicipality.set_id == set_id)
    )
    for mid in territory_ids:
        session.add(SetMunicipality(set_id=set_id, municipality_id=mid))


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


async def create_gang_set(
    session: AsyncSession, data: SetCreate, actor_id: uuid.UUID
) -> GangSet:
    dump = data.model_dump(exclude={"territory_ids", "friend_ids", "enemy_ids"})
    obj = GangSet(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.flush()
    await _sync_set_municipalities(session, obj.id, data.territory_ids)
    await _sync_set_relationships(session, obj.id, data.friend_ids, data.enemy_ids)
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


async def list_gang_sets(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 50
) -> tuple[list[GangSet], int]:
    count_result = await session.execute(
        select(func.count()).select_from(GangSet).where(GangSet.universe_id == universe_id)
    )
    total = count_result.scalar_one()
    result = await session.execute(
        select(GangSet).where(GangSet.universe_id == universe_id).offset(offset).limit(limit)
    )
    return result.scalars().all(), total


async def update_gang_set(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: SetUpdate
) -> GangSet | None:
    obj = await get_gang_set(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True, exclude={"territory_ids", "friend_ids", "enemy_ids"})
    for k, v in dump.items():
        setattr(obj, k, v)
    session.add(obj)
    if data.territory_ids is not None:
        await _sync_set_municipalities(session, obj.id, data.territory_ids)
    if data.friend_ids is not None or data.enemy_ids is not None:
        friend_ids = data.friend_ids if data.friend_ids is not None else []
        enemy_ids = data.enemy_ids if data.enemy_ids is not None else []
        await _sync_set_relationships(session, obj.id, friend_ids, enemy_ids)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_gang_set(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_gang_set(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


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


async def search_gang_sets(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[GangSet]:
    result = await session.execute(
        select(GangSet).where(
            GangSet.universe_id == universe_id,
            GangSet.name.ilike(f"%{q}%"),
        )
    )
    return result.scalars().all()
