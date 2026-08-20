import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.csv_export import to_csv_response
from app.core.database import get_session
from app.core.enums import BusinessStatus, BusinessType, GlobalRole
from app.crud import business as crud
from app.crud.municipality import get_municipality
from app.schemas.business import (
    BusinessCreate,
    BusinessListItem,
    BusinessRead,
    BusinessReadDetail,
    BusinessUpdate,
)
from app.schemas.common import OffsetPage

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("/", response_model=OffsetPage[BusinessListItem])
async def list_businesses(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    business_type: BusinessType | None = None,
    status: BusinessStatus | None = None,
    municipality_id: uuid.UUID | None = None,
    set_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    format: str = Query("json"),
):
    if format == "csv":
        items, _ = await crud.list_businesses(session, universe_id, offset=0, limit=1000)
        return to_csv_response(items, "businesses.csv")
    items, total = await crud.list_businesses(
        session,
        universe_id,
        offset=offset,
        limit=limit,
        business_type=business_type,
        status=status,
        municipality_id=municipality_id,
        set_id=set_id,
        member_id=member_id,
    )
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=BusinessRead, status_code=201)
async def create_business(
    data: BusinessCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_business(session, data, current_user.id)


@router.get("/search", response_model=list[BusinessListItem])
async def search_businesses(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    return await crud.search_businesses(session, universe_id, q)


@router.get("/{id_or_slug}", response_model=BusinessReadDetail)
async def get_business(
    id_or_slug: str,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = None
    try:
        obj = await crud.get_business(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await crud.get_business_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)
    members = await crud.list_business_members(session, obj.id)
    set_ids = await crud.list_business_set_ids(session, obj.id)
    source_ids = await crud.list_business_source_ids(session, obj.id)
    municipality_name = None
    if obj.municipality_id:
        muni = await get_municipality(session, obj.municipality_id, universe_id)
        if muni:
            municipality_name = muni["name"]
    base = BusinessRead.model_validate(obj).model_dump()
    return BusinessReadDetail(
        **base,
        municipality_name=municipality_name,
        members=members,
        set_ids=set_ids,
        source_ids=source_ids,
    )


@router.patch("/{id}", response_model=BusinessRead)
async def update_business(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: BusinessUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_business(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_business(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_business(session, id, universe_id)
    if not ok:
        raise HTTPException(404)
