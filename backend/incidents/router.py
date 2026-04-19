from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.base_class import get_db
from backend.incidents import service
from backend.incidents.schemas import IncidentCreate, IncidentRead, IncidentUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/", response_model=List[IncidentRead])
async def list_incidents(
    universe_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await service.list_incidents(db, universe_id=universe_id, skip=skip, limit=limit)


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    return await service.get_incident(db, incident_id)


@router.post("/", response_model=IncidentRead, status_code=201)
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    incident = await service.create_incident(db, data)
    await db.commit()
    return incident


@router.patch("/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: int, data: IncidentUpdate, db: AsyncSession = Depends(get_db)
):
    incident = await service.update_incident(db, incident_id, data)
    await db.commit()
    return incident


@router.delete("/{incident_id}", status_code=204)
async def delete_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_incident(db, incident_id)
    await db.commit()
