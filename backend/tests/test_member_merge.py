"""POST /members/{keep}/merge: fold a duplicate record into the canonical one.

Every name here is invented; nothing in this repository may name a person.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")

attach_audit_listeners()

Y = lambda y: {"year": y, "precision": "Y", "approx": False}  # noqa: E731


def _uid() -> str:
    return uuid.uuid4().hex[:8]


class World:
    def __init__(self, client: AsyncClient, headers: dict, uni: str):
        self.c, self.h, self.uni = client, headers, uni

    async def post(self, path: str, body: dict) -> dict:
        resp = await self.c.post(path, json={"universe_id": self.uni, **body}, headers=self.h)
        assert resp.status_code in (200, 201), resp.text
        return resp.json()

    async def get(self, path: str):
        sep = "&" if "?" in path else "?"
        return await self.c.get(f"{path}{sep}universe_id={self.uni}", headers=self.h)

    async def member(self, **body) -> dict:
        return await self.post("/api/v1/members/", body)

    async def merge(self, keep: str, drop: str, **body):
        return await self.c.post(
            f"/api/v1/members/{keep}/merge?universe_id={self.uni}",
            json={"drop_id": drop, **body},
            headers=self.h,
        )


async def _world(client: AsyncClient, session: AsyncSession, role=GlobalRole.ADMIN) -> World:
    email = f"u_{_uid()}@example.com"
    await create_user(session, email, "pass1234", role)
    token = (await client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})).json()[
        "access_token"
    ]
    h = {"Authorization": f"Bearer {token}"}
    if role == GlobalRole.ADMIN:
        uni = (
            await client.post(
                "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=h
            )
        ).json()["id"]
    else:
        uni = str(uuid.uuid4())
    return World(client, h, uni)


async def test_merge_moves_everything_and_deletes_the_duplicate(
    client: AsyncClient, db_session: AsyncSession
):
    w = await _world(client, db_session)
    set_a = await w.post("/api/v1/sets/", {"name": f"Lanternway {_uid()}"})
    set_b = await w.post("/api/v1/sets/", {"name": f"Copperfield {_uid()}"})
    src = await w.post(
        "/api/v1/sources/", {"url": "https://example.com/x", "title": "Digest", "reliability": "HIGH"}
    )
    keep = await w.member(nickname="Orrel", affiliations=[{"set_id": set_a["id"], "is_primary": True}])
    drop = await w.member(
        nickname="Orrell",
        legal_name="Tobin Vask",
        biography="Ran the dice game behind the laundromat.",
        dob=Y(1994),
        affiliations=[{"set_id": set_b["id"], "is_primary": True}],
        source_ids=[src["id"]],
    )
    inc = await w.post(
        "/api/v1/incidents/",
        {"type": "SHOOTING", "date": Y(2019), "participants": [{"member_id": drop["id"], "role": "SHOOTER"}]},
    )

    resp = await w.merge(keep["id"], drop["id"])
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert report["moved"]["incident_participations"] == 1
    assert report["moved"]["set_spells"] == 1
    assert report["moved"]["sources"] == 1
    assert report["conflicts"] == []

    assert (await w.get(f"/api/v1/members/{drop['id']}")).status_code == 404
    got = (await w.get(f"/api/v1/members/{keep['id']}")).json()
    assert got["nickname"] == "Orrel"  # kept value stands
    assert got["legal_name"] == "Tobin Vask"  # empty on keep, filled from drop
    assert got["biography"] == "Ran the dice game behind the laundromat."
    assert got["dob"]["year"] == 1994
    assert "Orrell" in got["aliases"]  # the old spelling still finds the record
    assert {a["set_id"] for a in got["affiliations"]} == {set_a["id"], set_b["id"]}
    assert [a["set_id"] for a in got["affiliations"] if a["is_primary"]] == [set_a["id"]]
    assert got["source_ids"] == [src["id"]]
    parts = (await w.get(f"/api/v1/incidents/{inc['id']}")).json()["participants"]
    assert [p["member_id"] for p in parts] == [keep["id"]]


async def test_dry_run_reports_and_changes_nothing(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Brisk")
    drop = await w.member(nickname="Briskk", legal_name="Ansel Rook")
    resp = await w.merge(keep["id"], drop["id"], dry_run=True)
    assert resp.status_code == 200, resp.text
    assert resp.json()["dry_run"] is True
    assert {f["field"] for f in resp.json()["fields"]} >= {"nickname", "legal_name"}
    assert (await w.get(f"/api/v1/members/{drop['id']}")).status_code == 200
    assert (await w.get(f"/api/v1/members/{keep['id']}")).json()["legal_name"] is None


async def test_prefer_takes_the_dropped_value(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Quell", biography="Short.")
    drop = await w.member(nickname="Quel", biography="The longer, better account.")
    resp = await w.merge(keep["id"], drop["id"], prefer=["biography"])
    assert resp.status_code == 200, resp.text
    assert (await w.get(f"/api/v1/members/{keep['id']}")).json()["biography"] == "The longer, better account."


async def test_same_incident_and_same_open_set_are_conflicts(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    s = await w.post("/api/v1/sets/", {"name": f"Harrowgate {_uid()}"})
    keep = await w.member(nickname="Vane", affiliations=[{"set_id": s["id"], "is_primary": True}])
    drop = await w.member(nickname="Vain", affiliations=[{"set_id": s["id"], "is_primary": True}])
    inc = await w.post(
        "/api/v1/incidents/",
        {
            "type": "SHOOTING",
            "date": Y(2020),
            "participants": [
                {"member_id": keep["id"], "role": "SHOOTER"},
                {"member_id": drop["id"], "role": "ASSISTED"},
            ],
        },
    )
    report = (await w.merge(keep["id"], drop["id"])).json()
    assert sorted(c["kind"] for c in report["conflicts"]) == ["incident_participant", "set_spell"]
    parts = (await w.get(f"/api/v1/incidents/{inc['id']}")).json()["participants"]
    assert [(p["member_id"], p["role"]) for p in parts] == [(keep["id"], "SHOOTER")]
    got = (await w.get(f"/api/v1/members/{keep['id']}")).json()
    assert len(got["affiliations"]) == 1


async def test_family_is_repointed_and_self_links_dropped(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Ashby")
    drop = await w.member(nickname="Ashbey")
    parent = await w.member(nickname="Elder")
    # drop is the parent's child, and (wrongly) keep's sibling.
    upd = await w.c.patch(
        f"/api/v1/members/{drop['id']}?universe_id={w.uni}",
        json={"family": {"parent": [parent["id"]], "sibling": [keep["id"]]}},
        headers=w.h,
    )
    assert upd.status_code == 200, upd.text
    assert (await w.merge(keep["id"], drop["id"])).status_code == 200
    got = (await w.get(f"/api/v1/members/{keep['id']}")).json()
    assert got["family"] == {"parent": [parent["id"]]}
    elder = (await w.get(f"/api/v1/members/{parent['id']}")).json()
    assert elder["family"] == {"child": [keep["id"]]}


async def test_killed_on_the_dropped_record_is_flagged(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Corvin", status="FREE")
    drop = await w.member(nickname="Korvin")
    await w.post(
        "/api/v1/incidents/",
        {
            "type": "MURDER",
            "date": Y(2018),
            "participants": [{"member_id": drop["id"], "role": "VICTIM", "outcome": "KILLED"}],
        },
    )
    report = (await w.merge(keep["id"], drop["id"])).json()
    assert [c["kind"] for c in report["conflicts"]] == ["status"]


async def test_merge_shows_in_history(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Thistle")
    drop = await w.member(nickname="Thistel")
    assert (await w.merge(keep["id"], drop["id"])).status_code == 200
    items = (await w.get(f"/api/v1/history/member/{keep['id']}")).json()["items"]
    merged = [i for i in items if i.get("link") == "merged"]
    assert len(merged) == 1
    assert merged[0]["added"][0]["display_name"] == "Thistel"


async def test_merge_guards(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    a = await w.member(nickname="Solo")
    b = await w.member(nickname="Duo")
    assert (await w.merge(a["id"], a["id"])).status_code == 422
    assert (await w.merge(a["id"], b["id"], prefer=["slug"])).status_code == 422
    assert (await w.merge(a["id"], str(uuid.uuid4()))).status_code == 404
    other = await _world(client, db_session)
    stranger = await other.member(nickname="Elsewhere")
    assert (await w.merge(a["id"], stranger["id"])).status_code == 404
    user = await _world(client, db_session, role=GlobalRole.USER)
    resp = await client.post(
        f"/api/v1/members/{a['id']}/merge?universe_id={w.uni}", json={"drop_id": b["id"]}, headers=user.h
    )
    assert resp.status_code == 403
