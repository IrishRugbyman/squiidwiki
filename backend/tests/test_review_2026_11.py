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


# --- FuzzyDate ----------------------------------------------------------------


async def test_impossible_fuzzy_date_is_a_422(client: AsyncClient, db_session: AsyncSession):
    """A FuzzyDate naming a day or month that does not exist is bad input, so a
    422, not a crash when the sortable date is computed from it."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    for date in (
        {"year": 2020, "month": 2, "day": 30, "precision": "YMD"},
        {"year": 2020, "month": 13, "precision": "YM"},
        {"year": 2020, "month": 0, "precision": "YM"},
    ):
        resp = await client.post(
            "/api/v1/incidents/",
            json={"universe_id": uni, "type": "SHOOTING", "date": date},
            headers=h,
        )
        assert resp.status_code == 422, (date, resp.text)


# --- set_gang / alliance_gang primary mirroring -------------------------------


async def test_deleting_a_gang_makes_the_next_one_position_zero(
    client: AsyncClient, db_session: AsyncSession
):
    """Position 0 is the primary. Deleting a set's primary gang promotes the
    next, so that gang is now at position 0 and its page lists the set as
    primary; likewise for an alliance's gangs."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    g1 = await _post(client, h, "/api/v1/gangs/", {"universe_id": uni, "name": f"First {_uid()}"})
    g2 = await _post(client, h, "/api/v1/gangs/", {"universe_id": uni, "name": f"Second {_uid()}"})
    s = await _post(
        client,
        h,
        "/api/v1/sets/",
        {"universe_id": uni, "name": f"Crew {_uid()}", "gang_ids": [g1["id"], g2["id"]]},
    )
    a = await _post(
        client,
        h,
        "/api/v1/alliances/",
        {"universe_id": uni, "name": f"Bloc {_uid()}", "gang_ids": [g1["id"], g2["id"]]},
    )
    resp = await client.delete(f"/api/v1/gangs/{g1['id']}?universe_id={uni}", headers=h)
    assert resp.status_code == 204, resp.text

    got = (await client.get(f"/api/v1/sets/{s['id']}?universe_id={uni}", headers=h)).json()
    assert got["gang_id"] == g2["id"]
    detail = (
        await client.get(f"/api/v1/gangs/{g2['id']}/detail?universe_id={uni}", headers=h)
    ).json()
    row = next(x for x in detail["sets"] if x["id"] == s["id"])
    assert row["is_primary"] is True

    position = (
        await db_session.execute(
            text("SELECT position FROM alliance_gang WHERE alliance_id = :a"), {"a": a["id"]}
        )
    ).scalar_one()
    assert position == 0


# --- alliance_set: joining befriends every set in the alliance ----------------


async def test_joining_an_alliance_befriends_its_secondary_members(
    client: AsyncClient, db_session: AsyncSession
):
    """"Joining an alliance befriends its sets", and an alliance's sets are every
    membership, not only the sets holding it as primary."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    primary = await _post(client, h, "/api/v1/alliances/", {"universe_id": uni, "name": "Elm"})
    shared = await _post(client, h, "/api/v1/alliances/", {"universe_id": uni, "name": "Oak"})
    # In Oak only as its second alliance.
    elder = await _post(
        client,
        h,
        "/api/v1/sets/",
        {
            "universe_id": uni,
            "name": f"Elder {_uid()}",
            "alliance_ids": [primary["id"], shared["id"]],
        },
    )
    newcomer = await _post(
        client,
        h,
        "/api/v1/sets/",
        {"universe_id": uni, "name": f"New {_uid()}", "alliance_ids": [shared["id"]]},
    )
    got = (await client.get(f"/api/v1/sets/{newcomer['id']}?universe_id={uni}", headers=h)).json()
    assert elder["id"] in got["friend_ids"]

    # The same through an edit.
    late = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Late {_uid()}"})
    resp = await client.patch(
        f"/api/v1/sets/{late['id']}?universe_id={uni}",
        json={"alliance_ids": [shared["id"]]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    got = (await client.get(f"/api/v1/sets/{late['id']}?universe_id={uni}", headers=h)).json()
    assert elder["id"] in got["friend_ids"]
