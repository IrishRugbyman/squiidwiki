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
    """Joining an alliance befriends its sets (CLAUDE.md), and an alliance's sets
    are every membership, not only the sets holding it as primary."""
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


# --- join-table audit ---------------------------------------------------------


async def test_alliance_gang_and_territory_changes_reach_history(
    client: AsyncClient, db_session: AsyncSession
):
    """Every join-table sync calls record_link_change, so an alliance's gangs
    and territories show on its History tab like a set's gangs do."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    gang = await _post(client, h, "/api/v1/gangs/", {"universe_id": uni, "name": f"G {_uid()}"})
    city = await _post(
        client, h, "/api/v1/municipalities/", {"universe_id": uni, "name": f"City {_uid()}"}
    )
    a = await _post(client, h, "/api/v1/alliances/", {"universe_id": uni, "name": f"A {_uid()}"})
    resp = await client.patch(
        f"/api/v1/alliances/{a['id']}?universe_id={uni}",
        json={"gang_ids": [gang["id"]], "territory_ids": [city["id"]]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    page = await _history(client, h, uni, "alliance", a["id"])
    by_link = {e["link"]: e for e in page["items"] if e["link"]}
    assert [r["gang_id"] for r in by_link["gangs"]["added"]] == [gang["id"]]
    assert [r["municipality_id"] for r in by_link["territories"]["added"]] == [city["id"]]


async def test_set_territory_changes_reach_history(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    city = await _post(
        client, h, "/api/v1/municipalities/", {"universe_id": uni, "name": f"City {_uid()}"}
    )
    area = await _post(
        client,
        h,
        "/api/v1/municipalities/",
        {"universe_id": uni, "name": f"Area {_uid()}", "parent_id": city["id"]},
    )
    s = await _post(
        client,
        h,
        "/api/v1/sets/",
        {"universe_id": uni, "name": f"Crew {_uid()}", "municipality_id": city["id"]},
    )
    resp = await client.patch(
        f"/api/v1/sets/{s['id']}?universe_id={uni}",
        json={"territory_ids": [area["id"]]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    page = await _history(client, h, uni, "set", s["id"])
    links = [e for e in page["items"] if e["link"] == "territories"]
    assert len(links) == 1
    assert [r["municipality_id"] for r in links[0]["added"]] == [area["id"]]


# --- lookup-source uniqueness -------------------------------------------------


async def test_editing_a_source_url_into_a_lookup_system_is_a_409(
    client: AsyncClient, db_session: AsyncSession
):
    """The custody lookups are one source per universe
    (uq_source_universe_lookup_system). A create refuses a second one with 409
    lookup_source; an edit that turns another source's URL into one must too,
    rather than failing on the unique index."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    canonical = await _post(
        client,
        h,
        "/api/v1/sources/",
        {"universe_id": uni, "url": "https://www.bop.gov/inmateloc/", "title": "BOP locator"},
    )
    other = await _post(
        client,
        h,
        "/api/v1/sources/",
        {"universe_id": uni, "url": f"https://example.com/{_uid()}", "title": "Some page"},
    )
    resp = await client.patch(
        f"/api/v1/sources/{other['id']}?universe_id={uni}",
        json={"url": "https://www.bop.gov/inmateloc/?inmatenum=00000-000"},
        headers=h,
    )
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "lookup_source"
    assert resp.json()["existing_id"] == canonical["id"]

    # The lookup source itself may still change its own URL.
    resp = await client.patch(
        f"/api/v1/sources/{canonical['id']}?universe_id={uni}",
        json={"url": "https://www.bop.gov/inmateloc"},
        headers=h,
    )
    assert resp.status_code == 200, resp.text


# --- name variants ------------------------------------------------------------


async def test_blank_name_variant_is_refused(client: AsyncClient, db_session: AsyncSession):
    """A variant must fill at least one slot, and a slot holding only spaces is
    empty: it displays as "", which would make an unnamed set or alliance."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    for path in ("/api/v1/sets/", "/api/v1/alliances/"):
        resp = await client.post(
            path, json={"universe_id": uni, "name_variants": [{"name": "   "}]}, headers=h
        )
        assert resp.status_code == 422, (path, resp.text)


# --- un-kill ------------------------------------------------------------------


async def test_dropping_a_killed_outcome_only_unlinks_the_death(
    client: AsyncClient, db_session: AsyncSession
):
    """CLAUDE.md: "Reverting (un-kill) is never automatic". An edit that no longer has a
    member KILLED clears his death_incident_id, and only where it points at
    this incident. Status and date_of_death are his own to change, so a
    hand-corrected date survives."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    hand = {"year": 2016, "month": 8, "day": 3, "precision": "YMD", "approx": False}

    async def member(nickname: str) -> str:
        return (
            await _post(client, h, "/api/v1/members/", {"universe_id": uni, "nickname": nickname})
        )["id"]

    async def incident(*participants: dict) -> str:
        return (
            await _post(
                client,
                h,
                "/api/v1/incidents/",
                {
                    "universe_id": uni,
                    "type": "MURDER",
                    "date": {"year": 2016, "month": 7, "precision": "YM", "approx": False},
                    "participants": list(participants),
                },
            )
        )["id"]

    def killed(mid: str) -> dict:
        return {"member_id": mid, "role": "VICTIM", "outcome": "KILLED"}

    async def get(mid: str) -> dict:
        return (await client.get(f"/api/v1/members/{mid}?universe_id={uni}", headers=h)).json()

    shot = await member("Review Shot")
    elsewhere = await member("Review Elsewhere")
    other = await incident(killed(elsewhere))
    a = await incident(killed(shot), killed(elsewhere))
    # The date of death corrected by hand after the shooting.
    resp = await client.patch(
        f"/api/v1/members/{shot}?universe_id={uni}", json={"date_of_death": hand}, headers=h
    )
    assert resp.status_code == 200, resp.text
    assert (await get(elsewhere))["death_incident_id"] == other

    resp = await client.patch(
        f"/api/v1/incidents/{a}?universe_id={uni}",
        json={
            "participants": [
                {"member_id": shot, "role": "VICTIM", "outcome": "INJURED"},
                {"member_id": elsewhere, "role": "VICTIM", "outcome": "INJURED"},
            ]
        },
        headers=h,
    )
    assert resp.status_code == 200, resp.text

    got = await get(shot)
    assert got["death_incident_id"] is None
    assert got["status"] == "DEAD"
    assert got["date_of_death"]["day"] == 3 and got["date_of_death"]["month"] == 8
    # Linked to another incident: not touched by this one.
    got = await get(elsewhere)
    assert got["death_incident_id"] == other
    assert got["status"] == "DEAD"

    # Removing the participant outright is the same un-link.
    again = await incident(killed(shot))
    assert (await get(shot))["death_incident_id"] == again
    resp = await client.patch(
        f"/api/v1/incidents/{again}?universe_id={uni}", json={"participants": []}, headers=h
    )
    assert resp.status_code == 200, resp.text
    got = await get(shot)
    assert got["death_incident_id"] is None
    assert got["status"] == "DEAD"
    assert got["date_of_death"]["day"] == 3
