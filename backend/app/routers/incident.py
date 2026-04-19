import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import incident as crud
from app.schemas.common import CursorPage
from app.schemas.incident import (
    IncidentCreate,
    IncidentListItem,
    IncidentRead,
    IncidentReadDetail,
    IncidentUpdate,
    ParticipantRead,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/", response_model=CursorPage[IncidentListItem])
async def list_incidents(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
):
    items, next_cursor = await crud.list_incidents(session, universe_id, limit=limit, cursor=cursor)
    return CursorPage(items=items, next_cursor=next_cursor, total=None)


@router.post("/", response_model=IncidentRead, status_code=201)
async def create_incident(
    data: IncidentCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_incident(session, data, current_user.id)


@router.get("/search", response_model=list[IncidentListItem])
async def search_incidents(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.search_incidents(session, universe_id, q)


@router.get("/{id}", response_model=IncidentReadDetail)
async def get_incident(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_incident(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    participants = await crud.list_incident_participants(session, id)
    source_ids = await crud.list_incident_source_ids(session, id)
    participant_reads = [ParticipantRead.model_validate(p) for p in participants]
    return IncidentReadDetail.model_validate(obj).model_copy(
        update={"participants": participant_reads, "source_ids": source_ids}
    )


@router.patch("/{id}", response_model=IncidentRead)
async def update_incident(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: IncidentUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_incident(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_incident(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_incident(session, id, universe_id)
    if not ok:
        raise HTTPException(404)
