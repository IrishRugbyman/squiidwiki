"""Async Redis client and cache helpers.

``init_redis()`` / ``close_redis()`` are called from the app lifespan.
``get_or_set()`` implements the standard cache-aside pattern.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

import redis.asyncio as aioredis

from backend.settings import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


def init_redis() -> aioredis.Redis:
    global _redis
    _redis = aioredis.from_url(
        settings.redis.url,
        encoding="utf-8",
        decode_responses=True,
    )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized — call init_redis() first")
    return _redis


async def get_or_set(
    key: str,
    loader: Callable[[], Any],
    ttl: int = 300,
) -> Any:
    """Return cached value if present; otherwise call loader, cache, and return."""
    try:
        redis = get_redis()
        cached = await redis.get(key)
        if cached is not None:
            return json.loads(cached)
        value = await loader() if callable(loader) else loader
        await redis.set(key, json.dumps(value), ex=ttl)
        return value
    except Exception as exc:
        logger.warning("Redis error, falling back to loader: %s", exc)
        return await loader() if callable(loader) else loader


async def invalidate(key: str) -> None:
    """Delete a single cache key."""
    try:
        await get_redis().delete(key)
    except Exception as exc:
        logger.warning("Redis invalidate error: %s", exc)


async def invalidate_prefix(prefix: str) -> None:
    """Delete all keys matching a prefix pattern (SCAN-safe)."""
    try:
        redis = get_redis()
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=f"{prefix}*", count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
    except Exception as exc:
        logger.warning("Redis invalidate_prefix error: %s", exc)
