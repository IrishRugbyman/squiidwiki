"""API integration tests for the /api/v1/municipalities/ vertical slice."""

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


async def _make_universe(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_municipality(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": universe_id, "name": "Detroit"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Detroit"
    assert data["parent_id"] is None


async def test_create_municipality_with_parent(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    parent = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "Detroit"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": universe_id, "name": "Midtown", "parent_id": parent["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["parent_id"] == parent["id"]


async def test_list_municipalities(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": universe_id, "name": "Flint"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/municipalities/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_municipality(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "Pontiac"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pontiac"


async def test_get_municipality_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/municipalities/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_municipality(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "OldName"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        json={"name": "NewName"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"


async def test_delete_municipality_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "DeleteMe"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_municipality_forbidden_for_user(
    client: AsyncClient, db_session: AsyncSession
):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "Protected"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_list_rolls_district_incidents_into_the_city(
    client: AsyncClient, db_session: AsyncSession
):
    """A city's total counts its districts' incidents; set_count follows anchor and territory.

    Regression: the list showed only incidents filed on the city itself, and
    incidents are usually filed under a district, so Detroit read 23 of 42.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    async def post(path: str, body: dict) -> str:
        resp = await client.post(path, json={"universe_id": universe_id, **body}, headers=auth)
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    city = await post("/api/v1/municipalities/", {"name": "Detroit"})
    district = await post("/api/v1/municipalities/", {"name": "48205", "parent_id": city})
    other = await post("/api/v1/municipalities/", {"name": "Flint"})
    await post("/api/v1/incidents/", {"type": "SHOOTING", "municipality_id": city})
    for _ in range(2):
        await post("/api/v1/incidents/", {"type": "SHOOTING", "municipality_id": district})
    # One set, anchored on the city and claiming the district as territory.
    await post(
        "/api/v1/sets/",
        {"name": f"Set {_uid()}", "municipality_id": city, "territory_ids": [district]},
    )

    resp = await client.get(
        "/api/v1/municipalities/", params={"universe_id": universe_id, "limit": 1000}, headers=auth
    )
    assert resp.status_code == 200
    rows = {r["id"]: r for r in resp.json()["items"]}
    assert rows[city]["incident_count"] == 1
    assert rows[city]["total_incident_count"] == 3
    assert rows[district]["total_incident_count"] == 2
    assert rows[other]["total_incident_count"] == 0
    assert rows[city]["set_count"] == 1
    assert rows[district]["set_count"] == 1
    assert rows[other]["set_count"] == 0
