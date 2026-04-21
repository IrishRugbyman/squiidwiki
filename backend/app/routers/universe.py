import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_global_role
from app.core.database import get_session
from app.core.enums import GlobalRole
from app.crud import universe as crud
from app.schemas.common import OffsetPage
from app.schemas.universe import UniverseCreate, UniverseListItem, UniverseRead, UniverseUpdate


class UniverseAnalytics(BaseModel):
    total_members: int
    total_sets: int
    total_alliances: int
    total_incidents: int
    total_sources: int
    member_by_status: dict[str, int]
    incident_by_type: dict[str, int]
    top_sets_by_incidents: list[dict]
    top_sources_by_references: list[dict]
    incidents_by_month: list[dict]
    source_by_reliability: dict[str, int]
    top_members_by_incidents: list[dict]

router = APIRouter(prefix="/universes", tags=["universes"])


@router.get("/", response_model=OffsetPage[UniverseListItem])
async def list_universes(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = await crud.list_universes(session, offset=offset, limit=limit)
    return OffsetPage(items=items, total=total)


@router.post("/", response_model=UniverseRead, status_code=201)
async def create_universe(
    data: UniverseCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    return await crud.create_universe(session, data, current_user.id)


@router.get("/{id}", response_model=UniverseRead)
async def get_universe(
    id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    obj = await crud.get_universe(session, id)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.patch("/{id}", response_model=UniverseRead)
async def update_universe(
    id: uuid.UUID,
    data: UniverseUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    __: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    obj = await crud.update_universe(session, id, data)
    if obj is None:
        raise HTTPException(404)
    return obj


@router.delete("/{id}", status_code=204)
async def delete_universe(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, require_global_role(GlobalRole.ADMIN)],
):
    ok = await crud.delete_universe(session, id)
    if not ok:
        raise HTTPException(404)


@router.get("/{id}/analytics", response_model=UniverseAnalytics)
async def get_universe_analytics(
    id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UniverseAnalytics:
    uid = str(id)

    totals = (await session.execute(text("""
        SELECT
            (SELECT count(*) FROM member WHERE universe_id = :uid) AS members,
            (SELECT count(*) FROM sets WHERE universe_id = :uid) AS sets,
            (SELECT count(*) FROM alliance WHERE universe_id = :uid) AS alliances,
            (SELECT count(*) FROM incident WHERE universe_id = :uid) AS incidents,
            (SELECT count(*) FROM source WHERE universe_id = :uid) AS sources
    """), {"uid": uid})).one()

    status_rows = (await session.execute(text(
        "SELECT status, count(*) AS cnt FROM member WHERE universe_id = :uid GROUP BY status"
    ), {"uid": uid})).fetchall()

    type_rows = (await session.execute(text(
        "SELECT type, count(*) AS cnt FROM incident WHERE universe_id = :uid GROUP BY type"
    ), {"uid": uid})).fetchall()

    top_sets_rows = (await session.execute(text("""
        SELECT s.id, s.name, count(DISTINCT ip.incident_id) AS incident_count
        FROM sets s
        JOIN member m ON m.set_id = s.id
        JOIN incident_participant ip ON ip.member_id = m.id
        JOIN incident i ON i.id = ip.incident_id AND i.universe_id = :uid
        WHERE s.universe_id = :uid
        GROUP BY s.id, s.name
        ORDER BY incident_count DESC
        LIMIT 5
    """), {"uid": uid})).fetchall()

    top_sources_rows = (await session.execute(text("""
        SELECT src.id, src.title,
            (SELECT count(*) FROM incident_source WHERE source_id = src.id) +
            (SELECT count(*) FROM member_source WHERE source_id = src.id) AS ref_count
        FROM source src
        WHERE src.universe_id = :uid
        ORDER BY ref_count DESC
        LIMIT 5
    """), {"uid": uid})).fetchall()

    month_rows = (await session.execute(text("""
        SELECT TO_CHAR(DATE_TRUNC('month', sortable_date), 'YYYY-MM') AS month, count(*) AS cnt
        FROM incident
        WHERE universe_id = :uid AND sortable_date IS NOT NULL
        GROUP BY month
        ORDER BY month
    """), {"uid": uid})).fetchall()

    reliability_rows = (await session.execute(text(
        "SELECT reliability, count(*) AS cnt FROM source WHERE universe_id = :uid GROUP BY reliability"
    ), {"uid": uid})).fetchall()

    top_members_rows = (await session.execute(text("""
        SELECT m.id,
            CASE WHEN m.nickname_unknown OR m.nickname IS NULL THEN m.legal_name ELSE m.nickname END AS display_name,
            count(DISTINCT ip.incident_id) AS incident_count
        FROM member m
        JOIN incident_participant ip ON ip.member_id = m.id
        JOIN incident i ON i.id = ip.incident_id AND i.universe_id = :uid
        WHERE m.universe_id = :uid
        GROUP BY m.id, display_name
        ORDER BY incident_count DESC
        LIMIT 5
    """), {"uid": uid})).fetchall()

    return UniverseAnalytics(
        total_members=totals.members,
        total_sets=totals.sets,
        total_incidents=totals.incidents,
        total_alliances=totals.alliances,
        total_sources=totals.sources,
        member_by_status={r.status: r.cnt for r in status_rows},
        incident_by_type={r.type: r.cnt for r in type_rows},
        top_sets_by_incidents=[
            {"id": str(r.id), "name": r.name, "incident_count": r.incident_count}
            for r in top_sets_rows
        ],
        top_sources_by_references=[
            {"id": str(r.id), "title": r.title, "ref_count": r.ref_count}
            for r in top_sources_rows
        ],
        incidents_by_month=[{"month": r.month, "count": r.cnt} for r in month_rows],
        source_by_reliability={r.reliability: r.cnt for r in reliability_rows},
        top_members_by_incidents=[
            {"id": str(r.id), "display_name": r.display_name or "Unknown", "incident_count": r.incident_count}
            for r in top_members_rows
        ],
    )
