"""API integration tests for the /api/v1/businesses/ vertical slice."""

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


async def _make_universe(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _make_member(client: AsyncClient, token: str, universe_id: str, nickname: str) -> str:
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": nickname},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _make_set(client: AsyncClient, token: str, universe_id: str, name: str) -> str:
    resp = await client.post(
        "/api/v1/sets/",
        json={"universe_id": universe_id, "name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _make_source(client: AsyncClient, token: str, universe_id: str, title: str) -> str:
    resp = await client.post(
        "/api/v1/sources/",
        json={
            "universe_id": universe_id,
            "url": "https://example.com/article",
            "title": title,
            "reliability": "MEDIUM",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_business(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/businesses/",
        json={
            "universe_id": universe_id,
            "name": "Casino Le Phare",
            "business_type": "GAMING",
            "status": "ACTIVE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Casino Le Phare"
    assert data["business_type"] == "GAMING"
    assert data["status"] == "ACTIVE"
    assert data["slug"] == "casino-le-phare"


async def test_create_business_with_owner_set_and_source(
    client: AsyncClient, db_session: AsyncSession
):
    """The motivating case: a business owned by a member and protected by a set."""
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    owner_id = await _make_member(client, token, universe_id, "Ignace")
    set_id = await _make_set(client, token, universe_id, "Brise de Mer")
    source_id = await _make_source(client, token, universe_id, "Article on machines à sous")

    resp = await client.post(
        "/api/v1/businesses/",
        json={
            "universe_id": universe_id,
            "name": "Slot Machine Co",
            "business_type": "GAMING",
            "members": [{"member_id": owner_id, "role": "OWNER"}],
            "set_ids": [set_id],
            "source_ids": [source_id],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    business_id = resp.json()["id"]

    detail = (
        await client.get(
            f"/api/v1/businesses/{business_id}?universe_id={universe_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    assert detail["set_ids"] == [set_id]
    assert detail["source_ids"] == [source_id]
    assert len(detail["members"]) == 1
    assert detail["members"][0]["member_id"] == owner_id
    assert detail["members"][0]["role"] == "OWNER"
    assert detail["members"][0]["member_name"] == "Ignace"


async def test_list_businesses_filters_by_type_and_set(
    client: AsyncClient, db_session: AsyncSession
):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    set_id = await _make_set(client, token, universe_id, "Petit Bar")

    await client.post(
        "/api/v1/businesses/",
        json={
            "universe_id": universe_id,
            "name": "Cercle de jeux",
            "business_type": "GAMING",
            "set_ids": [set_id],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/businesses/",
        json={"universe_id": universe_id, "name": "BTP Corp", "business_type": "CONSTRUCTION"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(
        f"/api/v1/businesses/?universe_id={universe_id}&business_type=GAMING",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Cercle de jeux"
    assert items[0]["member_count"] == 0

    resp = await client.get(
        f"/api/v1/businesses/?universe_id={universe_id}&set_id={set_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert [i["name"] for i in resp.json()["items"]] == ["Cercle de jeux"]


async def test_update_business_replaces_members(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    owner_a = await _make_member(client, token, universe_id, "Owner A")
    owner_b = await _make_member(client, token, universe_id, "Owner B")

    created = (
        await client.post(
            "/api/v1/businesses/",
            json={
                "universe_id": universe_id,
                "name": "Restaurant Chez Toi",
                "business_type": "HOSPITALITY",
                "members": [{"member_id": owner_a, "role": "OWNER"}],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()

    resp = await client.patch(
        f"/api/v1/businesses/{created['id']}?universe_id={universe_id}",
        json={"status": "SEIZED", "members": [{"member_id": owner_b, "role": "FRONT"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SEIZED"

    detail = (
        await client.get(
            f"/api/v1/businesses/{created['id']}?universe_id={universe_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    assert len(detail["members"]) == 1
    assert detail["members"][0]["member_id"] == owner_b
    assert detail["members"][0]["role"] == "FRONT"


async def test_deleting_a_member_does_not_break_the_business(
    client: AsyncClient, db_session: AsyncSession
):
    """business_member.member_id cascades: removing the owner must not orphan
    the join row or 500 on the FK."""
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    owner_id = await _make_member(client, token, universe_id, "Doomed Owner")

    created = (
        await client.post(
            "/api/v1/businesses/",
            json={
                "universe_id": universe_id,
                "name": "Waste Co",
                "business_type": "WASTE_MANAGEMENT",
                "members": [{"member_id": owner_id, "role": "OWNER"}],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()

    del_resp = await client.delete(
        f"/api/v1/members/{owner_id}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204

    detail = (
        await client.get(
            f"/api/v1/businesses/{created['id']}?universe_id={universe_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    assert detail["members"] == []


async def test_get_business_by_slug(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/businesses/",
        json={"universe_id": universe_id, "name": "Port Franc", "business_type": "PORT"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/businesses/port-franc?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Port Franc"


async def test_get_business_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/businesses/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_delete_business(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/businesses/",
            json={
                "universe_id": universe_id,
                "name": "To Be Seized",
                "business_type": "OTHER",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/businesses/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
    resp = await client.get(
        f"/api/v1/businesses/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
