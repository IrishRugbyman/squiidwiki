import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate


def _fuzzy_to_dict(fd) -> dict | None:
    if fd is None:
        return None
    return fd.model_dump()


async def create_source(
    session: AsyncSession, data: SourceCreate, actor_id: uuid.UUID
) -> Source:
    dump = data.model_dump()
    dump["published_at"] = _fuzzy_to_dict(data.published_at)
    obj = Source(**dump, created_by_id=actor_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_source(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> Source | None:
    result = await session.execute(
        select(Source).where(Source.id == id, Source.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_sources(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 50
) -> tuple[list[Source], int]:
    count_result = await session.execute(
        select(func.count()).select_from(Source).where(Source.universe_id == universe_id)
    )
    total = count_result.scalar_one()
    result = await session.execute(
        select(Source).where(Source.universe_id == universe_id).offset(offset).limit(limit)
    )
    return result.scalars().all(), total


async def update_source(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: SourceUpdate
) -> Source | None:
    obj = await get_source(session, id, universe_id)
    if obj is None:
        return None
    dump = data.model_dump(exclude_unset=True)
    if "published_at" in dump:
        dump["published_at"] = _fuzzy_to_dict(data.published_at)
    for k, v in dump.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.utcnow()
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_source(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> bool:
    obj = await get_source(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def search_sources(
    session: AsyncSession, universe_id: uuid.UUID, q: str
) -> list[Source]:
    result = await session.execute(
        select(Source).where(
            Source.universe_id == universe_id,
            Source.title.ilike(f"%{q}%"),
        )
    )
    return result.scalars().all()
