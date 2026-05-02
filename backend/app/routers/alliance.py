import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.core.csv_export import to_csv_response
from app.crud import alliance as crud
from app.crud import member as member_crud
from app.crud.media import attach_primary_photos_alliances
from app.crud import incident as incident_crud
from app.schemas.alliance import (
    AllianceCreate,
    AllianceListItem,
    AllianceRead,
    AllianceReadDetail,
    AllianceUpdate,
)
from app.schemas.common import CursorPage, OffsetPage
from app.schemas.member import MemberListItem
from app.schemas.incident import IncidentListItem

router = APIRouter(prefix="/alliances", tags=["alliances"])


@router.get("/", response_model=OffsetPage[AllianceListItem])
async def list_alliances(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    format: str = Query("json"),
):
    if format == "csv":
        items, _ = await crud.list_alliances(session, universe_id, offset=0, limit=1000)
        return to_csv_response(items, "alliances.csv")
    items, total = await crud.list_alliances(session, universe_id, offset=offset, limit=limit)
    await attach_primary_photos_alliances(session, items)
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=AllianceRead, status_code=201)
async def create_alliance(
    data: AllianceCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_alliance(session, data, current_user.id)


@router.get("/search", response_model=list[AllianceListItem])
async def search_alliances(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    return await crud.search_alliances(session, universe_id, q)


@router.get("/{id_or_slug}", response_model=AllianceReadDetail)
async def get_alliance(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = None
    try:
        obj = await crud.get_alliance(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await crud.get_alliance_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    territory_ids = await crud.list_alliance_territory_ids(session, obj.id)
    set_ids = await crud.list_alliance_set_ids(session, obj.id)
    base = AllianceRead.model_validate(obj)
    return AllianceReadDetail(**base.model_dump(), territory_ids=territory_ids, set_ids=set_ids)


@router.patch("/{id}", response_model=AllianceRead)
async def update_alliance(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: AllianceUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_alliance(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_alliance(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_alliance(session, id, universe_id)
    if not ok:
        raise HTTPException(404)


@router.get("/{id}/members", response_model=CursorPage[MemberListItem])
async def list_alliance_members(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
):
    obj = await crud.get_alliance(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    items, next_cursor = await member_crud.list_members(
        session, universe_id, limit=limit, cursor=cursor, alliance_id=id
    )
    await member_crud.attach_primary_photos(session, items)
    return CursorPage(items=items, next_cursor=next_cursor, total=None)


@router.get("/{id}/incidents", response_model=CursorPage[IncidentListItem])
async def list_alliance_incidents(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
):
    obj = await crud.get_alliance(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    items = await incident_crud.list_incidents_by_alliance(session, id, universe_id, limit=limit)
    return CursorPage(items=items, next_cursor=None, total=None)
