"""APScheduler setup for periodic background jobs.

``start_scheduler()`` / ``stop_scheduler()`` are called from the app lifespan.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.stats.refresh import refresh_materialized_views

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        refresh_materialized_views,
        trigger="interval",
        minutes=5,
        id="refresh_stats",
        replace_existing=True,
        misfire_grace_time=60,
    )
    _scheduler.start()
    logger.info("APScheduler started — stats refresh every 5 minutes")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
    _scheduler = None
