import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.research_note import ResearchNote
from app.schemas.research_note import ResearchNoteCreate, ResearchNoteUpdate


async def create_note(
    session: AsyncSession, data: ResearchNoteCreate, actor_id: uuid.UUID
) -> ResearchNote:
    obj = ResearchNote(**data.model_dump(), created_by_id=actor_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_note(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID
) -> ResearchNote | None:
    result = await session.execute(
        select(ResearchNote).where(ResearchNote.id == id, ResearchNote.universe_id == universe_id)
    )
    return result.scalar_one_or_none()


async def list_notes(
    session: AsyncSession, universe_id: uuid.UUID, offset: int = 0, limit: int = 50
) -> tuple[list[ResearchNote], int]:
    count_result = await session.execute(
        select(func.count())
        .select_from(ResearchNote)
        .where(ResearchNote.universe_id == universe_id)
    )
    total = count_result.scalar_one()
    result = await session.execute(
        select(ResearchNote)
        .where(ResearchNote.universe_id == universe_id)
        .order_by(ResearchNote.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


async def search_notes(session: AsyncSession, universe_id: uuid.UUID, q: str) -> list[ResearchNote]:
    result = await session.execute(
        select(ResearchNote)
        .where(
            ResearchNote.universe_id == universe_id,
            (ResearchNote.title.ilike(f"%{q}%") | ResearchNote.content.ilike(f"%{q}%")),
        )
        .order_by(ResearchNote.updated_at.desc())
    )
    return result.scalars().all()


async def update_note(
    session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID, data: ResearchNoteUpdate
) -> ResearchNote | None:
    obj = await get_note(session, id, universe_id)
    if obj is None:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    obj.updated_at = datetime.now(UTC)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_note(session: AsyncSession, id: uuid.UUID, universe_id: uuid.UUID) -> bool:
    obj = await get_note(session, id, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True
