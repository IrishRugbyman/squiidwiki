import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import universe as crud
from app.schemas.common import OffsetPage
from app.schemas.universe import UniverseCreate, UniverseListItem, UniverseRead, UniverseUpdate

router = APIRouter(prefix="/universes", tags=["universes"])


@router.get("/", response_model=OffsetPage[UniverseListItem])
async def list_universes(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = await crud.list_universes(session, offset=offset, limit=limit)
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=UniverseRead, status_code=201)
async def create_universe(
    data: UniverseCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    return await crud.create_universe(session, data, current_user.id)


@router.get("/{id}", response_model=UniverseRead)
async def get_universe(
    id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_universe(session, id)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.patch("/{id}", response_model=UniverseRead)
async def update_universe(
    id: uuid.UUID,
    data: UniverseUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    __: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    obj = await crud.update_universe(session, id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_universe(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_universe(session, id)
    if not ok:
        raise HTTPException(404)
