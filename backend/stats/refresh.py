"""Materialized view refresh utilities.

The two views (member_stats, set_stats) aggregate incident data and are
refreshed on a schedule.  SQLite does not support materialized views, so
the refresh is a no-op in test environments.
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from backend.database.base_class import get_db_context

logger = logging.getLogger(__name__)

_REFRESH_VIEWS = ["member_stats", "set_stats"]


async def refresh_materialized_views() -> None:
    """REFRESH MATERIALIZED VIEW CONCURRENTLY for each stats view."""
    try:
        async with get_db_context() as db:
            for view in _REFRESH_VIEWS:
                await db.execute(
                    text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                )
                logger.info("Refreshed materialized view: %s", view)
    except OperationalError as exc:
        # SQLite in tests doesn't support MVs — silently skip
        logger.debug("Skipping MV refresh (unsupported backend): %s", exc)
    except Exception as exc:
        logger.error("Failed to refresh materialized views: %s", exc)
