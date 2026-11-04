"""Regression tests for the follow-ups to the 2026-11 correctness review.

Each test states the documented contract or HTTP rule it checks. All names
and numbers are invented.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners
from app.core.enums import GlobalRole

# The ASGI test client skips the lifespan, where the audit listeners attach.
attach_audit_listeners()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _admin(client: AsyncClient, session: AsyncSession) -> dict:
    email = f"followup_{_uid()}@example.com"
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


async def _status(session: AsyncSession, call) -> tuple[int, str]:
    """Status of a request, with an unhandled server error counted as a 500.

    The ASGI transport re-raises what the app did not handle, and a failed
    flush leaves the shared session unusable for the tests after this one.
    """
    try:
        resp = await call
    except Exception as e:  # noqa: BLE001 - the point is to see any crash
        await session.rollback()
        return 500, repr(e)
    return resp.status_code, resp.text


async def _member(client: AsyncClient, h: dict, uni: str, nickname: str) -> str:
    return (await _post(client, h, "/api/v1/members/", {"universe_id": uni, "nickname": nickname}))[
        "id"
    ]


# --- 1. duplicate participants ------------------------------------------------


async def test_the_same_member_twice_in_an_incident_is_a_422(
    client: AsyncClient, db_session: AsyncSession
):
    """A member takes part in an incident once (incident_participant's key is
    incident + member), with one role and one outcome. Listing him twice is bad
    input, so a 422 that says so, on create and on update, and nothing written."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    twice = await _member(client, h, uni, "Followup Twice")
    once = await _member(client, h, uni, "Followup Once")
    participants = [
        {"member_id": twice, "role": "SHOOTER", "outcome": "UNHARMED"},
        {"member_id": once, "role": "VICTIM", "outcome": "INJURED"},
        {"member_id": twice, "role": "VICTIM", "outcome": "KILLED"},
    ]

    code, body = await _status(
        db_session,
        client.post(
            "/api/v1/incidents/",
            json={"universe_id": uni, "type": "SHOOTING", "participants": participants},
            headers=h,
        ),
    )
    assert code == 422, body
    assert twice in body and "more than once" in body

    incident = await _post(
        client,
        h,
        "/api/v1/incidents/",
        {"universe_id": uni, "type": "SHOOTING", "participants": participants[:2]},
    )
    code, body = await _status(
        db_session,
        client.patch(
            f"/api/v1/incidents/{incident['id']}?universe_id={uni}",
            json={"participants": participants},
            headers=h,
        ),
    )
    assert code == 422, body
    assert twice in body and "more than once" in body

    got = (
        await client.get(f"/api/v1/incidents/{incident['id']}?universe_id={uni}", headers=h)
    ).json()
    assert sorted(p["member_id"] for p in got["participants"]) == sorted([twice, once])
    # The refused edit marked nobody dead.
    member = (await client.get(f"/api/v1/members/{twice}?universe_id={uni}", headers=h)).json()
    assert member["status"] != "DEAD"


async def test_the_same_set_twice_in_an_incident_is_a_422(
    client: AsyncClient, db_session: AsyncSession
):
    """incident_set_participant is keyed on incident + set the same way."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    s = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Crew {_uid()}"})
    sets = [
        {"set_id": s["id"], "role": "SHOOTER"},
        {"set_id": s["id"], "role": "VICTIM"},
    ]
    code, body = await _status(
        db_session,
        client.post(
            "/api/v1/incidents/",
            json={"universe_id": uni, "type": "SHOOTING", "set_participants": sets},
            headers=h,
        ),
    )
    assert code == 422, body
    assert s["id"] in body

    incident = await _post(client, h, "/api/v1/incidents/", {"universe_id": uni, "type": "FIGHT"})
    code, body = await _status(
        db_session,
        client.patch(
            f"/api/v1/incidents/{incident['id']}?universe_id={uni}",
            json={"set_participants": sets},
            headers=h,
        ),
    )
    assert code == 422, body
