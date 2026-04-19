import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import alliance as crud
from app.schemas.alliance import (
    AllianceCreate,
    AllianceListItem,
    AllianceRead,
    AllianceReadDetail,
    AllianceUpdate,
)
from app.schemas.common import OffsetPage

router = APIRouter(prefix="/alliances", tags=["alliances"])


@router.get("/", response_model=OffsetPage[AllianceListItem])
async def list_alliances(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = await crud.list_alliances(session, universe_id, offset=offset, limit=limit)
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
    return await crud.search_alliances(session, universe_id, q)


@router.get("/{id}", response_model=AllianceReadDetail)
async def get_alliance(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_alliance(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    territory_ids = await crud.list_alliance_territory_ids(session, id)
    set_ids = await crud.list_alliance_set_ids(session, id)
    return AllianceReadDetail.model_validate(obj).model_copy(
        update={"territory_ids": territory_ids, "set_ids": set_ids}
    )


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
