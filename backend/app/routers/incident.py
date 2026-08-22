import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.csv_export import to_csv_response
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import incident as crud
from app.models.incident import IncidentParticipant
from app.models.member import Member
from app.models.municipality import Municipality
from app.schemas.common import CursorPage
from app.schemas.incident import (
    IncidentCreate,
    IncidentListItem,
    IncidentRead,
    IncidentReadDetail,
    IncidentUpdate,
    ParticipantRead,
    SetParticipantRead,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


async def _enrich_participant_names(
    session: AsyncSession, items: list, viewer_id: uuid.UUID | None = None
) -> list:
    if not items:
        return items
    incident_ids = [inc.id for inc in items]
    ip = IncidentParticipant.__table__
    m = Member.__table__
    display_name_expr = case(
        (m.c.nickname_unknown | m.c.nickname.is_(None), m.c.legal_name),
        else_=m.c.nickname,
    )
    rows = (
        await session.execute(
            select(ip.c.incident_id, ip.c.role, display_name_expr.label("display_name"))
            .join(m, m.c.id == ip.c.member_id)
            .where(ip.c.incident_id.in_(incident_ids))
            .where(ip.c.role.in_(("VICTIM", "SHOOTER")))
        )
    ).fetchall()
    victim_map: dict[str, list[str]] = {}
    shooter_map: dict[str, list[str]] = {}
    for incident_id, role, name in rows:
        key = str(incident_id)
        if role == "VICTIM":
            victim_map.setdefault(key, []).append(name)
        else:
            shooter_map.setdefault(key, []).append(name)

    # What the member being viewed did in each of these incidents. Fetched
    # separately because the query above keeps only VICTIM and SHOOTER, and an
    # assist is exactly the case the page was misreporting.
    viewer_map: dict[str, tuple] = {}
    if viewer_id is not None:
        viewer_rows = (
            await session.execute(
                select(ip.c.incident_id, ip.c.role, ip.c.outcome)
                .where(ip.c.incident_id.in_(incident_ids))
                .where(ip.c.member_id == viewer_id)
            )
        ).fetchall()
        viewer_map = {str(r[0]): (r[1], r[2]) for r in viewer_rows}
    # Single batched join for municipality names so the frontend doesn't have
    # to fetch the entire municipalities table just to label rows.
    muni_ids = {inc.municipality_id for inc in items if inc.municipality_id}
    muni_names: dict[uuid.UUID, str] = {}
    if muni_ids:
        muni_rows = (
            await session.execute(
                select(Municipality.id, Municipality.name).where(Municipality.id.in_(muni_ids))
            )
        ).all()
        muni_names = {r[0]: r[1] for r in muni_rows}

    enriched = []
    for inc in items:
        d = IncidentListItem.model_validate(inc)
        key = str(inc.id)
        d.victim_names = victim_map.get(key, [])
        d.shooter_names = shooter_map.get(key, [])
        if key in viewer_map:
            d.viewer_role, d.viewer_outcome = viewer_map[key]
        if inc.municipality_id:
            d.municipality_name = muni_names.get(inc.municipality_id)
        enriched.append(d)
    return enriched


@router.get("/", response_model=CursorPage[IncidentListItem])
async def list_incidents(
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=500),
    cursor: str | None = None,
    set_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    municipality_id: uuid.UUID | None = None,
    with_coords: bool = Query(False, description="Only incidents carrying lat/lng, for maps."),
    format: str = Query("json"),
):
    if with_coords:
        items = await crud.list_incidents_with_coords(session, universe_id)
        return CursorPage(
            items=await _enrich_participant_names(session, items),
            next_cursor=None,
            total=len(items),
        )
    if format == "csv":
        items, _ = await crud.list_incidents(session, universe_id, limit=1000)
        return to_csv_response(items, "incidents.csv")
    if set_id is not None:
        items = await crud.list_incidents_by_set(session, set_id, universe_id, limit=limit)
        return CursorPage(
            items=await _enrich_participant_names(session, items), next_cursor=None, total=None
        )
    if member_id is not None:
        items = await crud.list_incidents_by_member(session, member_id, universe_id, limit=limit)
        return CursorPage(
            items=await _enrich_participant_names(session, items, viewer_id=member_id),
            next_cursor=None,
            total=None,
        )
    if municipality_id is not None:
        items = await crud.list_incidents_by_municipality(
            session, municipality_id, universe_id, limit=limit
        )
        return CursorPage(
            items=await _enrich_participant_names(session, items), next_cursor=None, total=None
        )
    items, next_cursor = await crud.list_incidents(session, universe_id, limit=limit, cursor=cursor)
    return CursorPage(
        items=await _enrich_participant_names(session, items), next_cursor=next_cursor, total=None
    )


@router.post("/", response_model=IncidentRead, status_code=201)
async def create_incident(
    data: IncidentCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await crud.create_incident(session, data, current_user.id)


@router.get("/search", response_model=list[IncidentListItem])
async def search_incidents(
    universe_id: uuid.UUID,
    q: str,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if len(q.strip()) < 2:
        return []
    return await crud.search_incidents(session, universe_id, q)


@router.get("/{id}", response_model=IncidentReadDetail)
async def get_incident(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_incident(session, id, universe_id)
    if obj is None:
        raise HTTPException(404)
    participants = await crud.list_incident_participants(session, id)
    set_participants = await crud.list_incident_set_participants(session, id)
    source_ids = await crud.list_incident_source_ids(session, id)
    members = await crud.participant_member_briefs(session, [p.member_id for p in participants])
    sets = await crud.participant_set_briefs(session, [p.set_id for p in set_participants])
    participant_reads = []
    for p in participants:
        pr = ParticipantRead.model_validate(p)
        if m := members.get(p.member_id):
            pr.member_name = m.display_name
            pr.member_slug = m.slug
        participant_reads.append(pr)
    set_participant_reads = []
    for p in set_participants:
        sr = SetParticipantRead.model_validate(p)
        if s := sets.get(p.set_id):
            sr.set_name = s.name
            sr.set_slug = s.slug
        set_participant_reads.append(sr)
    base = IncidentRead.model_validate(obj)
    return IncidentReadDetail(
        **base.model_dump(),
        participants=participant_reads,
        set_participants=set_participant_reads,
        source_ids=source_ids,
    )


@router.patch("/{id}", response_model=IncidentRead)
async def update_incident(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    data: IncidentUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.update_incident(session, id, universe_id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_incident(
    id: uuid.UUID,
    universe_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_incident(session, id, universe_id)
    if not ok:
        raise HTTPException(404)
