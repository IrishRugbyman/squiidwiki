from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Incident,
    IncidentSource,
    Member,
    MemberSource,
    Source,
)
from backend.sources.schemas import SourceCreate, SourceUpdate


async def get_source(db: AsyncSession, source_id: int) -> Source:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalars().first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


async def list_sources(
    db: AsyncSession,
    universe_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Source]:
    q = select(Source)
    if universe_id is not None:
        q = q.where(Source.universe_id == universe_id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


async def create_source(db: AsyncSession, data: SourceCreate) -> Source:
    source = Source(**data.model_dump())
    db.add(source)
    await db.flush()
    return source


async def update_source(db: AsyncSession, source_id: int, data: SourceUpdate) -> Source:
    source = await get_source(db, source_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    await db.flush()
    return source


async def delete_source(db: AsyncSession, source_id: int) -> None:
    source = await get_source(db, source_id)
    source.soft_delete()
    await db.flush()


async def link_member(db: AsyncSession, source_id: int, member_id: int) -> None:
    await get_source(db, source_id)
    result = await db.execute(select(Member).where(Member.id == member_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Member not found")
    db.add(MemberSource(member_id=member_id, source_id=source_id))
    await db.flush()


async def link_incident(db: AsyncSession, source_id: int, incident_id: int) -> None:
    await get_source(db, source_id)
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Incident not found")
    db.add(IncidentSource(incident_id=incident_id, source_id=source_id))
    await db.flush()
