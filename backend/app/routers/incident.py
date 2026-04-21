import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.core.csv_export import to_csv_response
from app.crud import incident as crud
from app.models.incident import IncidentParticipant
from app.models.member import Member
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


async def _enrich_victim_names(session: AsyncSession, items: list) -> list:
    if not items:
        return items
    incident_ids = [inc.id for inc in items]
    ip = IncidentParticipant.__table__
    m = Member.__table__
    display_name = case(
        (m.c.nickname_unknown | m.c.nickname.is_(None), m.c.legal_name),
        else_=m.c.nickname,
    )
    rows = (await session.execute(
        select(ip.c.incident_id, display_name.label("display_name"))
        .join(m, m.c.id == ip.c.member_id)
        .where(ip.c.incident_id.in_(incident_ids))
        .where(ip.c.role == 'VICTIM')
    )).fetchall()
    victim_map: dict[str, list[str]] = {}
    for incident_id, display_name in rows:
        victim_map.setdefault(str(incident_id), []).append(display_name)
    enriched = []
    for inc in items:
        d = IncidentListItem.model_validate(inc)
        d.victim_names = victim_map.get(str(inc.id), [])
        enriched.append(d)
    return enriched


@router.get("/", response_model=CursorPage[IncidentListItem])
async def list_incidents(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
    set_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    municipality_id: uuid.UUID | None = None,
    format: str = Query("json"),
):
    if format == "csv":
        items, _ = await crud.list_incidents(session, universe_id, limit=1000)
        return to_csv_response(items, "incidents.csv")
    if set_id is not None:
        items = await crud.list_incidents_by_set(session, set_id, universe_id, limit=limit)
        return CursorPage(items=await _enrich_victim_names(session, items), next_cursor=None, total=None)
    if member_id is not None:
        items = await crud.list_incidents_by_member(session, member_id, universe_id, limit=limit)
        return CursorPage(items=await _enrich_victim_names(session, items), next_cursor=None, total=None)
    if municipality_id is not None:
        items = await crud.list_incidents_by_municipality(session, municipality_id, universe_id, limit=limit)
        return CursorPage(items=await _enrich_victim_names(session, items), next_cursor=None, total=None)
    items, next_cursor = await crud.list_incidents(session, universe_id, limit=limit, cursor=cursor)
    return CursorPage(items=await _enrich_victim_names(session, items), next_cursor=next_cursor, total=None)


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
    base = IncidentRead.model_validate(obj)
    return IncidentReadDetail(**base.model_dump(), participants=participant_reads, source_ids=source_ids)


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
