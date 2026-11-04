import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole, RapGroupKind, RapGroupStatus
from app.crud import citation as citation_crud
from app.crud import rap_group as crud
from app.schemas.common import OffsetPage
from app.schemas.rap_group import (
    RapGroupCreate,
    RapGroupListItem,
    RapGroupRead,
    RapGroupReadDetail,
    RapGroupUpdate,
)

router = APIRouter(prefix="/rap-groups", tags=["rap-groups"])


@router.get("/", response_model=OffsetPage[RapGroupListItem])
async def list_rap_groups(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    q: str | None = None,
    status: RapGroupStatus | None = None,
    kind: RapGroupKind | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
):
    groups, total = await crud.list_rap_groups(
        session, universe_id, q=q, status=status, kind=kind, offset=offset, limit=limit
    )
    return OffsetPage(items=await crud.to_list_items(session, groups), total=total)


@router.post("/", response_model=RapGroupRead, status_code=201)
async def create_rap_group(
    data: RapGroupCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_rap_group(session, data, current_user.id)


@router.get("/{id_or_slug}", response_model=RapGroupReadDetail)
async def get_rap_group(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        obj = await crud.get_rap_group(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await crud.get_rap_group_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    (item,) = await crud.to_list_items(session, [obj])
    return RapGroupReadDetail(
        **item.model_dump(),
        bio=obj.bio,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        citations=await citation_crud.list_citations(session, "rap_group", obj.id),
        **await crud.detail_extras(session, obj),
    )


@router.patch("/{id}", response_model=RapGroupRead)
async def update_rap_group(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: RapGroupUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_rap_group(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_rap_group(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    if not await crud.delete_rap_group(session, id, universe_id):
        raise HTTPException(404)
