import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import gang as crud
from app.schemas.common import OffsetPage
from app.schemas.gang import (
    GangCreate,
    GangDetail,
    GangListItem,
    GangRead,
    GangUpdate,
)

router = APIRouter(prefix="/gangs", tags=["gangs"])


@router.get("/", response_model=OffsetPage[GangListItem])
async def list_gangs(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    items, total = await crud.list_gangs(session, universe_id, offset=offset, limit=limit)
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=GangRead, status_code=201)
async def create_gang(
    data: GangCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    obj = await crud.create_gang(session, data, current_user.id)
    await crud.attach_gang_counts(session, obj.universe_id, [obj])
    return obj


@router.get("/{id_or_slug}/detail", response_model=GangDetail)
async def get_gang_detail(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """The gang page in one round trip: the card, its lineage and branches,
    the sets claiming it and the alliances tagged with it."""
    obj = None
    try:
        obj = await crud.get_gang(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await crud.get_gang_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    extra = await crud.get_gang_detail(session, obj)
    base = GangListItem.model_validate(obj).model_dump()
    return GangDetail(
        **base,
        parent=extra["parent"],
        ancestors=extra["ancestors"],
        branches=[GangListItem.model_validate(b) for b in extra["branches"]],
        sets=extra["sets"],
        alliances=extra["alliances"],
    )


@router.get("/{id_or_slug}", response_model=GangRead)
async def get_gang(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = None
    try:
        obj = await crud.get_gang(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await crud.get_gang_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    await crud.attach_gang_counts(session, universe_id, [obj])
    return obj


@router.patch("/{id}", response_model=GangRead)
async def update_gang(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: GangUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    obj = await crud.update_gang(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    await crud.attach_gang_counts(session, universe_id, [obj])
    return obj


@router.delete("/{id}", status_code=204)
async def delete_gang(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_gang(session, id, universe_id)
    if not ok:
        raise HTTPException(404)


@router.get("/{id}/usage")
async def gang_usage(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_gang(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return await crud.gang_usage_counts(session, id)
