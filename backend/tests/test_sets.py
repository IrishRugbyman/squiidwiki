"""API integration tests for the /api/v1/sets/ vertical slice."""

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


async def test_create_set(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/sets/",
        json={"universe_id": universe_id, "name": "Terror Town"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Terror Town"
    assert data["universe_id"] == universe_id


async def test_list_sets(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/sets/",
        json={"universe_id": universe_id, "name": "Set Alpha"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/sets/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_set(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": "Ghost Squad"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/sets/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Ghost Squad"
    assert "friend_ids" in data
    assert "enemy_ids" in data


async def test_get_set_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/sets/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_set(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": "Old Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/sets/{created['id']}?universe_id={universe_id}",
        json={"name_variants": [{"name": "New Name", "is_primary": True}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


async def test_delete_set_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": "ToDelete"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/sets/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_set_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": "NoDelete"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/sets/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_search_sets(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/sets/",
        json={"universe_id": universe_id, "name": "BreakNeck Boys"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/sets/search?universe_id={universe_id}&q=BreakNeck",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_set_stats(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": "Stats Set"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/sets/{created['id']}/stats?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "member_count" in data
    assert "total_kills" in data


_audit_attached = False


def _attach_audit_once() -> None:
    """The ASGI test client skips the app lifespan, which is where the audit
    listeners are attached; attaching twice would write every row twice."""
    global _audit_attached
    if not _audit_attached:
        from app.core.audit import attach_audit_listeners

        attach_audit_listeners()
        _audit_attached = True


async def test_set_activity_includes_edits_to_the_set_itself(
    client: AsyncClient, db_session: AsyncSession
):
    # audit_log stores the table name, "sets"; the feed used to look for "set"
    # and so showed only member edits, never the set's own creation or updates.
    _attach_audit_once()
    token = await _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/sets/",
        json={"universe_id": universe_id, "name": "Activity Block"},
        headers=headers,
    )
    set_id = resp.json()["id"]
    resp = await client.patch(
        f"/api/v1/sets/{set_id}?universe_id={universe_id}",
        json={"bio": "Edited once."},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/sets/{set_id}/activity?universe_id={universe_id}", headers=headers
    )
    assert resp.status_code == 200
    entries = resp.json()
    assert [(e["entity_type"], e["action"]) for e in entries] == [
        ("set", "UPDATE"),
        ("set", "CREATE"),
    ]
    assert all(e["target_label"] == "Activity Block" for e in entries)


async def test_set_sources_link_and_replace(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    h = {"Authorization": f"Bearer {token}"}
    src = []
    for title in ("Map placemark", "Member interview"):
        r = await client.post(
            "/api/v1/sources/",
            json={"universe_id": uni, "title": title, "url": f"https://e.x/{_uid()}"},
            headers=h,
        )
        assert r.status_code == 201, r.text
        src.append(r.json()["id"])

    created = await client.post(
        "/api/v1/sets/",
        json={"universe_id": uni, "name": f"Harperside {_uid()}", "source_ids": [src[0]]},
        headers=h,
    )
    assert created.status_code == 201, created.text
    sid = created.json()["id"]
    detail = f"/api/v1/sets/{sid}/detail?universe_id={uni}"
    got = (await client.get(detail, headers=h)).json()
    assert [s["title"] for s in got["sources"]] == ["Map placemark"]
    assert got["source_ids"] == [src[0]]

    url = f"/api/v1/sets/{sid}?universe_id={uni}"
    assert (await client.patch(url, json={"source_ids": src}, headers=h)).status_code == 200
    # A PATCH without source_ids leaves the links alone.
    assert (await client.patch(url, json={"bio": "Ravendale."}, headers=h)).status_code == 200
    got = (await client.get(url, headers=h)).json()
    assert sorted(got["source_ids"]) == sorted(src)

    bad = await client.patch(url, json={"source_ids": [str(uuid.uuid4())]}, headers=h)
    assert bad.status_code == 422
    assert sorted((await client.get(url, headers=h)).json()["source_ids"]) == sorted(src)

    assert (await client.patch(url, json={"source_ids": []}, headers=h)).status_code == 200
    assert (await client.get(detail, headers=h)).json()["sources"] == []
