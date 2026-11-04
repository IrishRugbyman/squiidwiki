"""GET /admin/anomalies: rows in one universe that contradict each other.

Each check gets a positive case (the contradiction is reported) and a negative
case (a near miss that must stay silent), each in a universe of its own so the
counts are exact.
"""

import datetime
import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole
from app.crud.anomalies import CHECKS, fuzzy_range, strictly_before


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def Y(year: int, approx: bool = False) -> dict:
    return {"year": year, "precision": "Y", "approx": approx}


def YM(year: int, month: int) -> dict:
    return {"year": year, "month": month, "precision": "YM"}


def YMD(year: int, month: int, day: int) -> dict:
    return {"year": year, "month": month, "day": day, "precision": "YMD"}


class World:
    """One fresh universe and an admin to write into it."""

    def __init__(self, client: AsyncClient, h: dict, uni: str):
        self.client, self.h, self.uni = client, h, uni

    @classmethod
    async def make(cls, client: AsyncClient, session: AsyncSession) -> "World":
        email = f"anom_{_uid()}@example.com"
        await create_user(session, email, "pass1234", GlobalRole.ADMIN)
        resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "pass1234"}
        )
        h = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        resp = await client.post(
            "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=h
        )
        assert resp.status_code == 201, resp.text
        return cls(client, h, resp.json()["id"])

    async def post(self, path: str, body: dict) -> dict:
        resp = await self.client.post(path, json={"universe_id": self.uni, **body}, headers=self.h)
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def patch(self, path: str, body: dict) -> dict:
        resp = await self.client.patch(f"{path}?universe_id={self.uni}", json=body, headers=self.h)
        assert resp.status_code == 200, resp.text
        return resp.json()

    async def member(self, **body) -> dict:
        return await self.post("/api/v1/members/", {"nickname": f"Member {_uid()}", **body})

    async def set(self, **body) -> dict:
        return await self.post("/api/v1/sets/", {"name": f"Test Set {_uid()}", **body})

    async def source(self) -> dict:
        return await self.post(
            "/api/v1/sources/", {"url": f"https://example.com/{_uid()}", "title": "Test Article"}
        )

    async def cite(self, source: dict, entity_type: str, record: dict) -> dict:
        return await self.post(
            f"/api/v1/citations/?universe_id={self.uni}",
            {"source_id": source["id"], "entity_type": entity_type, "entity_id": record["id"]},
        )

    async def incident(self, date: dict | None, participants=(), **body) -> dict:
        return await self.post(
            "/api/v1/incidents/",
            {"type": "SHOOTING", "date": date, "participants": list(participants), **body},
        )

    async def findings(self, kind: str) -> list[dict]:
        resp = await self.client.get(
            f"/api/v1/admin/anomalies?universe_id={self.uni}&kind={kind}", headers=self.h
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert [c["kind"] for c in body["checks"]] == [kind]
        assert body["checks"][0]["count"] == len(body["items"])
        return body["items"]


def p(member: dict, role: str = "VICTIM", outcome: str = "UNKNOWN") -> dict:
    return {"member_id": member["id"], "role": role, "outcome": outcome}


# --- FuzzyDate spans --------------------------------------------------------


def test_fuzzy_comparison_respects_precision():
    assert not strictly_before(YM(2021, 3), Y(2021))  # same year: ambiguous
    assert not strictly_before(Y(2021), YMD(2021, 12, 31))
    assert strictly_before(Y(2021), Y(2022))
    assert strictly_before(YM(2021, 3), YM(2021, 4))
    assert not strictly_before(Y(2021, approx=True), Y(2022))  # circa widens it
    assert not strictly_before(None, Y(2022))
    assert not strictly_before({"precision": "UNKNOWN"}, Y(2022))
    assert fuzzy_range(YM(2024, 2)) == (datetime.date(2024, 2, 1), datetime.date(2024, 2, 29))


# --- endpoint ---------------------------------------------------------------


async def test_report_lists_every_check_and_is_admin_only(
    client: AsyncClient, db_session: AsyncSession
):
    w = await World.make(client, db_session)
    resp = await client.get(f"/api/v1/admin/anomalies?universe_id={w.uni}", headers=w.h)
    assert resp.status_code == 200
    assert [c["kind"] for c in resp.json()["checks"]] == list(CHECKS)

    resp = await client.get(
        f"/api/v1/admin/anomalies?universe_id={w.uni}&kind=nonsense", headers=w.h
    )
    assert resp.status_code == 422
    resp = await client.get(f"/api/v1/admin/anomalies?universe_id={uuid.uuid4()}", headers=w.h)
    assert resp.status_code == 404

    email = f"user_{_uid()}@example.com"
    await create_user(db_session, email, "pass1234", GlobalRole.USER)
    tok = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    ).json()["access_token"]
    resp = await client.get(
        f"/api/v1/admin/anomalies?universe_id={w.uni}", headers={"Authorization": f"Bearer {tok}"}
    )
    assert resp.status_code == 403


async def test_set_member_unsourced(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    s = await w.set()
    bare = await w.member(affiliations=[{"set_id": s["id"]}])
    src = await w.source()
    # Cited directly.
    cited = await w.member(affiliations=[{"set_id": s["id"]}])
    await w.cite(src, "member", cited)
    # Cited through an incident they are in.
    via = await w.member(affiliations=[{"set_id": s["id"]}])
    await w.cite(src, "incident", await w.incident(Y(2020), [p(via)]))
    # Not in a set at all.
    await w.member()

    found = await w.findings("set_member_unsourced")
    assert [f["entity_id"] for f in found] == [bare["id"]]
    assert found[0]["related_id"] == s["id"]
    assert found[0]["display_name"] == bare["nickname"]


async def test_set_member_unsourced_ignores_reserved_sets(
    client: AsyncClient, db_session: AsyncSession
):
    w = await World.make(client, db_session)
    sets = (await client.get(f"/api/v1/sets/?universe_id={w.uni}", headers=w.h)).json()["items"]
    unknown = next(s for s in sets if s["name"] == "Unknown")
    await w.member(affiliations=[{"set_id": unknown["id"]}])
    assert await w.findings("set_member_unsourced") == []


async def test_dead_without_death_record(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    bad = await w.member(status="DEAD")
    await w.member(status="DEAD", date_of_death=Y(2019))
    await w.member(status="FREE")
    victim = await w.member()
    await w.incident(Y(2020), [p(victim, outcome="KILLED")])  # death sync links it

    found = await w.findings("dead_without_death_record")
    assert [f["entity_id"] for f in found] == [bad["id"]]


async def test_incident_after_death(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    dead = await w.member()
    await w.incident(Y(2021), [p(dead, outcome="KILLED")])
    later = await w.incident(Y(2023), [p(dead, role="SHOOTER")])

    # Same year at different precision: ambiguous, so silent.
    close = await w.member()
    await w.incident(Y(2021), [p(close, outcome="KILLED")])
    await w.incident(YM(2021, 6), [p(close, role="SHOOTER")])
    # An earlier incident is fine.
    before = await w.member()
    await w.incident(Y(2019), [p(before, role="SHOOTER")])
    await w.incident(Y(2021), [p(before, outcome="KILLED")])

    found = await w.findings("incident_after_death")
    assert [(f["entity_id"], f["related_id"]) for f in found] == [(dead["id"], later["id"])]


async def test_incident_after_date_of_death(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    m = await w.member(status="DEAD", date_of_death=YMD(2020, 5, 1))
    inc = await w.incident(YMD(2020, 6, 1), [p(m)])
    ok = await w.member(status="DEAD", date_of_death=YMD(2020, 5, 1))
    await w.incident(YM(2020, 5), [p(ok)])  # could be the same day
    found = await w.findings("incident_after_death")
    assert [(f["entity_id"], f["related_id"]) for f in found] == [(m["id"], inc["id"])]


async def test_incident_before_birth(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    young = await w.member(dob=Y(2005))
    inc = await w.incident(Y(2003), [p(young)])
    edge = await w.member(dob=YM(2005, 6))
    await w.incident(Y(2005), [p(edge)])  # the year of birth itself: ambiguous
    nodob = await w.member()
    await w.incident(Y(1990), [p(nodob)])

    found = await w.findings("incident_before_birth")
    assert [(f["entity_id"], f["related_id"]) for f in found] == [(young["id"], inc["id"])]


async def test_extinct_set_recent_incident(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    this_year = datetime.date.today().year
    extinct = await w.set(status="EXTINCT")
    old_extinct = await w.set(status="EXTINCT")
    active = await w.set()

    recent = await w.incident(
        Y(this_year), set_participants=[{"set_id": extinct["id"], "role": "SHOOTER"}]
    )
    await w.incident(Y(2010), set_participants=[{"set_id": old_extinct["id"], "role": "SHOOTER"}])
    await w.incident(Y(this_year), set_participants=[{"set_id": active["id"], "role": "SHOOTER"}])
    # A shooter whose primary set is extinct also counts; a victim does not.
    shooter = await w.member(affiliations=[{"set_id": old_extinct["id"], "is_primary": True}])
    via = await w.incident(Y(this_year), [p(shooter, role="SHOOTER")])
    victim = await w.member(affiliations=[{"set_id": old_extinct["id"], "is_primary": True}])
    await w.incident(Y(this_year), [p(victim, role="VICTIM")])

    found = await w.findings("extinct_set_recent_incident")
    assert sorted((f["entity_id"], f["related_id"]) for f in found) == sorted(
        [(extinct["id"], recent["id"]), (old_extinct["id"], via["id"])]
    )
    assert all(f["entity_type"] == "set" for f in found)


async def test_death_incident_but_not_dead_and_killed_but_not_dead(
    client: AsyncClient, db_session: AsyncSession
):
    w = await World.make(client, db_session)
    revived = await w.member()
    inc = await w.incident(Y(2021), [p(revived, outcome="KILLED")])
    # Half an un-kill: the status was put back, the outcome was not.
    await w.patch(f"/api/v1/members/{revived['id']}", {"status": "FREE"})
    dead = await w.member()
    await w.incident(Y(2021), [p(dead, outcome="KILLED")])  # consistent

    found = await w.findings("death_incident_but_not_dead")
    assert [(f["entity_id"], f["related_id"]) for f in found] == [(revived["id"], inc["id"])]
    found = await w.findings("killed_but_not_dead")
    assert [(f["entity_id"], f["related_id"]) for f in found] == [(revived["id"], inc["id"])]


async def test_killed_twice(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    twice = await w.member()
    await w.incident(Y(2020), [p(twice, outcome="KILLED")])
    await w.incident(Y(2021), [p(twice, outcome="KILLED")])
    once = await w.member()
    await w.incident(Y(2020), [p(once, outcome="INJURED")])
    await w.incident(Y(2021), [p(once, outcome="KILLED")])

    found = await w.findings("killed_twice")
    assert [f["entity_id"] for f in found] == [twice["id"]]


async def test_death_before_birth(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    bad = await w.member(status="DEAD", dob=Y(2000), date_of_death=Y(1999))
    await w.member(status="DEAD", dob=YM(2000, 3), date_of_death=Y(2000))
    found = await w.findings("death_before_birth")
    assert [f["entity_id"] for f in found] == [bad["id"]]


async def test_spell_ends_before_start(client: AsyncClient, db_session: AsyncSession):
    w = await World.make(client, db_session)
    s = await w.set()

    async def spell(from_date: dict, until_date: dict) -> dict:
        m = await w.member(affiliations=[{"set_id": s["id"], "from_date": from_date}])
        got = (
            await client.get(f"/api/v1/members/{m['id']}?universe_id={w.uni}", headers=w.h)
        ).json()
        aff = got["affiliations"][0]["id"]
        resp = await client.post(
            f"/api/v1/members/{m['id']}/affiliations/{aff}/end?universe_id={w.uni}",
            json={"until_date": until_date},
            headers=w.h,
        )
        assert resp.status_code == 204, resp.text
        return m

    bad = await spell(Y(2020), Y(2018))
    await spell(YM(2020, 5), Y(2020))
    found = await w.findings("spell_ends_before_start")
    assert [f["entity_id"] for f in found] == [bad["id"]]
