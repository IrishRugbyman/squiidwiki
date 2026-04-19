"""Stats service — reads from materialized views, cached in Redis.

Falls back gracefully when Redis or the MV is unavailable
(e.g., SQLite test environment).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.cache import get_or_set
from backend.settings import settings

logger = logging.getLogger(__name__)

_TTL = settings.redis.stats_ttl


async def get_member_stats(db: AsyncSession, universe_id: Optional[int] = None) -> Any:
    cache_key = f"stats:members:{universe_id or 'all'}"

    async def _load():
        try:
            if universe_id is not None:
                result = await db.execute(
                    text("SELECT * FROM member_stats WHERE universe_id = :uid"),
                    {"uid": universe_id},
                )
            else:
                result = await db.execute(text("SELECT * FROM member_stats"))
            rows = result.mappings().all()
            return [dict(r) for r in rows]
        except OperationalError:
            return []

    return await get_or_set(cache_key, _load, ttl=_TTL)


async def get_set_stats(db: AsyncSession, universe_id: Optional[int] = None) -> Any:
    cache_key = f"stats:sets:{universe_id or 'all'}"

    async def _load():
        try:
            if universe_id is not None:
                result = await db.execute(
                    text("SELECT * FROM set_stats WHERE universe_id = :uid"),
                    {"uid": universe_id},
                )
            else:
                result = await db.execute(text("SELECT * FROM set_stats"))
            rows = result.mappings().all()
            return [dict(r) for r in rows]
        except OperationalError:
            return []

    return await get_or_set(cache_key, _load, ttl=_TTL)
