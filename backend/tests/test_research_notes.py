"""Research notes: kinds and pins to members, sets, incidents and alliances.

Expected values are written from the rules: a new note is an INBOX note, `pins`
on update replaces the list, a pin must name an entity of the note's own
universe, and deleting a pinned entity drops the pin but never the note.
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


async def _setup(client: AsyncClient, session: AsyncSession) -> tuple[dict, str]:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers=headers,
    )
    assert resp.status_code == 201
    return headers, resp.json()["id"]


async def _make(client: AsyncClient, h: dict, path: str, body: dict) -> dict:
    resp = await client.post(f"/api/v1/{path}/", json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _entities(client: AsyncClient, h: dict, uid: str) -> dict:
    return {
        "member": await _make(client, h, "members", {"universe_id": uid, "nickname": "Pinny"}),
        "set": await _make(client, h, "sets", {"universe_id": uid, "name": "Pin Set"}),
        "incident": await _make(
            client,
            h,
            "incidents",
            {
                "universe_id": uid,
                "type": "SHOOTING",
                "location_text": "7 Mile & Gratiot",
                "date": {"year": 2022, "precision": "Y", "approx": False},
            },
        ),
        "alliance": await _make(client, h, "alliances", {"universe_id": uid, "name": "Pin Bloc"}),
    }


def _ref(kind: str, entity: dict) -> dict:
    return {"kind": kind, "id": entity["id"]}


async def _note(client: AsyncClient, h: dict, uid: str, **extra) -> dict:
    body = {"universe_id": uid, "title": f"Note {_uid()}", **extra}
    resp = await client.post("/api/v1/research/", json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_kind_defaults_to_inbox(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    note = await _note(client, h, uid)
    assert note["kind"] == "INBOX"
    assert note["pins"] == []
    got = await client.get(f"/api/v1/research/{note['id']}?universe_id={uid}", headers=h)
    assert got.json()["kind"] == "INBOX"


async def test_kind_filter_and_update(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    inbox = await _note(client, h, uid)
    parked = await _note(client, h, uid, kind="PARKED")
    ref = await _note(client, h, uid, kind="REFERENCE")
    assert parked["kind"] == "PARKED"

    resp = await client.get(f"/api/v1/research/?universe_id={uid}&kind=PARKED", headers=h)
    body = resp.json()
    assert [n["id"] for n in body["items"]] == [parked["id"]]
    assert body["total"] == 1
    assert body["items"][0]["kind"] == "PARKED"

    resp = await client.get(f"/api/v1/research/?universe_id={uid}", headers=h)
    assert resp.json()["total"] == 3

    resp = await client.patch(
        f"/api/v1/research/{inbox['id']}?universe_id={uid}", json={"kind": "FOR_YOU"}, headers=h
    )
    assert resp.status_code == 200
    assert resp.json()["kind"] == "FOR_YOU"
    resp = await client.get(f"/api/v1/research/?universe_id={uid}&kind=FOR_YOU", headers=h)
    assert [n["id"] for n in resp.json()["items"]] == [inbox["id"]]
    resp = await client.get(f"/api/v1/research/?universe_id={uid}&kind=REFERENCE", headers=h)
    assert [n["id"] for n in resp.json()["items"]] == [ref["id"]]

    bad = await client.patch(
        f"/api/v1/research/{inbox['id']}?universe_id={uid}", json={"kind": "NOPE"}, headers=h
    )
    assert bad.status_code == 422


async def test_create_with_pins_returns_labels(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    e = await _entities(client, h, uid)
    pins = [_ref(k, v) for k, v in e.items()]
    note = await _note(client, h, uid, pins=pins)

    by_kind = {p["kind"]: p for p in note["pins"]}
    assert set(by_kind) == {"member", "set", "incident", "alliance"}
    assert by_kind["member"]["id"] == e["member"]["id"]
    assert by_kind["member"]["name"] == "Pinny"
    assert by_kind["member"]["slug"] == e["member"]["slug"]
    assert by_kind["set"]["name"] == "Pin Set"
    assert by_kind["set"]["slug"] == e["set"]["slug"]
    assert by_kind["alliance"]["name"] == "Pin Bloc"
    assert by_kind["alliance"]["slug"] == e["alliance"]["slug"]
    assert by_kind["incident"]["slug"] is None
    assert by_kind["incident"]["name"] == "2022, 7 Mile & Gratiot"

    # The list item carries the same pins.
    resp = await client.get(f"/api/v1/research/?universe_id={uid}", headers=h)
    assert len(resp.json()["items"][0]["pins"]) == 4

    # Pinning the same entity twice stores it once.
    dup = await _note(client, h, uid, pins=[pins[0], pins[0]])
    assert len(dup["pins"]) == 1


async def test_update_replaces_pins(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    e = await _entities(client, h, uid)
    note = await _note(client, h, uid, pins=[_ref("member", e["member"]), _ref("set", e["set"])])
    url = f"/api/v1/research/{note['id']}?universe_id={uid}"

    resp = await client.patch(url, json={"pins": [_ref("alliance", e["alliance"])]}, headers=h)
    assert resp.status_code == 200
    assert [(p["kind"], p["id"]) for p in resp.json()["pins"]] == [
        ("alliance", e["alliance"]["id"])
    ]

    # Omitting pins leaves them; an empty list clears them.
    resp = await client.patch(url, json={"title": "Renamed"}, headers=h)
    assert len(resp.json()["pins"]) == 1
    resp = await client.patch(url, json={"pins": []}, headers=h)
    assert resp.json()["pins"] == []
    assert resp.json()["title"] == "Renamed"


async def test_cross_universe_and_missing_pin_rejected(
    client: AsyncClient, db_session: AsyncSession
):
    h, uid = await _setup(client, db_session)
    _, other_uid = await _setup(client, db_session)
    foreign = await _make(client, h, "members", {"universe_id": other_uid, "nickname": "Elsewhere"})
    mine = await _make(client, h, "members", {"universe_id": uid, "nickname": "Here"})

    resp = await client.post(
        "/api/v1/research/",
        json={"universe_id": uid, "title": "x", "pins": [_ref("member", foreign)]},
        headers=h,
    )
    assert resp.status_code == 422
    resp = await client.post(
        "/api/v1/research/",
        json={"universe_id": uid, "title": "x", "pins": [{"kind": "set", "id": str(uuid.uuid4())}]},
        headers=h,
    )
    assert resp.status_code == 422
    # Nothing was created by the rejected requests.
    resp = await client.get(f"/api/v1/research/?universe_id={uid}", headers=h)
    assert resp.json()["total"] == 0

    note = await _note(client, h, uid, pins=[_ref("member", mine)])
    resp = await client.patch(
        f"/api/v1/research/{note['id']}?universe_id={uid}",
        json={"pins": [_ref("member", foreign)]},
        headers=h,
    )
    assert resp.status_code == 422
    resp = await client.get(f"/api/v1/research/{note['id']}?universe_id={uid}", headers=h)
    assert [p["id"] for p in resp.json()["pins"]] == [mine["id"]]


async def test_pinned_endpoint(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    e = await _entities(client, h, uid)
    other = await _make(client, h, "members", {"universe_id": uid, "nickname": "Other"})
    first = await _note(client, h, uid, pins=[_ref("member", e["member"]), _ref("set", e["set"])])
    second = await _note(client, h, uid, pins=[_ref("member", e["member"])])
    await _note(client, h, uid, pins=[_ref("member", other)])
    await _note(client, h, uid)

    resp = await client.get(
        f"/api/v1/research/pinned?universe_id={uid}&member_id={e['member']['id']}", headers=h
    )
    assert resp.status_code == 200
    # Newest first: touching the older note moves it to the top.
    assert [n["id"] for n in resp.json()] == [second["id"], first["id"]]
    await client.patch(
        f"/api/v1/research/{first['id']}?universe_id={uid}", json={"title": "Bumped"}, headers=h
    )
    resp = await client.get(
        f"/api/v1/research/pinned?universe_id={uid}&member_id={e['member']['id']}", headers=h
    )
    assert [n["id"] for n in resp.json()] == [first["id"], second["id"]]
    assert {p["kind"] for p in resp.json()[0]["pins"]} == {"member", "set"}

    resp = await client.get(
        f"/api/v1/research/pinned?universe_id={uid}&set_id={e['set']['id']}", headers=h
    )
    assert [n["id"] for n in resp.json()] == [first["id"]]
    resp = await client.get(
        f"/api/v1/research/pinned?universe_id={uid}&incident_id={e['incident']['id']}", headers=h
    )
    assert resp.json() == []

    # Exactly one target is required.
    resp = await client.get(f"/api/v1/research/pinned?universe_id={uid}", headers=h)
    assert resp.status_code == 422
    resp = await client.get(
        f"/api/v1/research/pinned?universe_id={uid}&member_id={e['member']['id']}"
        f"&set_id={e['set']['id']}",
        headers=h,
    )
    assert resp.status_code == 422


@pytest.mark.parametrize(
    ("kind", "path"),
    [("member", "members"), ("set", "sets"), ("incident", "incidents"), ("alliance", "alliances")],
)
async def test_deleting_pinned_entity_keeps_note(
    client: AsyncClient, db_session: AsyncSession, kind: str, path: str
):
    h, uid = await _setup(client, db_session)
    e = await _entities(client, h, uid)
    note = await _note(client, h, uid, pins=[_ref(k, v) for k, v in e.items()])

    resp = await client.delete(f"/api/v1/{path}/{e[kind]['id']}?universe_id={uid}", headers=h)
    assert resp.status_code == 204, resp.text

    resp = await client.get(f"/api/v1/research/{note['id']}?universe_id={uid}", headers=h)
    assert resp.status_code == 200
    assert {p["kind"] for p in resp.json()["pins"]} == set(e) - {kind}


async def test_deleting_note_removes_pins_not_entity(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    e = await _entities(client, h, uid)
    note = await _note(client, h, uid, pins=[_ref("member", e["member"])])
    resp = await client.delete(f"/api/v1/research/{note['id']}?universe_id={uid}", headers=h)
    assert resp.status_code == 204
    resp = await client.get(
        f"/api/v1/research/pinned?universe_id={uid}&member_id={e['member']['id']}", headers=h
    )
    assert resp.json() == []
    resp = await client.get(f"/api/v1/members/{e['member']['id']}?universe_id={uid}", headers=h)
    assert resp.status_code == 200
