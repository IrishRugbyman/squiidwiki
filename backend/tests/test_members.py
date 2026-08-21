"""API integration tests for the /api/v1/members/ vertical slice."""

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


async def test_create_member(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": "Ghost", "status": "FREE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["display_name"] == "Ghost"
    assert data["status"] == "FREE"


async def test_create_member_nickname_unknown(client: AsyncClient, db_session: AsyncSession):
    """When nickname_unknown=True, display_name should use legal name."""
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_id,
            "legal_name": "John Doe",
            "nickname_unknown": True,
            "status": "FREE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["display_name"] == "John Doe"


async def test_list_members(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": "Spooky"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/members/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) >= 1


async def test_get_member(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Shadow"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Shadow"
    assert "source_ids" in data


async def test_get_member_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/members/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_member(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Lil D"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        json={"status": "LOCKED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "LOCKED"


async def test_delete_member_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "DeleteMe"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_member_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Protected"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_search_members(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": "Tornado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/members/search?universe_id={universe_id}&q=Tornado",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_member_stats(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "StatsGuy"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/members/{created['id']}/stats?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "shootings" in data
    assert "kills" in data
    assert data["shootings"] == 0


async def test_member_with_fuzzy_dob(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_id,
            "nickname": "OldTimer",
            "dob": {"year": 1990, "precision": "Y", "approx": True},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["dob"]["year"] == 1990
    assert data["dob"]["approx"] is True


async def test_search_returns_the_members_set(client: AsyncClient, db_session: AsyncSession):
    """Search must carry affiliations, not just the bare member row.

    Regression: search_members returned Members straight from the query without
    calling _attach_affiliations, so the schema serialised affiliations as [] and
    every primary_set_* field as null. The set column went blank in the UI while
    the data was intact in the database, and the old test passed because it only
    asserted a 200 and a list.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    headers = {"Authorization": f"Bearer {token}"}

    set_id = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": "Searchable Set"},
            headers=headers,
        )
    ).json()["id"]
    await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_id,
            "nickname": "FindMe",
            "affiliations": [{"set_id": set_id, "is_primary": True}],
        },
        headers=headers,
    )

    found = (
        await client.get(
            f"/api/v1/members/search?universe_id={universe_id}&q=FindMe", headers=headers
        )
    ).json()
    assert len(found) == 1
    hit = found[0]
    assert hit["primary_set_id"] == set_id
    assert hit["primary_set_name"] == "Searchable Set"
    assert [a["set_name"] for a in hit["affiliations"]] == ["Searchable Set"]

    # The list endpoint has always done this; search must agree with it.
    listed = (
        await client.get(f"/api/v1/members/?universe_id={universe_id}&q=FindMe", headers=headers)
    ).json()
    row = (listed["items"] if isinstance(listed, dict) else listed)[0]
    assert row["primary_set_name"] == hit["primary_set_name"]
