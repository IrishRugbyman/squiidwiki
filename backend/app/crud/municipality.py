import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.municipality import Municipality
from app.schemas.municipality import MunicipalityCreate, MunicipalityUpdate


async def create_municipality(
    session: AsyncSession, data: MunicipalityCreate, actor_id: uuid.UUID
) -> Municipality:
    obj = Municipality(**data.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Municipality | None:
    result = await session.execute(
        select(Municipality).where(
            Municipality.id == id, Municipality.universe_id == universe_id
        )
    )
    return result.scalar_one_or_none()


async def list_municipalities(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 100
) -> tuple[list[Municipality], int]:
    count_result = await session.execute(
        select(func.count()).select_from(Municipality).where(
            Municipality.universe_id == universe_id
        )
    )
    total = count_result.scalar_one()
    result = await session.execute(
        select(Municipality)
        .where(Municipality.universe_id == universe_id)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


async def update_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: MunicipalityUpdate
) -> Municipality | None:
    obj = await get_municipality(session, id, universe_id)
    if obj is None:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_municipality(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_municipality(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def search_municipalities(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[Municipality]:
    result = await session.execute(
        select(Municipality).where(
            Municipality.universe_id == universe_id,
            Municipality.name.ilike(f"%{q}%"),
        )
    )
    return result.scalars().all()
