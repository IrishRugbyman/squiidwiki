"""Tests for cache helper and stats service.

The materialized views only exist in Postgres. These tests unit-test the
cache helper by mocking Redis, and verify the graceful fallback when the
view is unavailable (as in SQLite tests).
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCacheHelper:
    """Unit tests for get_or_set — Redis is mocked."""

    async def test_returns_cached_value(self):
        cached_data = [{"member_id": 1, "shots_fired": 3}]
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        with patch("backend.cache.get_redis", return_value=mock_redis):
            from backend.cache import get_or_set
            loader = AsyncMock(return_value=[])
            result = await get_or_set("test_key", loader, ttl=60)

        assert result == cached_data
        loader.assert_not_called()

    async def test_calls_loader_on_cache_miss(self):
        fresh_data = [{"member_id": 2, "shots_fired": 1}]
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch("backend.cache.get_redis", return_value=mock_redis):
            from backend.cache import get_or_set
            loader = AsyncMock(return_value=fresh_data)
            result = await get_or_set("miss_key", loader, ttl=60)

        assert result == fresh_data
        loader.assert_called_once()
        mock_redis.set.assert_called_once()

    async def test_fallback_to_loader_on_redis_error(self):
        fallback_data = [{"member_id": 3, "shots_fired": 0}]

        with patch("backend.cache.get_redis", side_effect=RuntimeError("Redis down")):
            from backend.cache import get_or_set
            loader = AsyncMock(return_value=fallback_data)
            result = await get_or_set("error_key", loader, ttl=60)

        assert result == fallback_data

    async def test_cache_stores_serialized_json(self):
        data = {"key": "value", "num": 42}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch("backend.cache.get_redis", return_value=mock_redis):
            from backend.cache import get_or_set
            await get_or_set("json_key", AsyncMock(return_value=data), ttl=30)

        call_args = mock_redis.set.call_args
        stored_value = json.loads(call_args[0][1])
        assert stored_value == data


class TestStatsServiceFallback:
    """Verify stats service returns empty list when MVs don't exist (SQLite)."""

    async def test_member_stats_returns_empty_on_sqlite(self, db):
        with patch("backend.cache.get_redis", side_effect=RuntimeError("no redis")):
            from backend.stats.service import get_member_stats
            result = await get_member_stats(db)
        assert result == []

    async def test_set_stats_returns_empty_on_sqlite(self, db):
        with patch("backend.cache.get_redis", side_effect=RuntimeError("no redis")):
            from backend.stats.service import get_set_stats
            result = await get_set_stats(db)
        assert result == []


class TestScheduler:
    """Verify scheduler starts, registers the job, and stops cleanly."""

    async def test_start_registers_refresh_job(self):
        from backend.scheduler import start_scheduler, stop_scheduler
        scheduler = start_scheduler()
        try:
            job = scheduler.get_job("refresh_stats")
            assert job is not None
        finally:
            stop_scheduler()

    async def test_stop_shuts_down_scheduler(self):
        from backend.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        stop_scheduler()
        from backend.scheduler import _scheduler
        assert _scheduler is None
