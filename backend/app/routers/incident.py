import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.csv_export import to_csv_response
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import incident as crud
from app.crud import member as member_crud
from app.schemas.common import CursorPage
from app.schemas.incident import (
    IncidentCreate,
    IncidentListItem,
    IncidentRead,
    IncidentReadDetail,
    IncidentSourceBrief,
    IncidentUpdate,
    ParticipantRead,
    SetParticipantRead,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/", response_model=CursorPage[IncidentListItem])
async def list_incidents(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=500),
    cursor: str | None = None,
    set_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    municipality_id: uuid.UUID | None = None,
    with_coords: bool = Query(False, description="Only incidents carrying lat/lng, for maps."),
    with_date: bool = Query(False, description="Only incidents carrying a date, for the calendar."),
    format: str = Query("json"),
):
    if with_coords or with_date:
        items = await crud.list_incidents_by_capability(
            session, universe_id, needs="coords" if with_coords else "date"
        )
        return CursorPage(
            items=await crud.enrich_participant_names(session, items),
            next_cursor=None,
            total=len(items),
        )
    if format == "csv":
        # Uncapped: 1000 silently cut Illinois (3345 incidents) short.
        items, _ = await crud.list_incidents(session, universe_id, limit=1_000_000)
        return to_csv_response(items, "incidents.csv")
    if set_id is not None:
        items = await crud.list_incidents_by_set(session, set_id, universe_id, limit=limit)
        return CursorPage(
            items=await crud.enrich_participant_names(session, items), next_cursor=None, total=None
        )
    if member_id is not None:
        items = await crud.list_incidents_by_member(session, member_id, universe_id, limit=limit)
        return CursorPage(
            items=await crud.enrich_participant_names(session, items, viewer_id=member_id),
            next_cursor=None,
            total=None,
        )
    if municipality_id is not None:
        items = await crud.list_incidents_by_municipality(
            session, municipality_id, universe_id, limit=limit
        )
        return CursorPage(
            items=await crud.enrich_participant_names(session, items), next_cursor=None, total=None
        )
    items, next_cursor = await crud.list_incidents(session, universe_id, limit=limit, cursor=cursor)
    return CursorPage(
        items=await crud.enrich_participant_names(session, items),
        next_cursor=next_cursor,
        total=None,
    )


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
    if len(q.strip()) < 2:
        return []
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
    set_participants = await crud.list_incident_set_participants(session, id)
    source_ids = await crud.list_incident_source_ids(session, id)
    member_ids = [p.member_id for p in participants]
    members = await crud.participant_member_briefs(session, member_ids)
    await member_crud.attach_primary_photos(session, list(members.values()))
    member_sets = await crud.participant_current_sets(session, member_ids)
    sets = await crud.participant_set_briefs(session, [p.set_id for p in set_participants])
    participant_reads = []
    for p in participants:
        pr = ParticipantRead.model_validate(p)
        if m := members.get(p.member_id):
            pr.member_name = m.display_name
            pr.member_slug = m.slug
            pr.member_status = m.status
            pr.member_photo_url = getattr(m, "primary_photo_thumb_url", None) or getattr(
                m, "primary_photo_url", None
            )
        if gs := member_sets.get(p.member_id):
            pr.set_id, pr.set_name, pr.set_slug = gs.id, gs.name, gs.slug
        participant_reads.append(pr)
    set_participant_reads = []
    for p in set_participants:
        sr = SetParticipantRead.model_validate(p)
        if s := sets.get(p.set_id):
            sr.set_name = s.name
            sr.set_slug = s.slug
        set_participant_reads.append(sr)
    base = IncidentRead.model_validate(obj)
    return IncidentReadDetail(
        **base.model_dump(),
        participants=participant_reads,
        set_participants=set_participant_reads,
        source_ids=source_ids,
        sources=[
            IncidentSourceBrief.model_validate(src)
            for src in await crud.incident_source_briefs(session, source_ids)
        ],
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
