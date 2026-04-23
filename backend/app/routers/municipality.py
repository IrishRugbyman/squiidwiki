import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import municipality as crud
from app.schemas.common import OffsetPage
from app.schemas.municipality import (
    MunicipalityCreate,
    MunicipalityListItem,
    MunicipalityRead,
    MunicipalityUpdate,
)

router = APIRouter(prefix="/municipalities", tags=["municipalities"])


@router.get("/", response_model=OffsetPage[MunicipalityListItem])
async def list_municipalities(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    items, total = await crud.list_municipalities(session, universe_id, offset=offset, limit=limit)
    return OffsetPage(items=items, total=total)


@router.get("/geojson")
async def get_municipalities_geojson(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Any:
    return await crud.get_municipality_geojson(session, universe_id)


@router.post("/", response_model=MunicipalityRead, status_code=201)
async def create_municipality(
    data: MunicipalityCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.create_municipality(session, data, current_user.id)
    return await crud.get_municipality(session, obj.id, obj.universe_id)


@router.get("/search", response_model=list[MunicipalityListItem])
async def search_municipalities(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.search_municipalities(session, universe_id, q)


@router.get("/{id}", response_model=MunicipalityRead)
async def get_municipality(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_municipality(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.patch("/{id}", response_model=MunicipalityRead)
async def update_municipality(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: MunicipalityUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_municipality(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_municipality(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_municipality(session, id, universe_id)
    if not ok:
        raise HTTPException(404)
