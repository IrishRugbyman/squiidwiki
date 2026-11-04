"""People in a photo: `media_member` links a photo to the members who appear in it.

Expected values are written from the spec (people-in-photo brief, 2026-10-13),
never copied from a response. Names are invented. Photos are inserted as
EXTERNAL_URL rows so no R2 call is made.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")

M = "/api/v1/media"


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _ctx(client: AsyncClient, session: AsyncSession) -> tuple[dict, str]:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "pass1234", GlobalRole.ADMIN)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    uni = (
        await client.post(
            "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=h
        )
    ).json()["id"]
    return h, uni


async def _make(client: AsyncClient, h: dict, path: str, body: dict) -> dict:
    r = await client.post(path, json=body, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


async def _member(client, h, uni, nickname: str | None, **body) -> dict:
    return await _make(
        client, h, "/api/v1/members/", {"universe_id": uni, "nickname": nickname, **body}
    )


async def _members(client, h, uni, *nicknames: str) -> list[dict]:
    return [await _member(client, h, uni, n) for n in nicknames]


async def _photo(session: AsyncSession, uni: str, owner_col: str, owner_id: str) -> str:
    """A photo owned by one entity, inserted directly (the upload path needs R2)."""
    media_id = str(uuid.uuid4())
    await session.execute(
        text(
            f"INSERT INTO media (id, universe_id, {owner_col}, kind, external_url, is_primary, "
            "created_at) VALUES (:id, :u, :o, 'EXTERNAL_URL', 'https://img.example/a.jpg', "
            "false, now())"
        ),
        {"id": media_id, "u": uni, "o": owner_id},
    )
    await session.commit()
    return media_id


def _put(client, h, media_id, uni, people):
    return client.put(
        f"{M}/{media_id}/people", json={"universe_id": uni, "people": people}, headers=h
    )


def _names(body: dict) -> list[str]:
    return [p["nickname"] for p in body["people"]]


async def _rows(session: AsyncSession, media_id: str) -> int:
    r = await session.execute(
        text("SELECT count(*) FROM media_member WHERE media_id = :m"), {"m": media_id}
    )
    return r.scalar_one()


# ── replace semantics and ordering ─────────────────────────────────────────


async def test_put_replaces_the_set_and_returns_the_media(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Set {_uid()}"})
    a, b, c = await _members(client, h, uni, "Aaron", "Bobby", "Cass")
    photo = await _photo(db_session, uni, "set_id", s["id"])

    first = await _put(
        client,
        h,
        photo,
        uni,
        [{"member_id": a["id"], "position": 0}, {"member_id": b["id"], "position": 1}],
    )
    assert first.status_code == 200, first.text
    assert first.json()["id"] == photo
    assert first.json()["set_id"] == s["id"]
    assert _names(first.json()) == ["Aaron", "Bobby"]

    # Replace: Aaron out, Cass in, Bobby kept but moved.
    second = await _put(
        client,
        h,
        photo,
        uni,
        [{"member_id": c["id"], "position": 0}, {"member_id": b["id"], "position": 1}],
    )
    assert _names(second.json()) == ["Cass", "Bobby"]
    assert await _rows(db_session, photo) == 2

    # An empty list clears the photo.
    cleared = await _put(client, h, photo, uni, [])
    assert cleared.json()["people"] == []
    assert await _rows(db_session, photo) == 0


async def test_order_is_position_then_null_last_then_name(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Ord {_uid()}"})
    zed, amy, mia, bo = await _members(client, h, uni, "Zed", "Amy", "Mia", "Bo")
    unknown = await _member(client, h, uni, None, nickname_unknown=True, legal_name="Carl Young")
    photo = await _photo(db_session, uni, "set_id", s["id"])

    r = await _put(
        client,
        h,
        photo,
        uni,
        [
            {"member_id": zed["id"], "position": None},
            {"member_id": amy["id"], "position": None},
            {"member_id": mia["id"], "position": 1},
            {"member_id": bo["id"], "position": 0},
            {"member_id": unknown["id"], "position": None},
        ],
    )
    assert r.status_code == 200, r.text
    # Positioned first (0, 1), then the unordered alphabetically by the name
    # they are shown under: Amy, Carl Young (legal name, nickname unknown), Zed.
    assert [p["display_name"] for p in r.json()["people"]] == [
        "Bo",
        "Mia",
        "Amy",
        "Carl Young",
        "Zed",
    ]
    assert [p["position"] for p in r.json()["people"]] == [0, 1, None, None, None]
    carl = r.json()["people"][3]
    assert carl["nickname"] is None
    assert carl["legal_name"] == "Carl Young"
    assert carl["slug"] == unknown["slug"]
    assert carl["member_id"] == unknown["id"]


async def test_list_and_get_carry_people_for_every_photo(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Lst {_uid()}"})
    a, b = await _member(client, h, uni, "Ann"), await _member(client, h, uni, "Ben")
    p1 = await _photo(db_session, uni, "set_id", s["id"])
    p2 = await _photo(db_session, uni, "set_id", s["id"])
    p3 = await _photo(db_session, uni, "set_id", s["id"])
    await _put(client, h, p1, uni, [{"member_id": a["id"], "position": 0}])
    await _put(client, h, p2, uni, [{"member_id": b["id"], "position": None}])

    listed = (await client.get(f"{M}/?universe_id={uni}&set_id={s['id']}", headers=h)).json()
    by_id = {x["id"]: _names(x) for x in listed}
    assert by_id == {p1: ["Ann"], p2: ["Ben"], p3: []}
    one = (await client.get(f"{M}/{p1}?universe_id={uni}", headers=h)).json()
    assert _names(one) == ["Ann"]


# ── rejections ─────────────────────────────────────────────────────────────


async def test_the_photos_own_member_cannot_be_tagged(client, db_session):
    h, uni = await _ctx(client, db_session)
    owner = await _member(client, h, uni, "Owner")
    other = await _member(client, h, uni, "Other")
    photo = await _photo(db_session, uni, "member_id", owner["id"])

    r = await _put(client, h, photo, uni, [{"member_id": owner["id"]}])
    assert r.status_code == 422
    assert r.json()["code"] == "person_is_owner"
    assert r.json()["member_id"] == owner["id"]
    # Nothing was written, and others can still be tagged on his photo.
    assert await _rows(db_session, photo) == 0
    ok = await _put(client, h, photo, uni, [{"member_id": other["id"]}])
    assert ok.status_code == 200
    assert _names(ok.json()) == ["Other"]


async def test_duplicates_are_rejected(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Dup {_uid()}"})
    a = await _member(client, h, uni, "Dupe")
    photo = await _photo(db_session, uni, "set_id", s["id"])
    r = await _put(
        client, h, photo, uni, [{"member_id": a["id"], "position": 0}, {"member_id": a["id"]}]
    )
    assert r.status_code == 422
    assert r.json()["code"] == "duplicate_person"
    assert r.json()["member_ids"] == [a["id"]]
    assert await _rows(db_session, photo) == 0


async def test_member_from_another_universe_or_missing_is_rejected(client, db_session):
    h, uni = await _ctx(client, db_session)
    _, other_uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Xu {_uid()}"})
    mine = await _member(client, h, uni, "Mine")
    foreign = await _member(client, h, other_uni, "Foreign")
    photo = await _photo(db_session, uni, "set_id", s["id"])
    await _put(client, h, photo, uni, [{"member_id": mine["id"]}])

    for bad in (foreign["id"], str(uuid.uuid4())):
        r = await _put(client, h, photo, uni, [{"member_id": mine["id"]}, {"member_id": bad}])
        assert r.status_code == 422, r.text
        assert r.json()["code"] == "person_not_in_universe"
        assert r.json()["member_ids"] == [bad]
    # The rejected PUTs left the earlier tags alone.
    got = (await client.get(f"{M}/{photo}?universe_id={uni}", headers=h)).json()
    assert _names(got) == ["Mine"]


async def test_negative_position_is_a_validation_error(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Neg {_uid()}"})
    a = await _member(client, h, uni, "Neg")
    photo = await _photo(db_session, uni, "set_id", s["id"])
    r = await _put(client, h, photo, uni, [{"member_id": a["id"], "position": -1}])
    assert r.status_code == 422


async def test_unknown_photo_and_anonymous_are_refused(client, anon_client, db_session):
    h, uni = await _ctx(client, db_session)
    assert (await _put(client, h, str(uuid.uuid4()), uni, [])).status_code == 404
    anon = await anon_client.put(
        f"{M}/{uuid.uuid4()}/people", json={"universe_id": uni, "people": []}
    )
    assert anon.status_code == 401


# ── cascades ───────────────────────────────────────────────────────────────


async def test_deleting_the_photo_removes_its_tags(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Cm {_uid()}"})
    a = await _member(client, h, uni, "Stays")
    photo = await _photo(db_session, uni, "set_id", s["id"])
    await _put(client, h, photo, uni, [{"member_id": a["id"]}])
    assert await _rows(db_session, photo) == 1

    assert (await client.delete(f"{M}/{photo}?universe_id={uni}", headers=h)).status_code == 204
    assert await _rows(db_session, photo) == 0
    still = await client.get(f"/api/v1/members/{a['id']}?universe_id={uni}", headers=h)
    assert still.status_code == 200


async def test_deleting_a_member_removes_his_tags_not_the_photo(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Cd {_uid()}"})
    gone, kept = await _member(client, h, uni, "Gone"), await _member(client, h, uni, "Kept")
    photo = await _photo(db_session, uni, "set_id", s["id"])
    await _put(client, h, photo, uni, [{"member_id": gone["id"]}, {"member_id": kept["id"]}])

    d = await client.delete(f"/api/v1/members/{gone['id']}?universe_id={uni}", headers=h)
    assert d.status_code == 204, d.text
    got = (await client.get(f"{M}/{photo}?universe_id={uni}", headers=h)).json()
    assert _names(got) == ["Kept"]
    assert await _rows(db_session, photo) == 1


# ── appears-in ─────────────────────────────────────────────────────────────


async def test_appears_in_lists_other_entities_photos_with_their_owner(client, db_session):
    h, uni = await _ctx(client, db_session)
    star = await _member(client, h, uni, "Star")
    friend = await _member(client, h, uni, "Friend", legal_name="Fred Friend")
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Own {_uid()}"})
    al = await _make(client, h, "/api/v1/alliances/", {"universe_id": uni, "name": f"Al {_uid()}"})
    rg = await _make(client, h, "/api/v1/rap-groups/", {"universe_id": uni, "name": f"Rg {_uid()}"})
    inc = await _make(
        client,
        h,
        "/api/v1/incidents/",
        {
            "universe_id": uni,
            "type": "SHOOTING",
            "location_text": "7 Mile",
            "date": {"year": 2022, "precision": "Y", "approx": False},
        },
    )
    muni = await _make(client, h, "/api/v1/municipalities/", {"universe_id": uni, "name": "Ville"})

    own = await _photo(db_session, uni, "member_id", star["id"])  # his own: never listed
    p_member = await _photo(db_session, uni, "member_id", friend["id"])
    p_set = await _photo(db_session, uni, "set_id", s["id"])
    p_alliance = await _photo(db_session, uni, "alliance_id", al["id"])
    p_group = await _photo(db_session, uni, "rap_group_id", rg["id"])
    p_inc = await _photo(db_session, uni, "incident_id", inc["id"])
    p_muni = await _photo(db_session, uni, "municipality_id", muni["id"])
    untagged = await _photo(db_session, uni, "set_id", s["id"])
    for p in (p_member, p_set, p_alliance, p_group, p_inc, p_muni):
        r = await _put(client, h, p, uni, [{"member_id": star["id"], "position": 0}])
        assert r.status_code == 200, r.text
    # A tag on someone else's photo does not make it appear on Star's page.
    await _put(client, h, untagged, uni, [{"member_id": friend["id"]}])

    r = await client.get(f"{M}/appears-in?member_id={star['id']}&universe_id={uni}", headers=h)
    assert r.status_code == 200, r.text
    items = {x["id"]: x for x in r.json()}
    assert set(items) == {p_member, p_set, p_alliance, p_group, p_inc, p_muni}
    assert own not in items and untagged not in items

    assert items[p_member]["owner"] == {
        "type": "member",
        "id": friend["id"],
        "name": "Friend",
        "slug": friend["slug"],
    }
    assert items[p_set]["owner"] == {
        "type": "set",
        "id": s["id"],
        "name": s["name"],
        "slug": s["slug"],
    }
    assert items[p_alliance]["owner"] == {
        "type": "alliance",
        "id": al["id"],
        "name": al["name"],
        "slug": al["slug"],
    }
    assert items[p_group]["owner"] == {
        "type": "rap_group",
        "id": rg["id"],
        "name": rg["name"],
        "slug": rg["slug"],
    }
    # An incident has no name or slug: it is labelled by its date and place.
    assert items[p_inc]["owner"] == {
        "type": "incident",
        "id": inc["id"],
        "name": "2022, 7 Mile",
        "slug": None,
    }
    assert items[p_muni]["owner"] == {
        "type": "municipality",
        "id": muni["id"],
        "name": "Ville",
        "slug": None,
    }
    # The same payload as a normal photo: signed urls and the people in it.
    assert items[p_set]["url"] == "https://img.example/a.jpg"
    assert _names(items[p_set]) == ["Star"]


async def test_appears_in_is_empty_without_tags_and_scoped_to_the_universe(client, db_session):
    h, uni = await _ctx(client, db_session)
    _, other_uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, "Lonely")
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Em {_uid()}"})
    photo = await _photo(db_session, uni, "set_id", s["id"])
    url = f"{M}/appears-in?member_id={m['id']}&universe_id="
    assert (await client.get(url + uni, headers=h)).json() == []
    await _put(client, h, photo, uni, [{"member_id": m["id"]}])
    assert len((await client.get(url + uni, headers=h)).json()) == 1
    assert (await client.get(url + other_uni, headers=h)).json() == []


async def test_appears_in_is_newest_photo_first(client, db_session):
    h, uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, "Order")
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Nw {_uid()}"})
    old = await _photo(db_session, uni, "set_id", s["id"])
    new = await _photo(db_session, uni, "set_id", s["id"])
    await db_session.execute(
        text("UPDATE media SET created_at = now() - interval '1 day' WHERE id = :i"), {"i": old}
    )
    await db_session.commit()
    for p in (old, new):
        await _put(client, h, p, uni, [{"member_id": m["id"]}])
    got = (
        await client.get(f"{M}/appears-in?member_id={m['id']}&universe_id={uni}", headers=h)
    ).json()
    assert [x["id"] for x in got] == [new, old]


# ── municipality photos live in prod ───────────────────────────────────────


async def test_municipality_photo_tagging_needs_the_prod_database(client, db_session, monkeypatch):
    h, uni = await _ctx(client, db_session)
    muni = await _make(
        client, h, "/api/v1/municipalities/", {"universe_id": uni, "name": "Prodville"}
    )
    m = await _member(client, h, uni, "Local")
    photo = await _photo(db_session, uni, "municipality_id", muni["id"])

    # In test mode the photo is in prod and the member is not: refused, nothing written.
    monkeypatch.setattr("app.routers.media.get_db_mode", lambda: "test")
    refused = await _put(client, h, photo, uni, [{"member_id": m["id"]}])
    assert refused.status_code == 409
    assert refused.json()["code"] == "people_need_prod"
    assert await _rows(db_session, photo) == 0

    # In prod mode both live in one database: allowed.
    monkeypatch.setattr("app.routers.media.get_db_mode", lambda: "prod")
    ok = await _put(client, h, photo, uni, [{"member_id": m["id"]}])
    assert ok.status_code == 200, ok.text
    assert _names(ok.json()) == ["Local"]


# ── audit ──────────────────────────────────────────────────────────────────


async def test_tag_changes_are_audited(client, db_session):
    attach_audit_listeners()
    h, uni = await _ctx(client, db_session)
    s = await _make(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Au {_uid()}"})
    a, b = await _member(client, h, uni, "AuA"), await _member(client, h, uni, "AuB")
    photo = await _photo(db_session, uni, "set_id", s["id"])
    await _put(client, h, photo, uni, [{"member_id": a["id"]}, {"member_id": b["id"]}])
    await _put(client, h, photo, uni, [{"member_id": a["id"], "position": 0}])

    rows = (
        await db_session.execute(
            text(
                "SELECT action, diff_json->>'media_id' AS media_id, diff_json->>'member_id' AS mid "
                "FROM audit_log WHERE entity_type = 'media_member' "
                "AND diff_json->>'media_id' = :m ORDER BY created_at, action"
            ),
            {"m": photo},
        )
    ).all()
    # Two creates, then Bobby's removal (the whole row, since a tag has no id of its own)
    # and Aaron's position change.
    assert sorted((r.action, r.mid) for r in rows) == sorted(
        [
            ("CREATE", a["id"]),
            ("CREATE", b["id"]),
            ("DELETE", b["id"]),
            ("UPDATE", a["id"]),
        ]
    )
