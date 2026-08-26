"""API integration tests for member incarceration spells.

The interesting field is `to_date`. It is what makes a spell *historical*, and
the whole point of separating it from `max_discharge_date` is that the latter is
a forecast: once a spell has actually ended, its projected release dates are
facts that were overtaken, and nothing may keep announcing them.
"""

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


def _ymd(year: int, month: int, day: int) -> dict:
    return {"year": year, "month": month, "day": day, "precision": "YMD"}


class _Fixture:
    """Token, universe and member, so each test starts from a clean member."""

    def __init__(self, token: str, universe_id: str, member_id: str):
        self.token = token
        self.universe_id = universe_id
        self.member_id = member_id

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}


async def _setup(client: AsyncClient, session: AsyncSession) -> _Fixture:
    token = await _admin_token(client, session)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers=headers,
    )
    assert resp.status_code == 201
    universe_id = resp.json()["id"]
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": f"Subject {_uid()}", "status": "LOCKED"},
        headers=headers,
    )
    assert resp.status_code == 201
    return _Fixture(token, universe_id, resp.json()["id"])


async def _create_spell(client: AsyncClient, f: _Fixture, **body) -> dict:
    resp = await client.post(
        f"/api/v1/members/{f.member_id}/incarcerations?universe_id={f.universe_id}",
        json=body,
        headers=f.headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_spell_round_trips_its_end_date(client: AsyncClient, db_session: AsyncSession):
    f = await _setup(client, db_session)
    spell = await _create_spell(
        client,
        f,
        from_date=_ymd(2011, 3, 4),
        to_date=_ymd(2015, 8, 20),
        case_id="11002233-FC",
    )
    assert spell["from_date"]["year"] == 2011
    assert spell["to_date"] == {
        "year": 2015,
        "month": 8,
        "day": 20,
        "precision": "YMD",
        "approx": False,
        "circa_text": None,
    }

    resp = await client.get(
        f"/api/v1/members/{f.member_id}/incarcerations?universe_id={f.universe_id}",
        headers=f.headers,
    )
    assert resp.status_code == 200
    assert resp.json()[0]["to_date"]["day"] == 20


async def test_an_ongoing_spell_has_no_end_date(client: AsyncClient, db_session: AsyncSession):
    f = await _setup(client, db_session)
    spell = await _create_spell(client, f, from_date=_ymd(2021, 1, 12))
    assert spell["to_date"] is None


async def test_a_life_term_still_records_when_it_ended(
    client: AsyncClient, db_session: AsyncSession
):
    """Commutation and death both end a life sentence; `to_date` is not gated on it."""
    f = await _setup(client, db_session)
    spell = await _create_spell(
        client,
        f,
        from_date=_ymd(1998, 4, 1),
        to_date=_ymd(2020, 12, 24),
        life_sentence=True,
    )
    assert spell["life_sentence"] is True
    assert spell["to_date"]["year"] == 2020
    # A life term has no release dates, whatever else is sent.
    assert spell["earliest_release_date"] is None
    assert spell["max_discharge_date"] is None


async def test_patching_notes_does_not_wipe_the_end_date(
    client: AsyncClient, db_session: AsyncSession
):
    """The trap `from_date` was already guarded against: unsent is not cleared."""
    f = await _setup(client, db_session)
    spell = await _create_spell(client, f, from_date=_ymd(2011, 3, 4), to_date=_ymd(2015, 8, 20))
    resp = await client.patch(
        f"/api/v1/members/{f.member_id}/incarcerations/{spell['id']}?universe_id={f.universe_id}",
        json={"notes": "County: Wayne"},
        headers=f.headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["to_date"]["year"] == 2015
    assert resp.json()["notes"] == "County: Wayne"


async def test_an_end_date_can_be_cleared_explicitly(client: AsyncClient, db_session: AsyncSession):
    f = await _setup(client, db_session)
    spell = await _create_spell(client, f, to_date=_ymd(2015, 8, 20))
    resp = await client.patch(
        f"/api/v1/members/{f.member_id}/incarcerations/{spell['id']}?universe_id={f.universe_id}",
        json={"to_date": None},
        headers=f.headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["to_date"] is None


async def test_a_facility_can_be_cleared(client: AsyncClient, db_session: AsyncSession):
    """A wrongly-entered facility has to be removable.

    The edit form sends null for a blanked field, so treating null as "not
    mentioned" made these three fields write-once in practice.
    """
    f = await _setup(client, db_session)
    spell = await _create_spell(client, f, facility="St. Louis Correctional Facility")
    resp = await client.patch(
        f"/api/v1/members/{f.member_id}/incarcerations/{spell['id']}?universe_id={f.universe_id}",
        json={"facility": None},
        headers=f.headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["facility"] is None


async def test_a_patch_that_omits_a_field_leaves_it_alone(
    client: AsyncClient, db_session: AsyncSession
):
    """The other half of the same rule: unsent is not cleared."""
    f = await _setup(client, db_session)
    spell = await _create_spell(
        client, f, facility="St. Louis Correctional Facility", case_id="15000121-01-FC", notes="x"
    )
    resp = await client.patch(
        f"/api/v1/members/{f.member_id}/incarcerations/{spell['id']}?universe_id={f.universe_id}",
        json={"notes": "y"},
        headers=f.headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["notes"] == "y"
    assert body["facility"] == "St. Louis Correctional Facility"
    assert body["case_id"] == "15000121-01-FC"


async def test_release_events_list_an_ongoing_spell(client: AsyncClient, db_session: AsyncSession):
    f = await _setup(client, db_session)
    spell = await _create_spell(
        client, f, from_date=_ymd(2021, 1, 12), max_discharge_date=_ymd(2046, 4, 15)
    )
    resp = await client.get(
        f"/api/v1/members/release-events?universe_id={f.universe_id}&year=2046",
        headers=f.headers,
    )
    assert resp.status_code == 200, resp.text
    assert [e["spell_id"] for e in resp.json()] == [spell["id"]]


async def test_release_events_skip_a_spell_that_already_ended(
    client: AsyncClient, db_session: AsyncSession
):
    """A projected 2046 release on a spell served out in 2015 is not an event.

    Without this the calendar would announce a max discharge for someone who
    has been out for years.
    """
    f = await _setup(client, db_session)
    await _create_spell(
        client,
        f,
        from_date=_ymd(2011, 3, 4),
        to_date=_ymd(2015, 8, 20),
        max_discharge_date=_ymd(2046, 4, 15),
    )
    resp = await client.get(
        f"/api/v1/members/release-events?universe_id={f.universe_id}&year=2046",
        headers=f.headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []
