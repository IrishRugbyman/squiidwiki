"""Regression tests from the 2026-11 correctness review.

Each test states the documented contract it checks (root CLAUDE.md and
backend/CLAUDE.md). All names are invented.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners
from app.core.enums import GlobalRole

# asyncio_mode=auto (pytest.ini) runs these on the session loop.
# The ASGI test client skips the lifespan, where the audit listeners attach.
attach_audit_listeners()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _admin(client: AsyncClient, session: AsyncSession) -> dict:
    email = f"review_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _post(client: AsyncClient, h: dict, path: str, body: dict) -> dict:
    resp = await client.post(path, json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _universe(client: AsyncClient, h: dict) -> str:
    return (
        await _post(
            client, h, "/api/v1/universes/", {"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}
        )
    )["id"]


async def _history(client: AsyncClient, h: dict, uni: str, kind: str, eid: str) -> dict:
    resp = await client.get(f"/api/v1/history/{kind}/{eid}?universe_id={uni}", headers=h)
    assert resp.status_code == 200, resp.text
    return resp.json()


# --- death sync ---------------------------------------------------------------


async def test_death_sync_copies_no_date_below_year_precision(
    client: AsyncClient, db_session: AsyncSession
):
    """date_of_death is copied "only when the incident date has at least year
    precision". A date marked UNKNOWN is below Y even when a year is filled in,
    and the incident itself treats it as undated (no sortable_date)."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    victim = await _post(
        client, h, "/api/v1/members/", {"universe_id": uni, "nickname": "Review Victim"}
    )
    incident = await _post(
        client,
        h,
        "/api/v1/incidents/",
        {
            "universe_id": uni,
            "type": "MURDER",
            "date": {"year": 2015, "precision": "UNKNOWN", "approx": False},
            "participants": [{"member_id": victim["id"], "role": "VICTIM", "outcome": "KILLED"}],
        },
    )
    member = (
        await client.get(f"/api/v1/members/{victim['id']}?universe_id={uni}", headers=h)
    ).json()
    assert member["status"] == "DEAD"
    assert member["death_incident_id"] == incident["id"]
    assert member["date_of_death"] is None
