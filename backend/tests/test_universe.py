import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _admin_token(client: AsyncClient, session: AsyncSession) -> str:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return resp.json()["access_token"]


async def _user_token(client: AsyncClient, session: AsyncSession) -> str:
    email = f"user_{_uid()}@example.com"
    await create_user(session, email, "userpass", GlobalRole.USER)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "userpass"})
    return resp.json()["access_token"]


async def test_create_universe_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": "Metro Detroit", "slug": f"metro-detroit-{_uid()}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert "metro-detroit" in resp.json()["slug"]


async def test_create_universe_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    token = await _user_token(client, db_session)
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": "Chicago", "slug": f"chicago-{_uid()}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_list_universes(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    await client.post(
        "/api/v1/universes/",
        json={"name": "Test City", "slug": f"test-city-{_uid()}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get("/api/v1/universes/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_universe_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    resp = await client.get(
        f"/api/v1/universes/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
