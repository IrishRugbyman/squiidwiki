"""API integration tests for the /api/v1/incidents/ vertical slice."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _ymd(fuzzy: dict | None) -> tuple | None:
    """(year, month, day) from a FuzzyDate payload, ignoring precision/approx/circa."""
    if fuzzy is None:
        return None
    return (fuzzy["year"], fuzzy["month"], fuzzy["day"])


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
        await client.get(
            f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}", headers=headers
        )
    ).json()
    shooter = next(p for p in detail["participants"] if p["member_id"] == shooter_id)
    assert shooter["role"] == "SHOOTER"
    assert shooter["acquitted"] is True
    assert shooter["notes"] == "Acquitted at trial."

    # The victim is untouched: being shot is not a claim anyone can be acquitted of.
    victim = next(p for p in detail["participants"] if p["member_id"] == victim_id)
    assert victim["acquitted"] is False


async def test_incident_edit_does_not_overwrite_a_hand_entered_date_of_death(
    client: AsyncClient, db_session: AsyncSession
):
    """
    A member shot on one date and dying on a later one keeps the later date.

    Expected values come from the domain rule, not from running the sync: being
    shot in July and dying in August are two events, so a date_of_death a human
    put there must survive any number of edits to the shooting. The first half
    of the test - the auto-fill on create - is what proves the second half can
    fail, since it shows the sync does write when nobody has said otherwise.
    """
    token = await _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    universe_id = await _make_universe(client, token)
    victim_id = await _make_member(client, token, universe_id, "Shot in July")

    shooting = {"year": 2014, "month": 7, "day": 14, "precision": "YMD", "approx": False}
    died = {"year": 2014, "month": 8, "day": 3, "precision": "YMD", "approx": False}

    incident = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": universe_id,
                "type": "MURDER",
                "date": shooting,
                "participants": [{"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"}],
            },
            headers=headers,
        )
    ).json()

    async def member_date() -> dict | None:
        resp = await client.get(
            f"/api/v1/members/{victim_id}?universe_id={universe_id}", headers=headers
        )
        assert resp.status_code == 200
        return resp.json()["date_of_death"]

    # Nobody has said otherwise yet, so the incident date is the best guess.
    assert (await member_date())["day"] == 14

    # A human records the real date of death.
    resp = await client.patch(
        f"/api/v1/members/{victim_id}?universe_id={universe_id}",
        json={"date_of_death": died},
        headers=headers,
    )
    assert resp.status_code == 200

    # Any later edit of the incident must leave that alone.
    resp = await client.patch(
        f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}",
        json={
            "location_text": "corrected address",
            "participants": [{"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"}],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert _ymd(await member_date()) == _ymd(died), (
        "an incident edit overwrote a hand-entered date of death"
    )

    # And correcting the shooting date must not resurrect the overwrite either.
    resp = await client.patch(
        f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}",
        json={
            "date": {"year": 2014, "month": 7, "day": 15, "precision": "YMD", "approx": False},
            "participants": [{"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"}],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert _ymd(await member_date()) == _ymd(died)


async def test_incident_date_correction_still_propagates_when_untouched(
    client: AsyncClient, db_session: AsyncSession
):
    """
    The other half of the rule: a date the sync wrote itself is still its own.

    Nobody has hand-entered anything here, so correcting the incident date must
    carry through to the member. Without this the fix above would trade one bug
    for another - a member left on a date the incident no longer claims.
    """
    token = await _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    universe_id = await _make_universe(client, token)
    victim_id = await _make_member(client, token, universe_id, "Date was wrong")

    incident = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": universe_id,
                "type": "MURDER",
                "date": {"year": 2019, "month": 3, "day": 2, "precision": "YMD", "approx": False},
                "participants": [{"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"}],
            },
            headers=headers,
        )
    ).json()

    corrected = {"year": 2019, "month": 3, "day": 9, "precision": "YMD", "approx": False}
    resp = await client.patch(
        f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}",
        json={
            "date": corrected,
            "participants": [{"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"}],
        },
        headers=headers,
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/members/{victim_id}?universe_id={universe_id}", headers=headers
    )
    assert _ymd(resp.json()["date_of_death"]) == _ymd(corrected)


async def test_dating_an_undated_killing_fills_an_unknown_date_of_death(
    client: AsyncClient, db_session: AsyncSession
):
    """
    An UNKNOWN date of death is a blank, not a hand-entered date.

    A member killed in an undated incident, whose record carries the member
    form's placeholder ``{"precision": "UNKNOWN"}``, must take the date the
    incident is later given. Expected value from the domain rule: the only date
    anyone has for the death is the incident's. The hand-entered-date test above
    is the counterweight - a date with a year still wins.
    """
    token = await _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    universe_id = await _make_universe(client, token)
    victim_id = await _make_member(client, token, universe_id, "Undated at first")
    killed = [{"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"}]

    resp = await client.patch(
        f"/api/v1/members/{victim_id}?universe_id={universe_id}",
        json={"status": "DEAD", "date_of_death": {"precision": "UNKNOWN", "approx": False}},
        headers=headers,
    )
    assert resp.status_code == 200
    incident = (
        await client.post(
            "/api/v1/incidents/",
            json={"universe_id": universe_id, "type": "MURDER", "participants": killed},
            headers=headers,
        )
    ).json()

    dated = {"year": 2020, "month": 6, "day": 23, "precision": "YMD", "approx": False}
    resp = await client.patch(
        f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}",
        json={"date": dated, "participants": killed},
        headers=headers,
    )
    assert resp.status_code == 200

    member = (
        await client.get(f"/api/v1/members/{victim_id}?universe_id={universe_id}", headers=headers)
    ).json()
    assert _ymd(member["date_of_death"]) == _ymd(dated)


async def test_date_only_incident_edit_still_dates_the_death(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Correcting only an incident's date carries through to its dead.

    A PATCH that sends ``date`` without ``participants`` leaves the participants
    as they are, and they include a KILLED member whose date of death the sync
    wrote itself, so the correction must reach that member exactly as it would
    if the same participants had been re-sent.
    """
    token = await _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    universe_id = await _make_universe(client, token)
    victim_id = await _make_member(client, token, universe_id, "Date only")

    incident = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": universe_id,
                "type": "MURDER",
                "date": {"year": 2020, "month": 6, "day": 24, "precision": "YMD", "approx": False},
                "participants": [{"member_id": victim_id, "role": "VICTIM", "outcome": "KILLED"}],
            },
            headers=headers,
        )
    ).json()

    corrected = {"year": 2020, "month": 6, "day": 23, "precision": "YMD", "approx": False}
    resp = await client.patch(
        f"/api/v1/incidents/{incident['id']}?universe_id={universe_id}",
        json={"date": corrected},
        headers=headers,
    )
    assert resp.status_code == 200

    member = (
        await client.get(f"/api/v1/members/{victim_id}?universe_id={universe_id}", headers=headers)
    ).json()
    assert _ymd(member["date_of_death"]) == _ymd(corrected)


async def test_incident_detail_carries_participant_set_status_and_sources(
    client: AsyncClient, db_session: AsyncSession
):
    """The detail payload draws the page alone: each participant's status and
    current set, and the cited sources, so the page need not load the universe."""
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    async def post(path: str, body: dict) -> str:
        resp = await client.post(path, json={"universe_id": universe_id, **body}, headers=auth)
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    set_id = await post("/api/v1/sets/", {"name": f"Set {_uid()}"})
    shooter = await post(
        "/api/v1/members/",
        {
            "nickname": "Shooter",
            "status": "LOCKED",
            "affiliations": [{"set_id": set_id, "is_primary": True}],
        },
    )
    victim = await post("/api/v1/members/", {"nickname": "Victim"})
    source = await post(
        "/api/v1/sources/",
        {
            "url": "https://example.com/a",
            "title": "Article",
            "publication": "Daily",
            "reliability": "HIGH",
        },
    )
    incident = await post(
        "/api/v1/incidents/",
        {
            "type": "SHOOTING",
            "participants": [
                {"member_id": shooter, "role": "SHOOTER", "outcome": "UNHARMED"},
                {"member_id": victim, "role": "VICTIM", "outcome": "INJURED"},
            ],
            "source_ids": [source],
        },
    )

    resp = await client.get(
        f"/api/v1/incidents/{incident}", params={"universe_id": universe_id}, headers=auth
    )
    assert resp.status_code == 200
    body = resp.json()
    by_member = {p["member_id"]: p for p in body["participants"]}
    assert by_member[shooter]["member_status"] == "LOCKED"
    assert by_member[shooter]["set_id"] == set_id
    assert by_member[victim]["set_id"] is None
    assert [s["id"] for s in body["sources"]] == [source]
    assert body["sources"][0]["publication"] == "Daily"
    assert body["sources"][0]["reliability"] == "HIGH"
