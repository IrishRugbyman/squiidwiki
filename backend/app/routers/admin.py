import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_global_role
from app.core.database import DbMode, get_db_mode, get_session, set_db_mode
from app.core.enums import GlobalRole
from app.crud import anomalies as anomaly_checks
from app.models.universe import Universe

router = APIRouter(prefix="/admin", tags=["admin"])

_admin = require_global_role(GlobalRole.ADMIN)


class DbModeResponse(BaseModel):
    mode: DbMode


@router.get("/db-mode", response_model=DbModeResponse)
async def read_db_mode(_: Annotated[None, _admin]) -> DbModeResponse:
    return DbModeResponse(mode=get_db_mode())


@router.post("/db-mode", response_model=DbModeResponse)
async def write_db_mode(mode: DbMode, _: Annotated[None, _admin]) -> DbModeResponse:
    set_db_mode(mode)
    return DbModeResponse(mode=get_db_mode())


class AnomalyRead(BaseModel):
    kind: str
    entity_type: str
    entity_id: uuid.UUID
    slug: str | None
    display_name: str
    message: str
    related_type: str | None = None
    related_id: uuid.UUID | None = None
    related_label: str | None = None


class AnomalyCheckRead(BaseModel):
    kind: str
    title: str
    count: int


class AnomalyReport(BaseModel):
    universe_id: uuid.UUID
    checks: list[AnomalyCheckRead]
    items: list[AnomalyRead]


@router.get("/anomalies", response_model=AnomalyReport)
async def list_anomalies(
    universe_id: uuid.UUID,
    _: Annotated[None, _admin],
    session: Annotated[AsyncSession, Depends(get_session)],
    kind: Annotated[list[str] | None, Query()] = None,
) -> AnomalyReport:
    """Rows in one universe that contradict each other (see app/crud/anomalies.py).

    `kind` (repeatable) limits the run to those checks; unknown kinds are a 422
    so a typo in a CLI call is not read as "no findings".
    """
    if await session.get(Universe, universe_id) is None:
        raise HTTPException(status_code=404, detail="universe not found")
    if kind:
        unknown = sorted(set(kind) - set(anomaly_checks.CHECKS))
        if unknown:
            raise HTTPException(status_code=422, detail=f"unknown check kind: {', '.join(unknown)}")
    wanted = set(kind) if kind else None
    data = await anomaly_checks.load_universe_data(session, universe_id)
    found = anomaly_checks.run_checks(data, wanted)
    counts: dict[str, int] = {}
    for a in found:
        counts[a.kind] = counts.get(a.kind, 0) + 1
    checks = [
        AnomalyCheckRead(kind=k, title=t, count=counts.get(k, 0))
        for k, t in anomaly_checks.CHECKS.items()
        if wanted is None or k in wanted
    ]
    return AnomalyReport(
        universe_id=universe_id,
        checks=checks,
        items=[AnomalyRead(**a.__dict__) for a in found],
    )
