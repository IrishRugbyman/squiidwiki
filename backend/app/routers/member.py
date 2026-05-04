import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole, MemberStatus
from app.core.csv_export import to_csv_response
from app.crud import member as crud
from app.schemas.common import CursorPage
from app.schemas.member import (
    MemberAliasCreate,
    MemberAliasRead,
    MemberCreate,
    MemberIncarcerationCreate,
    MemberIncarcerationRead,
    MemberIncarcerationUpdate,
    MemberListItem,
    MemberRead,
    MemberReadDetail,
    MemberReleaseEvent,
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
    set_id: uuid.UUID | None = None,
    alliance_id: uuid.UUID | None = None,
    format: str = Query("json"),
):
    if format == "csv":
        items, _ = await crud.list_members(session, universe_id, limit=1000)
        return to_csv_response(items, "members.csv")
    items, next_cursor = await crud.list_members(
        session, universe_id, limit=limit, cursor=cursor, set_id=set_id, alliance_id=alliance_id
    )
    await crud.attach_primary_photos(session, items)
    return CursorPage(items=items, next_cursor=next_cursor, total=None)


@router.post("/", response_model=MemberRead, status_code=201)
async def create_member(
    data: MemberCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.create_member(session, data, current_user.id)
    await crud.attach_primary_photos(session, [obj])
    return obj


@router.post("/bulk-status", response_model=dict)
async def bulk_update_status(
    universe_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    member_ids: list[uuid.UUID] = Body(...),
    status: MemberStatus = Body(...),
):
    count = await crud.bulk_update_member_status(session, universe_id, member_ids, status)
    return {"updated": count}


@router.get("/search", response_model=list[MemberListItem])
async def search_members(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    items = await crud.search_members(session, universe_id, q)
    await crud.attach_primary_photos(session, items)
    return items


@router.get("/release-events", response_model=list[MemberReleaseEvent])
async def list_universe_release_events(
    universe_id: uuid.UUID,
    year: int,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.list_universe_release_events(session, universe_id, year)


@router.get("/{id_or_slug}", response_model=MemberReadDetail)
async def get_member(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = None
    try:
        obj = await crud.get_member(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await crud.get_member_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    await crud.attach_primary_photos(session, [obj])
    source_ids = await crud.list_member_source_ids(session, obj.id)
    base = MemberRead.model_validate(obj)
    return MemberReadDetail(**base.model_dump(), source_ids=source_ids)


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
    await crud.attach_primary_photos(session, [obj])
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


@router.get("/{id}/aliases", response_model=list[MemberAliasRead])
async def list_member_aliases(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return await crud.list_member_aliases(session, id)


@router.post("/{id}/aliases", response_model=MemberAliasRead, status_code=201)
async def create_member_alias(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: MemberAliasCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return await crud.create_member_alias(session, id, data)


@router.delete("/{id}/aliases/{alias_id}", status_code=204)
async def delete_member_alias(
    id: uuid.UUID,
    alias_id: uuid.UUID,
    universe_id: uuid.UUID,
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ok = await crud.delete_member_alias(session, alias_id, id)
    if not ok:
        raise HTTPException(404)


@router.get("/{id}/incarcerations", response_model=list[MemberIncarcerationRead])
async def list_member_incarcerations(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return await crud.list_member_incarcerations(session, id)


@router.post("/{id}/incarcerations", response_model=MemberIncarcerationRead, status_code=201)
async def create_member_incarceration(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: MemberIncarcerationCreate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    return await crud.create_member_incarceration(session, id, data)


@router.patch("/{id}/incarcerations/{spell_id}", response_model=MemberIncarcerationRead)
async def update_member_incarceration(
    id: uuid.UUID,
    spell_id: uuid.UUID,
    universe_id: uuid.UUID,
    data: MemberIncarcerationUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    result = await crud.update_member_incarceration(session, spell_id, id, data)
    if result is None:
        raise HTTPException(404)
    return result


@router.delete("/{id}/incarcerations/{spell_id}", status_code=204)
async def delete_member_incarceration(
    id: uuid.UUID,
    spell_id: uuid.UUID,
    universe_id: uuid.UUID,
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_member(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    ok = await crud.delete_member_incarceration(session, spell_id, id)
    if not ok:
        raise HTTPException(404)
