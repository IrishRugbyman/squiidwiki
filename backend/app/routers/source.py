import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import source as crud
from app.schemas.common import OffsetPage
from app.schemas.source import SourceCreate, SourceListItem, SourceRead, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/", response_model=OffsetPage[SourceListItem])
async def list_sources(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
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
