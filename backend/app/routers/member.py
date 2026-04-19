import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import member as crud
from app.schemas.common import CursorPage
from app.schemas.member import (
    MemberCreate,
    MemberListItem,
    MemberRead,
    MemberReadDetail,
    MemberStats,
    MemberUpdate,
)

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/", response_model=CursorPage[MemberListItem])
async def list_members(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
):
    items, next_cursor = await crud.list_members(session, universe_id, limit=limit, cursor=cursor)
    return CursorPage(items=items, next_cursor=next_cursor, total=None)


@router.post("/", response_model=MemberRead, status_code=201)
async def create_member(
    data: MemberCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_member(session, data, current_user.id)


@router.get("/search", response_model=list[MemberListItem])
async def search_members(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.search_members(session, universe_id, q)


@router.get("/{id}", response_model=MemberReadDetail)
async def get_member(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    source_ids = await crud.list_member_source_ids(session, id)
    return MemberReadDetail.model_validate(obj).model_copy(update={"source_ids": source_ids})


@router.patch("/{id}", response_model=MemberRead)
async def update_member(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: MemberUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_member(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_member(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_member(session, id, universe_id)
    if not ok:
        raise HTTPException(404)


@router.get("/{id}/stats", response_model=MemberStats)
async def get_member_stats(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    stats = await crud.get_member_stats(session, id)
    return MemberStats(**stats)
