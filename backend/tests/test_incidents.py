"""API integration tests for the /api/v1/incidents/ vertical slice."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
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


async def _make_member(client: AsyncClient, token: str, universe_id: str, nickname: str) -> str:
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": nickname},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_incident(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/incidents/",
        json={
            "universe_id": universe_id,
            "type": "SHOOTING",
            "location_text": "7 Mile & Gratiot",
            "date": {"year": 2022, "precision": "Y", "approx": False},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "SHOOTING"
    assert data["location_text"] == "7 Mile & Gratiot"


async def test_create_incident_with_participants(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    shooter_id = await _make_member(client, token, universe_id, "BigShot")
    victim_id = await _make_member(client, token, universe_id, "Lil Victim")
    resp = await client.post(
        "/api/v1/incidents/",
        json={
            "universe_id": universe_id,
            "type": "SHOOTING",
            "participants": [
                {"member_id": shooter_id, "role": "SHOOTER", "outcome": "UNHARMED"},
                {"member_id": victim_id, "role": "VICTIM", "outcome": "INJURED"},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201


async def test_get_incident_has_participants(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    member_id = await _make_member(client, token, universe_id, "Witness")
    created = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": universe_id,
                "type": "MURDER",
                "participants": [
                    {"member_id": member_id, "role": "VICTIM", "outcome": "KILLED"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/incidents/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["participants"]) == 1
    assert data["participants"][0]["role"] == "VICTIM"
    assert data["participants"][0]["outcome"] == "KILLED"


async def test_list_incidents(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/incidents/",
        json={"universe_id": universe_id, "type": "SHOOTING"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/incidents/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_get_incident_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/incidents/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_incident(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/incidents/",
            json={"universe_id": universe_id, "type": "SHOOTING"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/incidents/{created['id']}?universe_id={universe_id}",
        json={"verified": True, "narrative": "Occurred near park entrance."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["narrative"] == "Occurred near park entrance."


async def test_delete_incident_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/incidents/",
            json={"universe_id": universe_id, "type": "SHOOTING"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/incidents/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_incident_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/incidents/",
            json={"universe_id": universe_id, "type": "MURDER"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/incidents/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_incident_source_ids_in_detail(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/incidents/",
            json={"universe_id": universe_id, "type": "SHOOTING"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/incidents/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "source_ids" in resp.json()


async def test_acquitted_participant_excluded_from_offender_stats(
    client: AsyncClient, db_session: AsyncSession
):
    """An acquitted SHOOTER keeps the role on record but stops counting as a kill.

    Expected values come from the domain rule, not from running the view: one
    shooter, one killed victim, so kills is 1 while the role stands and 0 once a
    court has cleared him. The first half of the test is what proves the second
    half can fail.
    """
    token = await _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    universe_id = await _make_universe(client, token)
    shooter_id = await _make_member(client, token, universe_id, "Accused")
    victim_id = await _make_member(client, token, universe_id, "Deceased")

    incident = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": universe_id,
                "type": "MURDER",
                "participants": [
                    {"member_id": shooter_id, "role": "SHOOTER", "outcome": "UNHARMED"},
                    {"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"},
                ],
            },
            headers=headers,
        )
    ).json()

    async def stats() -> dict:
        # Non-concurrent on purpose: crud.refresh_materialized_views swallows
        # every exception, which would leave this test reading stale rows.
        await db_session.execute(text("REFRESH MATERIALIZED VIEW member_stats"))
        await db_session.commit()
        resp = await client.get(
            f"/api/v1/members/{shooter_id}/stats?universe_id={universe_id}", headers=headers
        )
        assert resp.status_code == 200
        return resp.json()

    before = await stats()
    assert before["shootings"] == 1
    assert before["kills"] == 1

    resp = await client.patch(
        f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}",
        json={
            "participants": [
                {
                    "member_id": shooter_id,
                    "role": "SHOOTER",
                    "outcome": "UNHARMED",
                    "acquitted": True,
                    "notes": "Acquitted at trial.",
                },
                {"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"},
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200

    after = await stats()
    assert after["kills"] == 0, "a court-cleared role must not be counted as a kill"
    assert after["shootings"] == 0

    # The role itself is still on record — the flag qualifies it, it does not delete it.
    detail = (
        await client.get(f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}", headers=headers)
    ).json()
    shooter = next(p for p in detail["participants"] if p["member_id"] == shooter_id)
    assert shooter["role"] == "SHOOTER"
    assert shooter["acquitted"] is True
    assert shooter["notes"] == "Acquitted at trial."

    # The victim is untouched: being shot is not a claim anyone can be acquitted of.
    victim = next(p for p in detail["participants"] if p["member_id"] == victim_id)
    assert victim["acquitted"] is False
