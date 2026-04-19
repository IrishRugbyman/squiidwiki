import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.universe import Universe
from app.schemas.universe import UniverseCreate, UniverseUpdate


async def create_universe(
    session: AsyncSession, data: UniverseCreate, actor_id: uuid.UUID
) -> Universe:
    obj = Universe(**data.model_dump(), created_by_id=actor_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
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
