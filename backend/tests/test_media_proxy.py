"""The share-image proxy only reads objects this backend could have signed."""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core import storage
from app.core.config import settings
from app.core.enums import GlobalRole

ENDPOINT = "https://acct.r2.cloudflarestorage.com"


@pytest_asyncio.fixture(loop_scope="session")
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    await create_user(db_session, email, "userpass", GlobalRole.USER)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "userpass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(autouse=True)
def _r2(monkeypatch):
    monkeypatch.setattr(settings, "r2_endpoint_url", ENDPOINT)
    monkeypatch.setattr(settings, "r2_bucket_prod", "wiki-prod")
    monkeypatch.setattr(settings, "r2_bucket_test", "wiki-test")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            f"{ENDPOINT}/wiki-prod/prod/member/a.jpg?X-Amz-Signature=x",
            ("wiki-prod", "prod/member/a.jpg"),
        ),
        (f"{ENDPOINT}/wiki-test/test/set/b%20c.png", ("wiki-test", "test/set/b c.png")),
        (f"{ENDPOINT}/other-bucket/prod/a.jpg", None),
        (f"{ENDPOINT}/wiki-prod/", None),
        ("https://evil.example.com/wiki-prod/prod/a.jpg", None),
        ("http://acct.r2.cloudflarestorage.com/wiki-prod/prod/a.jpg", None),
        ("https://acct.r2.cloudflarestorage.com.evil.com/wiki-prod/a.jpg", None),
        ("file:///etc/passwd", None),
    ],
)
def test_key_from_signed_url(url, expected):
    assert storage.key_from_signed_url(url) == expected


@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_rejects_foreign_url(client, auth_headers):
    r = await client.get(
        "/api/v1/media/proxy", params={"url": "https://example.com/x.png"}, headers=auth_headers
    )
    assert r.status_code == 400


@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_requires_auth(anon_client):
    r = await anon_client.get("/api/v1/media/proxy", params={"url": f"{ENDPOINT}/wiki-prod/a.jpg"})
    assert r.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_serves_object(client, auth_headers, monkeypatch):
    async def fake_get(bucket, key):
        assert (bucket, key) == ("wiki-prod", "prod/a.jpg")
        return b"\x89PNG", "image/png"

    monkeypatch.setattr(storage, "get_object", fake_get)
    r = await client.get(
        "/api/v1/media/proxy",
        params={"url": f"{ENDPOINT}/wiki-prod/prod/a.jpg?sig=1"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.content == b"\x89PNG"
    assert r.headers["content-type"] == "image/png"
