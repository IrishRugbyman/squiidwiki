import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import gang_set as crud
from app.crud.media import attach_primary_photos_sets
from app.crud.gang_set import get_gang_set_by_slug
from app.core.csv_export import to_csv_response
from app.crud.incident import get_set_stats
from app.schemas.common import OffsetPage
from app.schemas.gang_set import (
    SetCreate,
    SetListItem,
    SetRead,
    SetReadDetail,
    SetRelationshipCreate,
    SetStats,
    SetUpdate,
)

router = APIRouter(prefix="/sets", tags=["sets"])


@router.get("/", response_model=OffsetPage[SetListItem])
async def list_sets(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    format: str = Query("json"),
):
    if format == "csv":
        items, _ = await crud.list_gang_sets(session, universe_id, offset=0, limit=1000)
        return to_csv_response(items, "sets.csv")
    items, total = await crud.list_gang_sets(session, universe_id, offset=offset, limit=limit)
    await attach_primary_photos_sets(session, items)
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=SetRead, status_code=201)
async def create_set(
    data: SetCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_gang_set(session, data, current_user.id)


@router.get("/search", response_model=list[SetListItem])
async def search_sets(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    items = await crud.search_gang_sets(session, universe_id, q)
    await attach_primary_photos_sets(session, items)
    return items


@router.get("/{id_or_slug}", response_model=SetReadDetail)
async def get_set(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = None
    try:
        obj = await crud.get_gang_set(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await get_gang_set_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    territory_ids = await crud.list_set_territory_ids(session, obj.id)
    friend_ids, enemy_ids = await crud.list_set_relationships(session, obj.id, universe_id)
    base = SetRead.model_validate(obj)
    return SetReadDetail(**base.model_dump(), territory_ids=territory_ids, friend_ids=friend_ids, enemy_ids=enemy_ids)


@router.patch("/{id}", response_model=SetRead)
async def update_set(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: SetUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_gang_set(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_set(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_gang_set(session, id, universe_id)
    if not ok:
        raise HTTPException(404)


@router.post("/{id}/relationships", response_model=SetReadDetail)
async def add_relationship(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: SetRelationshipCreate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_gang_set(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    await crud.add_set_relationship(session, id, data.target_id, data.type, universe_id)
    territory_ids = await crud.list_set_territory_ids(session, id)
    friend_ids, enemy_ids = await crud.list_set_relationships(session, id, universe_id)
    base = SetRead.model_validate(obj)
    return SetReadDetail(**base.model_dump(), territory_ids=territory_ids, friend_ids=friend_ids, enemy_ids=enemy_ids)


@router.delete("/{id}/relationships/{target_id}", status_code=204)
async def remove_relationship(
    id: uuid.UUID,
    target_id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ok = await crud.remove_set_relationship(session, id, target_id, universe_id)
    if not ok:
        raise HTTPException(404)


@router.get("/{id}/stats", response_model=SetStats)
async def get_set_stats_endpoint(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_gang_set(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    stats = await get_set_stats(session, id)
    return SetStats(**stats)
