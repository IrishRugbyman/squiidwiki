import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.auth import UserUniverseAccess
from app.models.universe import Universe
from app.schemas.universe import UniverseCreate, UniverseUpdate
from app.crud.gang_set import seed_reserved_sets


async def create_universe(
    session: AsyncSession, data: UniverseCreate, actor_id: uuid.UUID
) -> Universe:
    obj = Universe(**data.model_dump(), created_by_id=actor_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    await seed_reserved_sets(session, obj.id)
    return obj


async def get_universe(session: AsyncSession, id: uuid.UUID) -> Universe | None:
    return await session.get(Universe, id)


async def list_universes(
    session: AsyncSession, offset: int = 0, limit: int = 50
) -> tuple[list[Universe], int]:
    count_result = await session.execute(select(func.count()).select_from(Universe))
    total = count_result.scalar_one()
    result = await session.execute(select(Universe).offset(offset).limit(limit))
    return result.scalars().all(), total


async def list_universes_for_user(
    session: AsyncSession, user_id: uuid.UUID, offset: int = 0, limit: int = 50
) -> tuple[list[Universe], int]:
    stmt = (
        select(Universe)
        .join(UserUniverseAccess, UserUniverseAccess.universe_id == Universe.id)
        .where(UserUniverseAccess.user_id == user_id)
    )
    count_result = await session.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()
    result = await session.execute(stmt.offset(offset).limit(limit))
    return result.scalars().all(), total


async def user_has_universe_access(
    session: AsyncSession, user_id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    row = await session.execute(
        select(UserUniverseAccess).where(
            UserUniverseAccess.user_id == user_id,
            UserUniverseAccess.universe_id == universe_id,
        )
    )
    return row.scalar_one_or_none() is not None


async def update_universe(
    session: AsyncSession, id: uuid.UUID, data: UniverseUpdate
) -> Universe | None:
    obj = await session.get(Universe, id)
    if obj is None:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_universe(session: AsyncSession, id: uuid.UUID) -> bool:
    obj = await session.get(Universe, id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True
