"""Cloudflare R2 (S3-compatible) storage helpers.

Bucket selection follows the active DB mode (prod vs test) so test uploads
never touch prod assets and vice versa.
"""
from contextlib import asynccontextmanager
from typing import Optional

from aiobotocore.session import get_session

from app.core.config import settings
from app.core.database import get_db_mode


def get_bucket() -> str:
    return settings.r2_bucket_prod if get_db_mode() == "prod" else settings.r2_bucket_test


@asynccontextmanager
async def _client():
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    ) as client:
        yield client


async def upload_object(key: str, data: bytes, content_type: str) -> None:
    async with _client() as client:
        await client.put_object(
            Bucket=get_bucket(),
            Key=key,
            Body=data,
            ContentType=content_type,
        )


async def delete_object(key: str) -> None:
    async with _client() as client:
        await client.delete_object(Bucket=get_bucket(), Key=key)


async def signed_get_url(key: str, ttl: Optional[int] = None) -> str:
    async with _client() as client:
        return await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": get_bucket(), "Key": key},
            ExpiresIn=ttl or settings.r2_signed_url_ttl_seconds,
        )
