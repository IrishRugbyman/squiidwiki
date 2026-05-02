import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def test_register_and_login(client: AsyncClient, db_session: AsyncSession):
    email = f"reg_{_uid()}@example.com"
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
    assert resp.status_code == 201
    assert resp.json()["email"] == email

    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    email = f"pw_{_uid()}@example.com"
    await create_user(db_session, email, "correct")
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401


async def test_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_returns_user(client: AsyncClient, db_session: AsyncSession):
    email = f"me_{_uid()}@example.com"
    await create_user(db_session, email, "pass123")
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "pass123"})
    token = login.json()["access_token"]

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == email


async def test_duplicate_register(client: AsyncClient, db_session: AsyncSession):
    email = f"dup_{_uid()}@example.com"
    await create_user(db_session, email, "pass")
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": "pass"})
    assert resp.status_code == 409
