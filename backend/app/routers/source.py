import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.core.csv_export import to_csv_response
from app.crud import source as crud
from app.crud import member as member_crud
from app.crud import incident as incident_crud
from app.schemas.common import CursorPage, OffsetPage
from app.schemas.incident import IncidentListItem
from app.schemas.member import MemberListItem
from app.schemas.source import SourceCreate, SourceListItem, SourceRead, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/", response_model=OffsetPage[SourceListItem])
async def list_sources(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    format: str = Query("json"),
):
    if format == "csv":
        items, _ = await crud.list_sources(session, universe_id, offset=0, limit=1000)
        return to_csv_response(items, "sources.csv")
    items, total = await crud.list_sources(session, universe_id, offset=offset, limit=limit)
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(
    data: SourceCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_source(session, data, current_user.id)


@router.get("/search", response_model=list[SourceListItem])
async def search_sources(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    return await crud.search_sources(session, universe_id, q)


@router.get("/{id}", response_model=SourceRead)
async def get_source(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_source(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.patch("/{id}", response_model=SourceRead)
async def update_source(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: SourceUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_source(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_source(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_source(session, id, universe_id)
    if not ok:
        raise HTTPException(404)


@router.get("/{id}/incidents", response_model=CursorPage[IncidentListItem])
async def list_source_incidents(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_source(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    items = await incident_crud.list_incidents_by_source(session, id, universe_id)
    return CursorPage(items=items, next_cursor=None, total=None)


@router.get("/{id}/members", response_model=CursorPage[MemberListItem])
async def list_source_members(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_source(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    items = await member_crud.list_members_by_source(session, id, universe_id)
    return CursorPage(items=items, next_cursor=None, total=None)
