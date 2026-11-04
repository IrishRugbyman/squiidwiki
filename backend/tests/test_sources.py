"""API integration tests for the /api/v1/sources/ vertical slice."""

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


async def test_create_source(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/sources/",
        json={
            "universe_id": universe_id,
            "url": "https://example.com/article",
            "title": "Gang Activity Report 2022",
            "reliability": "HIGH",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Gang Activity Report 2022"
    assert data["reliability"] == "HIGH"


async def test_create_source_with_optional_fields(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/sources/",
        json={
            "universe_id": universe_id,
            "url": "https://news.example.com/story",
            "title": "Detailed Report",
            "publication": "Detroit Free Press",
            "reliability": "MEDIUM",
            "notes": "Important background context",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["publication"] == "Detroit Free Press"
    assert data["notes"] == "Important background context"


async def test_list_sources(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/sources/",
        json={
            "universe_id": universe_id,
            "url": "https://example.com/a",
            "title": "Test Article",
            "reliability": "UNVERIFIED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/sources/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_source(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/sources/",
            json={
                "universe_id": universe_id,
                "url": "https://example.com/b",
                "title": "Specific Article",
                "reliability": "LOW",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/sources/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Specific Article"


async def test_get_source_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/sources/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_source(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/sources/",
            json={
                "universe_id": universe_id,
                "url": "https://example.com/c",
                "title": "Original Title",
                "reliability": "UNVERIFIED",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/sources/{created['id']}?universe_id={universe_id}",
        json={"reliability": "HIGH", "notes": "Updated notes"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["reliability"] == "HIGH"
    assert data["notes"] == "Updated notes"


async def test_delete_source_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/sources/",
            json={
                "universe_id": universe_id,
                "url": "https://example.com/delete-me",
                "title": "Delete Me",
                "reliability": "LOW",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/sources/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_source_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/sources/",
            json={
                "universe_id": universe_id,
                "url": "https://example.com/protected",
                "title": "Protected",
                "reliability": "MEDIUM",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/sources/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_search_sources(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/sources/",
        json={
            "universe_id": universe_id,
            "url": "https://example.com/searchable",
            "title": "SearchableTitle123",
            "reliability": "HIGH",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/sources/search?universe_id={universe_id}&q=SearchableTitle",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def _cited_source(client: AsyncClient, token: str, universe_id: str) -> tuple[str, str, str]:
    """A source cited by one incident and two members. Returns (source, incident, member)."""
    auth = {"Authorization": f"Bearer {token}"}
    source_id = (
        await client.post(
            "/api/v1/sources/",
            json={
                "universe_id": universe_id,
                "url": f"https://example.com/{_uid()}",
                "title": "Cited Article",
                "publication": "Example Daily",
            },
            headers=auth,
        )
    ).json()["id"]
    member_ids = []
    for name in ("Cited One", "Cited Two"):
        resp = await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": name},
            headers=auth,
        )
        assert resp.status_code == 201, resp.text
        member_ids.append(resp.json()["id"])
    resp = await client.post(
        "/api/v1/incidents/",
        json={"universe_id": universe_id, "type": "SHOOTING"},
        headers=auth,
    )
    assert resp.status_code == 201, resp.text
    incident_id = resp.json()["id"]
    items = [
        {"source_id": source_id, "entity_type": "member", "entity_id": m} for m in member_ids
    ] + [{"source_id": source_id, "entity_type": "incident", "entity_id": incident_id}]
    batch = await client.post(
        "/api/v1/citations/batch",
        params={"universe_id": universe_id},
        json={"items": items},
        headers=auth,
    )
    assert batch.status_code == 200, batch.text
    assert len(batch.json()["created"]) == 3
    return source_id, incident_id, member_ids[0]


async def test_list_sources_carries_citation_counts(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    source_id, _, _ = await _cited_source(client, token, universe_id)
    resp = await client.get(
        "/api/v1/sources/",
        params={"universe_id": universe_id, "limit": 200},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    row = next(r for r in resp.json()["items"] if r["id"] == source_id)
    assert row["counts"]["incident"] == 1
    assert row["counts"]["member"] == 2
    assert row["counts"]["set"] == 0
    assert row["counts"]["total"] == 3
    assert row["publication"] == "Example Daily"


async def test_delete_cited_source(client: AsyncClient, db_session: AsyncSession):
    """A cited source is refused with its counts; `force` detaches it everywhere.

    Since citations moved to one table (2026-10-04) a source is RESTRICTed
    while cited, so a delete cannot silently strip a record of its evidence.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}
    source_id, incident_id, member_id = await _cited_source(client, token, universe_id)

    resp = await client.delete(
        f"/api/v1/sources/{source_id}", params={"universe_id": universe_id}, headers=auth
    )
    assert resp.status_code == 409, resp.text
    body = resp.json()
    assert body["code"] == "source_in_use"
    assert body["counts"]["incident"] == 1 and body["counts"]["member"] == 2

    resp = await client.delete(
        f"/api/v1/sources/{source_id}",
        params={"universe_id": universe_id, "force": True},
        headers=auth,
    )
    assert resp.status_code == 204, resp.text
    incident = await client.get(
        f"/api/v1/incidents/{incident_id}", params={"universe_id": universe_id}, headers=auth
    )
    assert incident.status_code == 200
    assert incident.json()["citations"] == []
    member = await client.get(
        f"/api/v1/members/{member_id}", params={"universe_id": universe_id}, headers=auth
    )
    assert member.status_code == 200
    assert member.json()["citations"] == []
