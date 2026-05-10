import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole, SetStatus
from app.core.etag import check_etag, make_etag
from app.crud import gang_set as crud
from app.crud.media import attach_primary_photos_sets
from app.crud.gang_set import get_gang_set_by_slug
from app.core.csv_export import to_csv_response
from app.crud.incident import get_set_stats
from app.models.alliance import Alliance
from app.models.member import Member
from app.models.municipality import Municipality
from app.schemas.common import OffsetPage
from app.schemas.gang_set import (
    IncidentsPerYear,
    SetActivityEntry,
    SetCreate,
    SetListItem,
    SetPolygonItem,
    SetRead,
    SetReadDetail,
    SetReadDetailFull,
    SetRelatedSummary,
    SetRelationshipCreate,
    SetStats,
    SetTerritorySummary,
    SetUpdate,
)

router = APIRouter(prefix="/sets", tags=["sets"])


def _filter_id(value: str | None) -> uuid.UUID | Literal["none"] | None:
    """Parse a filter query param: missing/empty → None (no filter),
    'none' → match NULL, otherwise must be a UUID."""
    if value is None or value == "":
        return None
    if value == "none":
        return "none"
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid id filter: {value!r}")


def _to_list_item(obj) -> SetListItem:
    """Map an ORM GangSet (with transient _member_count/_*_name attrs) to SetListItem."""
    return SetListItem(
        id=obj.id,
        name=obj.name,
        slug=obj.slug,
        name_variants=obj.name_variants,
        status=obj.status,
        universe_id=obj.universe_id,
        alliance_id=obj.alliance_id,
        alliance_name=getattr(obj, "_alliance_name", None),
        gang_id=obj.gang_id,
        gang_name=getattr(obj, "_gang_name", None),
        municipality_id=obj.municipality_id,
        municipality_name=getattr(obj, "_municipality_name", None),
        member_count=getattr(obj, "_member_count", 0),
        is_reserved=obj.is_reserved,
        primary_photo_url=getattr(obj, "primary_photo_url", None),
        primary_photo_thumb_url=getattr(obj, "primary_photo_thumb_url", None),
    )


@router.get("/", response_model=OffsetPage[SetListItem])
async def list_sets(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    format: str = Query("json"),
    q: str | None = Query(None),
    status: SetStatus | None = Query(None),
    alliance_id: str | None = Query(None, description="UUID, 'none' for unassigned, or omit"),
    gang_id: str | None = Query(None, description="UUID, 'none' for unassigned, or omit"),
    municipality_id: str | None = Query(None, description="UUID, 'none' for unassigned, or omit"),
    sort: Literal["name", "status", "member_count", "updated_at", "created_at"] = Query("name"),
    order: Literal["asc", "desc"] = Query("asc"),
):
    filters = dict(
        q=q,
        status_filter=status,
        alliance_id=_filter_id(alliance_id),
        gang_id=_filter_id(gang_id),
        municipality_id=_filter_id(municipality_id),
        sort=sort,
        order=order,
    )
    if format == "csv":
        items, _total = await crud.list_gang_sets(
            session, universe_id, offset=0, limit=1000, **filters
        )
        return to_csv_response([_to_list_item(o) for o in items], "sets.csv")
    items, total = await crud.list_gang_sets(
        session, universe_id, offset=offset, limit=limit, **filters
    )
    return OffsetPage(items=[_to_list_item(o) for o in items], total=total)


@router.post("/", response_model=SetRead, status_code=201)
async def create_set(
    data: SetCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_gang_set(session, data, current_user.id)


@router.get("/territory-polygons", response_model=list[SetPolygonItem])
async def list_territory_polygons(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    municipality_id: uuid.UUID | None = Query(None),
):
    """Return every set in `universe_id` that has a drawn territory polygon.
    The territory map calls this once per universe (or per municipality drill-in)."""
    rows = await crud.list_set_polygons(session, universe_id, municipality_id)
    return [SetPolygonItem(**r) for r in rows]


@router.get("/search", response_model=list[SetListItem])
async def search_sets(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Backwards-compat shim. New callers should use GET /sets/?q= instead."""
    if len(q.strip()) < 2:
        return []
    items, _total = await crud.list_gang_sets(
        session, universe_id, offset=0, limit=200, q=q
    )
    return [_to_list_item(o) for o in items]


def _build_lede(
    *,
    member_count: int,
    dead_members: int,
    last_incident_year: int | None,
    top_ally: str | None,
    top_enemy: str | None,
) -> str:
    parts = [f"{member_count} member{'s' if member_count != 1 else ''}"]
    if dead_members:
        parts.append(f"{dead_members} dead")
    if last_incident_year:
        parts.append(f"last incident {last_incident_year}")
    if top_ally:
        parts.append(f"allied with {top_ally}")
    if top_enemy:
        parts.append(f"at war with {top_enemy}")
    return " · ".join(parts)


@router.get("/{id_or_slug}/detail", response_model=SetReadDetailFull)
async def get_set_detail(
    id_or_slug: str,
    universe_id: uuid.UUID,
    request: Request,
    response: Response,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Single denormalized payload for the set detail page.

    Bundles set core, territories, allies/enemies summaries, alliance/municipality/
    founder labels, stats, last-5-years incident sparkline data, and a one-line
    server-rendered lede. Honors If-None-Match for cheap back-navigation.
    """
    obj = None
    try:
        obj = await crud.get_gang_set(session, uuid.UUID(id_or_slug), universe_id)
    except ValueError:
        obj = await get_gang_set_by_slug(session, id_or_slug, universe_id)
    if obj is None:
        raise HTTPException(404)

    # ETag short-circuit before doing any expensive work.
    max_updated = await crud.get_set_max_updated_at(session, obj.id)
    etag = make_etag("set-detail", obj.id, obj.updated_at, max_updated)
    check_etag(request, response, etag)

    await attach_primary_photos_sets(session, [obj])

    territory_ids = await crud.list_set_territory_ids(session, obj.id)
    friend_ids, enemy_ids = await crud.list_set_relationships(session, obj.id, universe_id)
    territories_raw = await crud.list_set_territories_detail(session, obj.id)
    allies_raw, enemies_raw = await crud.list_set_relationships_detail(
        session, obj.id, universe_id
    )

    alliance_name = alliance_slug = None
    if obj.alliance_id:
        row = (await session.execute(
            select(Alliance.name, Alliance.slug).where(Alliance.id == obj.alliance_id)
        )).one_or_none()
        if row:
            alliance_name, alliance_slug = row

    municipality_name = None
    if obj.municipality_id:
        row = (await session.execute(
            select(Municipality.name).where(Municipality.id == obj.municipality_id)
        )).one_or_none()
        if row:
            municipality_name = row[0]

    founder_display_name = founder_slug = None
    if obj.founder_id:
        row = (await session.execute(
            select(Member.nickname, Member.legal_name, Member.nickname_unknown, Member.slug)
            .where(Member.id == obj.founder_id)
        )).one_or_none()
        if row:
            nickname, legal_name, nickname_unknown, m_slug = row
            if nickname_unknown or not nickname:
                founder_display_name = legal_name or "Unknown"
            else:
                founder_display_name = nickname
            founder_slug = m_slug

    stats_dict = await get_set_stats(session, obj.id)
    stats = SetStats(**stats_dict)

    # Sparkline: last 5 years inclusive of last_incident_year (or current span).
    from datetime import datetime as _dt
    end_year = stats.last_incident_year or _dt.utcnow().year
    incidents_per_year = await crud.list_set_incidents_per_year(
        session, obj.id, since_year=end_year - 4
    )

    top_ally = allies_raw[0]["name"] if allies_raw else None
    top_enemy = enemies_raw[0]["name"] if enemies_raw else None
    lede = _build_lede(
        member_count=stats.member_count,
        dead_members=stats.dead_members,
        last_incident_year=stats.last_incident_year,
        top_ally=top_ally,
        top_enemy=top_enemy,
    )

    base = SetRead.model_validate(obj).model_dump()
    base["primary_photo_url"] = getattr(obj, "primary_photo_url", None)
    base["primary_photo_thumb_url"] = getattr(obj, "primary_photo_thumb_url", None)

    return SetReadDetailFull(
        **base,
        territory_ids=territory_ids,
        friend_ids=friend_ids,
        enemy_ids=enemy_ids,
        alliance_name=alliance_name,
        alliance_slug=alliance_slug,
        municipality_name=municipality_name,
        municipality_slug=None,
        founder_display_name=founder_display_name,
        founder_slug=founder_slug,
        territories=[SetTerritorySummary(**t) for t in territories_raw],
        allies=[SetRelatedSummary(**a) for a in allies_raw],
        enemies=[SetRelatedSummary(**e) for e in enemies_raw],
        stats=stats,
        incidents_per_year=[IncidentsPerYear(**y) for y in incidents_per_year],
        lede=lede,
    )


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
    await attach_primary_photos_sets(session, [obj])
    base = SetRead.model_validate(obj).model_dump()
    base["primary_photo_url"] = getattr(obj, "primary_photo_url", None)
    base["primary_photo_thumb_url"] = getattr(obj, "primary_photo_thumb_url", None)
    return SetReadDetail(
        **base,
        territory_ids=territory_ids,
        friend_ids=friend_ids,
        enemy_ids=enemy_ids,
    )


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


@router.get("/{id}/activity", response_model=list[SetActivityEntry])
async def get_set_activity(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
):
    obj = await crud.get_gang_set(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    rows = await crud.list_set_activity(session, id, limit=limit)
    return [SetActivityEntry(**r) for r in rows]


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
