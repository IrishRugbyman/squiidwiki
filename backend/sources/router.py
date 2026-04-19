from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.base_class import get_db
from backend.sources import service
from backend.sources.schemas import SourceCreate, SourceRead, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/", response_model=List[SourceRead])
async def list_sources(
    universe_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await service.list_sources(db, universe_id=universe_id, skip=skip, limit=limit)


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    return await service.get_source(db, source_id)


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(data: SourceCreate, db: AsyncSession = Depends(get_db)):
    source = await service.create_source(db, data)
    await db.commit()
    return source


@router.patch("/{source_id}", response_model=SourceRead)
async def update_source(
    source_id: int, data: SourceUpdate, db: AsyncSession = Depends(get_db)
):
    source = await service.update_source(db, source_id, data)
    await db.commit()
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_source(db, source_id)
    await db.commit()


@router.post("/{source_id}/members/{member_id}", status_code=204)
async def link_member(source_id: int, member_id: int, db: AsyncSession = Depends(get_db)):
    await service.link_member(db, source_id, member_id)
    await db.commit()


@router.post("/{source_id}/incidents/{incident_id}", status_code=204)
async def link_incident(source_id: int, incident_id: int, db: AsyncSession = Depends(get_db)):
    await service.link_incident(db, source_id, incident_id)
    await db.commit()
