"""API integration tests for the /api/v1/alliances/ vertical slice."""

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


async def test_create_alliance(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/alliances/",
        json={"universe_id": universe_id, "name": "East Side Coalition", "status": "ACTIVE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "East Side Coalition"
    assert data["status"] == "ACTIVE"


async def test_list_alliances(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/alliances/",
        json={"universe_id": universe_id, "name": "West Coalition"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/alliances/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_alliance(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "North Bloc"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "North Bloc"
    assert "set_ids" in data
    assert "territory_ids" in data


async def test_get_alliance_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/alliances/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_alliance(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "Original"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        json={"status": "DORMANT"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DORMANT"


async def test_delete_alliance_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "DeleteMe"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_alliance_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "Protected"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_search_alliances(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/alliances/",
        json={"universe_id": universe_id, "name": "SkylineAlliance"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/alliances/search?universe_id={universe_id}&q=Skyline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_alliance_members_includes_members_of_its_sets(
    client: AsyncClient, db_session: AsyncSession
):
    """An alliance's roster is its sets' members, not only directly-tagged ones.

    Regression: the query filtered on Member.alliance_id alone, so an alliance
    whose sets were full reported zero members, and every count derived from
    that list on the alliance page read 0.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    alliance_id = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": f"Coalition {_uid()}"},
            headers=auth,
        )
    ).json()["id"]

    set_id = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": f"Set {_uid()}", "alliance_id": alliance_id},
            headers=auth,
        )
    ).json()["id"]

    # In one of the alliance's sets, but not tagged to the alliance directly.
    via_set = (
        await client.post(
            "/api/v1/members/",
            json={
                "universe_id": universe_id,
                "nickname": "ViaSet",
                "affiliations": [{"set_id": set_id, "is_primary": True}],
            },
            headers=auth,
        )
    ).json()["id"]

    # Tagged straight to the alliance with no set at all.
    direct = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Direct", "alliance_id": alliance_id},
            headers=auth,
        )
    ).json()["id"]

    # In neither, and must not appear.
    outsider = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Outsider"},
            headers=auth,
        )
    ).json()["id"]

    resp = await client.get(
        f"/api/v1/alliances/{alliance_id}/members",
        params={"universe_id": universe_id, "limit": 100},
        headers=auth,
    )
    assert resp.status_code == 200
    ids = {m["id"] for m in resp.json()["items"]}
    assert via_set in ids
    assert direct in ids
    assert outsider not in ids


async def test_alliance_incidents_includes_incidents_of_its_sets_members(
    client: AsyncClient, db_session: AsyncSession
):
    """Same union for incidents: a set member's incident belongs to the alliance.

    Regression: the join filtered on Member.alliance_id, so an alliance whose
    sets' members were incident participants showed no incidents at all.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    alliance_id = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": f"Coalition {_uid()}"},
            headers=auth,
        )
    ).json()["id"]
    set_id = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": f"Set {_uid()}", "alliance_id": alliance_id},
            headers=auth,
        )
    ).json()["id"]
    member_id = (
        await client.post(
            "/api/v1/members/",
            json={
                "universe_id": universe_id,
                "nickname": "ViaSet",
                "affiliations": [{"set_id": set_id, "is_primary": True}],
            },
            headers=auth,
        )
    ).json()["id"]

    incident_id = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": universe_id,
                "type": "SHOOTING",
                "date": {"year": 2020, "month": 5, "day": 1, "precision": "YMD", "approx": False},
                "participants": [{"member_id": member_id, "role": "VICTIM", "outcome": "INJURED"}],
            },
            headers=auth,
        )
    ).json()["id"]

    resp = await client.get(
        f"/api/v1/alliances/{alliance_id}/incidents",
        params={"universe_id": universe_id, "limit": 100},
        headers=auth,
    )
    assert resp.status_code == 200
    assert incident_id in {i["id"] for i in resp.json()["items"]}
