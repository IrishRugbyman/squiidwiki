"""Cloudflare R2 (S3-compatible) storage helpers.

Bucket selection follows the active DB mode (prod vs test) so test uploads
never touch prod assets and vice versa.

The aiobotocore client is a long-lived singleton — opened lazily on first use
and closed once via `close_storage()` from the FastAPI lifespan. Constructing
the client per-call (the previous behaviour) added tens of milliseconds per
signed URL, which list endpoints multiplied by ~50 rows × 2 keys.

Signed GET URLs are cached in-process for nearly the full URL lifetime, so
repeated list renders skip re-signing entirely.
"""
from __future__ import annotations

import asyncio
import time
from contextlib import AsyncExitStack
from typing import Optional

from aiobotocore.session import get_session

from app.core.config import settings
from app.core.database import get_db_mode


def get_bucket() -> str:
    return settings.r2_bucket_prod if get_db_mode() == "prod" else settings.r2_bucket_test


_client_instance = None
_client_stack: AsyncExitStack | None = None
_client_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _client_lock
    if _client_lock is None:
        _client_lock = asyncio.Lock()
    return _client_lock


async def _get_client():
    global _client_instance, _client_stack
    if _client_instance is not None:
        return _client_instance
    async with _get_lock():
        if _client_instance is not None:
            return _client_instance
        stack = AsyncExitStack()
        await stack.__aenter__()
        session = get_session()
        client = await stack.enter_async_context(
            session.create_client(
                "s3",
                endpoint_url=settings.r2_endpoint_url,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
                region_name="auto",
            )
        )
        _client_instance = client
        _client_stack = stack
        return _client_instance


async def close_storage() -> None:
    global _client_instance, _client_stack
    if _client_stack is not None:
        await _client_stack.__aexit__(None, None, None)
    _client_instance = None
    _client_stack = None


# (bucket, key) -> (url, expires_monotonic)
_url_cache: dict[tuple[str, str], tuple[str, float]] = {}
_URL_CACHE_MARGIN_SECONDS = 60


async def upload_object(key: str, data: bytes, content_type: str) -> None:
    client = await _get_client()
    await client.put_object(
        Bucket=get_bucket(),
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    _url_cache.pop((get_bucket(), key), None)


async def delete_object(key: str) -> None:
    client = await _get_client()
    await client.delete_object(Bucket=get_bucket(), Key=key)
    _url_cache.pop((get_bucket(), key), None)


async def signed_get_url(key: str, ttl: Optional[int] = None) -> str:
    effective_ttl = ttl or settings.r2_signed_url_ttl_seconds
    bucket = get_bucket()
    cache_key = (bucket, key)
    now = time.monotonic()
    cached = _url_cache.get(cache_key)
    if cached is not None and cached[1] > now:
        return cached[0]
    client = await _get_client()
    url = await client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=effective_ttl,
    )
    _url_cache[cache_key] = (url, now + effective_ttl - _URL_CACHE_MARGIN_SECONDS)
    return url
