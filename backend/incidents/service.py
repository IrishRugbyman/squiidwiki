from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import Incident, IncidentParticipant
from backend.incidents.schemas import IncidentCreate, IncidentUpdate


async def get_incident(db: AsyncSession, incident_id: int) -> Incident:
    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.participants))
        .where(Incident.id == incident_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


async def list_incidents(
    db: AsyncSession,
    universe_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Incident]:
    q = select(Incident).options(selectinload(Incident.participants))
    if universe_id is not None:
        q = q.where(Incident.universe_id == universe_id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


async def create_incident(db: AsyncSession, data: IncidentCreate) -> Incident:
    incident = Incident(
        incident_type=data.incident_type,
        date=data.date,
        date_sortable=data.date_sortable,
        location_type=data.location_type,
        narrative=data.narrative,
        verified=data.verified,
        universe_id=data.universe_id,
    )
    db.add(incident)
    await db.flush()

    for p in data.participants:
        db.add(IncidentParticipant(
            incident_id=incident.id,
            member_id=p.member_id,
            role=p.role,
            outcome=p.outcome,
        ))

    await db.flush()
    await db.refresh(incident)
    return incident


async def update_incident(db: AsyncSession, incident_id: int, data: IncidentUpdate) -> Incident:
    incident = await get_incident(db, incident_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    await db.flush()
    return incident


async def delete_incident(db: AsyncSession, incident_id: int) -> None:
    incident = await get_incident(db, incident_id)
    incident.soft_delete()
    await db.flush()
