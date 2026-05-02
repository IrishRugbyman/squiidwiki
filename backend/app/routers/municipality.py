import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_prod_session, get_session, resolve_prod_universe
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

# Municipalities are geographic reference data shared across all DB modes.
# Every endpoint reads/writes against the prod DB, resolving the active-DB
# universe id to its prod-DB equivalent by slug.


async def _prod_uid(
    universe_id: uuid.UUID,
    active_session: AsyncSession,
    prod_session: AsyncSession,
) -> uuid.UUID:
    uid = await resolve_prod_universe(active_session, prod_session, universe_id)
    if uid is None:
        raise HTTPException(404, f"Universe {universe_id} not found in prod DB")
    return uid


@router.get("/", response_model=OffsetPage[MunicipalityListItem])
async def list_municipalities(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    prod_uid = await _prod_uid(universe_id, session, prod_session)
    items, total = await crud.list_municipalities(prod_session, prod_uid, offset=offset, limit=limit)
    return OffsetPage(items=items, total=total)


@router.get("/geojson")
async def get_municipalities_geojson(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
    parent_id: str | None = Query(
        None,
        description=(
            "Filter mode. Omitted = all municipalities with geometry. "
            "'top' = only top-level (parent_id IS NULL). "
            "A UUID = only children of that municipality."
        ),
    ),
) -> Any:
    uid = await resolve_prod_universe(session, prod_session, universe_id)
    if uid is None:
        return {"type": "FeatureCollection", "features": []}

    parent_filter: str | uuid.UUID | None
    if parent_id is None:
        parent_filter = None
    elif parent_id == "top":
        parent_filter = "top"
    else:
        try:
            parent_filter = uuid.UUID(parent_id)
        except ValueError:
            raise HTTPException(400, "parent_id must be 'top', a UUID, or omitted")

    return await crud.get_municipality_geojson(prod_session, uid, parent_filter=parent_filter)


@router.post("/", response_model=MunicipalityRead, status_code=201)
async def create_municipality(
    data: MunicipalityCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
):
    prod_uid = await _prod_uid(data.universe_id, session, prod_session)
    data.universe_id = prod_uid
    obj = await crud.create_municipality(prod_session, data, current_user.id)
    return await crud.get_municipality(prod_session, obj.id, obj.universe_id)


@router.get("/search", response_model=list[MunicipalityListItem])
async def search_municipalities(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
):
    if len(q.strip()) < 2:
        return []
    prod_uid = await _prod_uid(universe_id, session, prod_session)
    return await crud.search_municipalities(prod_session, prod_uid, q)


@router.get("/{id}", response_model=MunicipalityRead)
async def get_municipality(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
):
    prod_uid = await _prod_uid(universe_id, session, prod_session)
    obj = await crud.get_municipality(prod_session, id, prod_uid)
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
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
):
    prod_uid = await _prod_uid(universe_id, session, prod_session)
    obj = await crud.update_municipality(prod_session, id, prod_uid, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_municipality(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    prod_session: Annotated[AsyncSession, Depends(get_prod_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    prod_uid = await _prod_uid(universe_id, session, prod_session)
    ok = await crud.delete_municipality(prod_session, id, prod_uid)
    if not ok:
        raise HTTPException(404)
