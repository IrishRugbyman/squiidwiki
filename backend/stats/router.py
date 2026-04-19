from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.base_class import get_db
from backend.stats import service
from backend.stats.refresh import refresh_materialized_views

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/members", response_model=List[Any])
async def member_stats(
    universe_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await service.get_member_stats(db, universe_id=universe_id)


@router.get("/sets", response_model=List[Any])
async def set_stats(
    universe_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await service.get_set_stats(db, universe_id=universe_id)


@router.post("/refresh", status_code=204)
async def manual_refresh():
    """Admin endpoint: force-refresh both materialized views immediately."""
    await refresh_materialized_views()
