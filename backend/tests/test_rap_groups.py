"""Rap groups and labels: a separate link from sets, never an affiliation.

Expected values are written from the spec (rap-groups-spec, 2026-10-13), never
copied from a response. Names are invented.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")

G = "/api/v1/rap-groups/"


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


async def _group(client: AsyncClient, h: dict, uni: str, **body) -> dict:
    r = await client.post(G, json={"universe_id": uni, **body}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


async def _member(client: AsyncClient, h: dict, uni: str, nickname: str, **body) -> dict:
    r = await client.post(
        "/api/v1/members/", json={"universe_id": uni, "nickname": nickname, **body}, headers=h
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _set(client: AsyncClient, h: dict, uni: str, name: str) -> dict:
    r = await client.post("/api/v1/sets/", json={"universe_id": uni, "name": name}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def _get(client: AsyncClient, h: dict, uni: str, ref: str):
    return client.get(f"{G}{ref}?universe_id={uni}", headers=h)


def _patch(client: AsyncClient, h: dict, uni: str, gid: str, body: dict):
    return client.patch(f"{G}{gid}?universe_id={uni}", json=body, headers=h)


VARIANTS = [
    {"name": "Maple Street Mob", "initials": "MSM", "lead": "name", "is_primary": True},
    {"initials": "MSM"},
]


# ── names ──────────────────────────────────────────────────────────────────


async def test_name_is_derived_from_the_primary_variant(client, db_session):
    h, uni = await _ctx(client, db_session)
    g = await _group(client, h, uni, name_variants=VARIANTS)
    assert g["name"] == "Maple Street Mob"
    assert g["slug"] == "maple-street-mob"
    assert g["kind"] == "GROUP"
    assert g["status"] == "ACTIVE"
    assert [v["is_primary"] for v in g["name_variants"]] == [True, False]


async def test_name_alone_becomes_the_primary_variant(client, db_session):
    h, uni = await _ctx(client, db_session)
    g = await _group(client, h, uni, name="Oak Avenue Boys")
    assert g["name"] == "Oak Avenue Boys"
    assert g["name_variants"][0]["name"] == "Oak Avenue Boys"
    assert g["name_variants"][0]["is_primary"] is True


async def test_name_mismatch_is_422(client, db_session):
    h, uni = await _ctx(client, db_session)
    r = await client.post(
        G, json={"universe_id": uni, "name": "MSM", "name_variants": VARIANTS}, headers=h
    )
    assert r.status_code == 422
    assert "derived from its primary variant" in r.text


async def test_create_needs_a_name(client, db_session):
    h, uni = await _ctx(client, db_session)
    r = await client.post(G, json={"universe_id": uni}, headers=h)
    assert r.status_code == 422


async def test_unknown_fields_are_refused(client, db_session):
    h, uni = await _ctx(client, db_session)
    r = await client.post(
        G, json={"universe_id": uni, "name": "X Crew", "aliases": ["x"]}, headers=h
    )
    assert r.status_code == 422
    g = await _group(client, h, uni, name="Pine Crew")
    r = await _patch(client, h, uni, g["id"], {"universe_id": uni})
    assert r.status_code == 422


async def test_patch_of_name_alone_is_refused(client, db_session):
    h, uni = await _ctx(client, db_session)
    g = await _group(client, h, uni, name="Cedar Crew")
    r = await _patch(client, h, uni, g["id"], {"name": "Renamed"})
    assert r.status_code == 422
    assert "name_variants" in r.text


async def test_only_a_real_rename_reslugs(client, db_session):
    h, uni = await _ctx(client, db_session)
    g = await _group(client, h, uni, name_variants=VARIANTS)
    # Adding a variant leaves the displayed name alone: the slug stays.
    more = [*VARIANTS, {"name": "Maple St"}]
    r = await _patch(client, h, uni, g["id"], {"name_variants": more})
    assert r.status_code == 200, r.text
    assert r.json()["slug"] == "maple-street-mob"
    # Changing the primary's display renames and re-slugs.
    renamed = [{"name": "Maple Street Family", "is_primary": True}]
    r = await _patch(client, h, uni, g["id"], {"name_variants": renamed})
    assert r.json()["name"] == "Maple Street Family"
    assert r.json()["slug"] == "maple-street-family"
    # An agreeing name may ride along.
    r = await _patch(
        client, h, uni, g["id"], {"name": "Maple Street Family", "name_variants": renamed}
    )
    assert r.status_code == 200


async def test_slug_is_unique_per_universe(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _group(client, h, uni, name="Elm Crew")
    b = await _group(client, h, uni, name="Elm Crew")
    assert (a["slug"], b["slug"]) == ("elm-crew", "elm-crew-2")
    _, other = await _ctx(client, db_session)
    c = await _group(client, h, other, name="Elm Crew")
    assert c["slug"] == "elm-crew"


async def test_get_by_slug_or_id(client, db_session):
    h, uni = await _ctx(client, db_session)
    g = await _group(client, h, uni, name="Birch Crew", bio="A bio.")
    by_slug = await _get(client, h, uni, "birch-crew")
    by_id = await _get(client, h, uni, g["id"])
    assert by_slug.status_code == by_id.status_code == 200
    assert by_slug.json()["id"] == by_id.json()["id"] == g["id"]
    assert by_slug.json()["bio"] == "A bio."
    assert (await _get(client, h, uni, "no-such-group")).status_code == 404


# ── kind, status, fields ───────────────────────────────────────────────────


async def test_kind_status_dates_and_filters(client, db_session):
    h, uni = await _ctx(client, db_session)
    grp = await _group(
        client,
        h,
        uni,
        name="Harbor Gang Collective",
        status="DISBANDED",
        active_from={"year": 2012, "precision": "Y", "approx": False},
        active_to={"year": 2016, "precision": "Y", "approx": True},
    )
    lab = await _group(client, h, uni, name="Harbor Records", kind="LABEL")
    assert grp["kind"] == "GROUP" and lab["kind"] == "LABEL"
    assert grp["active_from"]["year"] == 2012
    assert grp["active_to"]["approx"] is True

    def ids(r):
        return {i["id"] for i in r.json()["items"]}

    base = f"{G}?universe_id={uni}"
    assert ids(await client.get(base, headers=h)) == {grp["id"], lab["id"]}
    assert ids(await client.get(f"{base}&kind=LABEL", headers=h)) == {lab["id"]}
    assert ids(await client.get(f"{base}&kind=GROUP", headers=h)) == {grp["id"]}
    assert ids(await client.get(f"{base}&status=DISBANDED", headers=h)) == {grp["id"]}
    assert ids(await client.get(f"{base}&status=ACTIVE", headers=h)) == {lab["id"]}
    assert (await client.get(f"{base}&kind=BOGUS", headers=h)).status_code == 422
    r = await _patch(client, h, uni, lab["id"], {"kind": "GROUP", "status": "DISBANDED"})
    assert (r.json()["kind"], r.json()["status"]) == ("GROUP", "DISBANDED")
    assert (await _patch(client, h, uni, lab["id"], {"kind": None})).status_code == 422


async def test_list_search_matches_name_and_variants(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _group(client, h, uni, name_variants=VARIANTS)
    await _group(client, h, uni, name="Unrelated Crew")
    base = f"{G}?universe_id={uni}&q="
    by_name = await client.get(base + "maple", headers=h)
    by_initials = await client.get(base + "MSM", headers=h)
    nothing = await client.get(base + "zzzz", headers=h)
    assert [i["id"] for i in by_name.json()["items"]] == [a["id"]]
    assert [i["id"] for i in by_initials.json()["items"]] == [a["id"]]
    assert nothing.json() == {"items": [], "total": 0}


async def test_home_area_must_be_in_the_universe(client, db_session):
    h, uni = await _ctx(client, db_session)
    _, other = await _ctx(client, db_session)
    muni = (
        await client.post(
            "/api/v1/municipalities/", json={"universe_id": uni, "name": "Testville"}, headers=h
        )
    ).json()
    foreign = (
        await client.post(
            "/api/v1/municipalities/", json={"universe_id": other, "name": "Elsewhere"}, headers=h
        )
    ).json()
    bad = await client.post(
        G, json={"universe_id": uni, "name": "A Crew", "municipality_id": foreign["id"]}, headers=h
    )
    assert bad.status_code == 422
    g = await _group(client, h, uni, name="B Crew", municipality_id=muni["id"])
    d = (await _get(client, h, uni, g["id"])).json()
    assert d["municipality"]["id"] == muni["id"]
    assert d["municipality"]["name"] == "Testville"
    listed = (await client.get(f"{G}?universe_id={uni}", headers=h)).json()["items"]
    assert listed[0]["municipality"]["name"] == "Testville"
    cleared = await _patch(client, h, uni, g["id"], {"municipality_id": None})
    assert cleared.json()["municipality_id"] is None
    assert (await _get(client, h, uni, g["id"])).json()["municipality"] is None


# ── members ────────────────────────────────────────────────────────────────


async def test_member_list_replaces_and_keeps_order(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _member(client, h, uni, f"Alpha{_uid()}")
    b = await _member(client, h, uni, f"Bravo{_uid()}")
    c = await _member(client, h, uni, f"Charlie{_uid()}")
    g = await _group(
        client,
        h,
        uni,
        name="Quartz Crew",
        members=[
            {"member_id": b["id"], "role": "FOUNDER", "since": {"year": 2010, "precision": "Y"}},
            {"member_id": a["id"]},
        ],
    )
    d = (await _get(client, h, uni, g["id"])).json()
    assert [m["member_id"] for m in d["members"]] == [b["id"], a["id"]]
    assert [m["role"] for m in d["members"]] == ["FOUNDER", "MEMBER"]
    assert d["members"][0]["since"]["year"] == 2010
    assert d["member_count"] == 2

    # The list replaces: a is dropped, c joins, b changes role and moves last.
    r = await _patch(
        client,
        h,
        uni,
        g["id"],
        {
            "members": [
                {"member_id": c["id"], "role": "SIGNED"},
                {"member_id": b["id"], "role": "AFFILIATE", "until": {"year": 2014}},
            ]
        },
    )
    assert r.status_code == 200, r.text
    d = (await _get(client, h, uni, g["id"])).json()
    assert [m["member_id"] for m in d["members"]] == [c["id"], b["id"]]
    assert [m["role"] for m in d["members"]] == ["SIGNED", "AFFILIATE"]
    assert d["members"][0]["since"] is None
    assert d["members"][1]["since"] is None
    assert d["members"][1]["until"]["year"] == 2014

    # A PATCH without members leaves them alone; [] clears.
    await _patch(client, h, uni, g["id"], {"bio": "Changed."})
    assert len((await _get(client, h, uni, g["id"])).json()["members"]) == 2
    await _patch(client, h, uni, g["id"], {"members": []})
    assert (await _get(client, h, uni, g["id"])).json()["members"] == []


async def test_members_must_be_in_the_groups_universe(client, db_session):
    h, uni = await _ctx(client, db_session)
    _, other = await _ctx(client, db_session)
    foreign = await _member(client, h, other, f"Foreign{_uid()}")
    r = await client.post(
        G,
        json={"universe_id": uni, "name": "C Crew", "members": [{"member_id": foreign["id"]}]},
        headers=h,
    )
    assert r.status_code == 422
    assert foreign["id"] in r.text
    g = await _group(client, h, uni, name="D Crew")
    r = await _patch(client, h, uni, g["id"], {"members": [{"member_id": foreign["id"]}]})
    assert r.status_code == 422


async def test_duplicate_member_in_one_list_is_422(client, db_session):
    h, uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, f"Dup{_uid()}")
    r = await client.post(
        G,
        json={
            "universe_id": uni,
            "name": "E Crew",
            "members": [{"member_id": m["id"]}, {"member_id": m["id"], "role": "FOUNDER"}],
        },
        headers=h,
    )
    assert r.status_code == 422


async def test_detail_members_sets_and_sets_represented(client, db_session):
    h, uni = await _ctx(client, db_session)
    north = await _set(client, h, uni, f"North {_uid()}")
    south = await _set(client, h, uni, f"South {_uid()}")
    m1 = await _member(
        client,
        h,
        uni,
        f"One{_uid()}",
        status="LOCKED",
        affiliations=[{"set_id": north["id"], "is_primary": True}],
    )
    m2 = await _member(
        client,
        h,
        uni,
        f"Two{_uid()}",
        affiliations=[
            {"set_id": south["id"], "is_primary": False},
            {"set_id": north["id"], "is_primary": True},
        ],
    )
    m3 = await _member(
        client, h, uni, f"Three{_uid()}", affiliations=[{"set_id": south["id"], "is_primary": True}]
    )
    m4 = await _member(client, h, uni, f"Four{_uid()}")
    g = await _group(
        client,
        h,
        uni,
        name="Ridge Hotboyz",
        members=[{"member_id": m["id"]} for m in (m1, m2, m3, m4)],
    )
    d = (await _get(client, h, uni, g["id"])).json()
    by_member = {m["member_id"]: m for m in d["members"]}
    assert by_member[m1["id"]]["status"] == "LOCKED"
    assert by_member[m1["id"]]["display_name"] == m1["display_name"]
    assert by_member[m1["id"]]["slug"] == m1["slug"]
    assert [s["id"] for s in by_member[m1["id"]]["sets"]] == [north["id"]]
    # His primary set comes first.
    assert [s["id"] for s in by_member[m2["id"]]["sets"]] == [north["id"], south["id"]]
    assert by_member[m4["id"]]["sets"] == []
    assert "primary_photo_thumb_url" in by_member[m1["id"]]
    # North: m1, m2. South: m2, m3. Two each, so the order falls to the name.
    reps = {s["id"]: s["count"] for s in d["sets_represented"]}
    assert reps == {north["id"]: 2, south["id"]: 2}
    assert set(d["sets_represented"][0]) == {"id", "slug", "name", "count"}


async def test_member_reads_include_rap_groups_by_position(client, db_session):
    h, uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, f"Solo{_uid()}")
    other = await _member(client, h, uni, f"Other{_uid()}")
    first = await _group(client, h, uni, name="Zed Crew", members=[{"member_id": other["id"]}])
    second = await _group(client, h, uni, name="Alpha Records", kind="LABEL")
    # Position is the index in each group's own list: m is 1 in the first group
    # and 0 in the second, so it reads [second, first].
    await _patch(
        client,
        h,
        uni,
        first["id"],
        {"members": [{"member_id": other["id"]}, {"member_id": m["id"], "role": "FOUNDER"}]},
    )
    await _patch(
        client, h, uni, second["id"], {"members": [{"member_id": m["id"], "role": "SIGNED"}]}
    )
    detail = (await client.get(f"/api/v1/members/{m['id']}?universe_id={uni}", headers=h)).json()
    assert detail["rap_groups"] == [
        {"id": second["id"], "slug": "alpha-records", "name": "Alpha Records", "role": "SIGNED"},
        {"id": first["id"], "slug": "zed-crew", "name": "Zed Crew", "role": "FOUNDER"},
    ]
    # is_rapper is not touched by membership.
    assert detail["is_rapper"] is False
    listed = (await client.get(f"/api/v1/members/?universe_id={uni}", headers=h)).json()["items"]
    by_id = {i["id"]: i for i in listed}
    assert [g["name"] for g in by_id[m["id"]]["rap_groups"]] == ["Alpha Records", "Zed Crew"]
    assert [g["name"] for g in by_id[other["id"]]["rap_groups"]] == ["Zed Crew"]
    loner = await _member(client, h, uni, f"Loner{_uid()}")
    listed = (await client.get(f"/api/v1/members/?universe_id={uni}", headers=h)).json()["items"]
    assert {i["id"]: i for i in listed}[loner["id"]]["rap_groups"] == []
    searched = (
        await client.get(f"/api/v1/members/search?universe_id={uni}&q=Solo", headers=h)
    ).json()
    assert [g["name"] for g in searched[0]["rap_groups"]] == ["Alpha Records", "Zed Crew"]


async def test_deleting_a_member_leaves_the_group(client, db_session):
    h, uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, f"Gone{_uid()}")
    g = await _group(client, h, uni, name="F Crew", members=[{"member_id": m["id"]}])
    r = await client.delete(f"/api/v1/members/{m['id']}?universe_id={uni}", headers=h)
    assert r.status_code == 204
    assert (await _get(client, h, uni, g["id"])).json()["members"] == []


# ── relationships ──────────────────────────────────────────────────────────


async def test_relationships_are_normalised_and_symmetric(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _group(client, h, uni, name="Rel A")
    b = await _group(client, h, uni, name="Rel B")
    c = await _group(client, h, uni, name="Rel C")
    r = await _patch(client, h, uni, a["id"], {"friend_ids": [b["id"]], "enemy_ids": [c["id"]]})
    assert r.status_code == 200, r.text
    da = (await _get(client, h, uni, a["id"])).json()
    got = {x["rap_group_id"]: x for x in da["relationships"]}
    assert {k: v["type"] for k, v in got.items()} == {b["id"]: "FRIEND", c["id"]: "ENEMY"}
    assert got[b["id"]]["name"] == "Rel B"
    assert got[b["id"]]["slug"] == "rel-b"
    # Read from the other end, whichever id is smaller.
    for other, kind, owner in ((b, "FRIEND", a), (c, "ENEMY", a)):
        d = (await _get(client, h, uni, other["id"])).json()
        assert [(x["rap_group_id"], x["type"]) for x in d["relationships"]] == [(owner["id"], kind)]
    # Stored once, smaller id first, whichever end wrote it.
    rows = (
        await db_session.execute(
            text(
                "SELECT rap_group_a_id, rap_group_b_id FROM rap_group_relationship "
                "WHERE rap_group_a_id IN (:a, :b, :c) OR rap_group_b_id IN (:a, :b, :c)"
            ),
            {"a": a["id"], "b": b["id"], "c": c["id"]},
        )
    ).all()
    assert len(rows) == 2
    assert all(str(x) < str(y) for x, y in rows)


async def test_relationship_lists_replace_and_one_list_keeps_the_other(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _group(client, h, uni, name="Rep A")
    b = await _group(client, h, uni, name="Rep B")
    c = await _group(client, h, uni, name="Rep C")
    await _patch(client, h, uni, a["id"], {"friend_ids": [b["id"]], "enemy_ids": [c["id"]]})
    # Only enemy_ids sent: the friends stay.
    await _patch(client, h, uni, a["id"], {"enemy_ids": []})
    d = (await _get(client, h, uni, a["id"])).json()
    assert [(x["rap_group_id"], x["type"]) for x in d["relationships"]] == [(b["id"], "FRIEND")]
    # A pair moved from friend to enemy changes type; the same call is idempotent.
    for _ in range(2):
        await _patch(client, h, uni, a["id"], {"friend_ids": [], "enemy_ids": [b["id"]]})
        d = (await _get(client, h, uni, a["id"])).json()
        assert [(x["rap_group_id"], x["type"]) for x in d["relationships"]] == [(b["id"], "ENEMY")]
    # In both lists, the enemy wins; itself is ignored.
    await _patch(
        client,
        h,
        uni,
        a["id"],
        {"friend_ids": [c["id"], a["id"]], "enemy_ids": [c["id"]]},
    )
    d = (await _get(client, h, uni, a["id"])).json()
    assert {x["rap_group_id"]: x["type"] for x in d["relationships"]} == {c["id"]: "ENEMY"}


async def test_relationships_stay_in_the_universe(client, db_session):
    h, uni = await _ctx(client, db_session)
    _, other = await _ctx(client, db_session)
    foreign = await _group(client, h, other, name="Far Crew")
    r = await client.post(
        G, json={"universe_id": uni, "name": "G Crew", "friend_ids": [foreign["id"]]}, headers=h
    )
    assert r.status_code == 422


async def test_relationship_check_constraint_rejects_wrong_order(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _group(client, h, uni, name="Chk A")
    b = await _group(client, h, uni, name="Chk B")
    hi, lo = sorted((a["id"], b["id"]), reverse=True)
    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("INSERT INTO rap_group_relationship VALUES (:hi, :lo, 'FRIEND')"),
            {"hi": hi, "lo": lo},
        )
        await db_session.flush()
    await db_session.rollback()


# ── incidents ──────────────────────────────────────────────────────────────


async def test_detail_lists_members_incidents_newest_first(client, db_session):
    h, uni = await _ctx(client, db_session)
    shooter = await _member(client, h, uni, f"Shooter{_uid()}")
    victim = await _member(client, h, uni, f"Victim{_uid()}")
    outsider = await _member(client, h, uni, f"Outsider{_uid()}")
    g = await _group(client, h, uni, name="Inc Crew", members=[{"member_id": shooter["id"]}])

    async def incident(year: int, *participants):
        r = await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": uni,
                "type": "SHOOTING",
                "date": {"year": year, "precision": "Y"},
                "participants": [
                    {"member_id": m, "role": role, "outcome": "UNHARMED"}
                    for m, role in participants
                ],
            },
            headers=h,
        )
        assert r.status_code == 201, r.text
        return r.json()["id"]

    old = await incident(2015, (shooter["id"], "SHOOTER"), (victim["id"], "VICTIM"))
    new = await incident(2021, (victim["id"], "SHOOTER"), (shooter["id"], "VICTIM"))
    await incident(2019, (victim["id"], "SHOOTER"), (outsider["id"], "VICTIM"))
    d = (await _get(client, h, uni, g["id"])).json()
    assert [i["id"] for i in d["incidents"]] == [new, old]
    assert d["incidents"][0]["date"]["year"] == 2021


# ── citations ──────────────────────────────────────────────────────────────


async def test_a_rap_group_can_be_cited(client, db_session):
    h, uni = await _ctx(client, db_session)
    g = await _group(client, h, uni, name="Cite Crew")
    src = (
        await client.post(
            "/api/v1/sources/",
            json={"universe_id": uni, "title": "A page", "url": f"https://e.x/{_uid()}"},
            headers=h,
        )
    ).json()["id"]
    r = await client.post(
        f"/api/v1/citations/?universe_id={uni}",
        json={
            "source_id": src,
            "entity_type": "rap_group",
            "entity_id": g["id"],
            "locator": "p. 4",
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    d = (await _get(client, h, uni, g["id"])).json()
    assert [(c["source_id"], c["locator"]) for c in d["citations"]] == [(src, "p. 4")]
    # Once per (source, record).
    again = await client.post(
        f"/api/v1/citations/?universe_id={uni}",
        json={"source_id": src, "entity_type": "rap_group", "entity_id": g["id"]},
        headers=h,
    )
    assert again.status_code == 409
    # The source page counts it.
    counts = (await client.get(f"/api/v1/sources/{src}?universe_id={uni}", headers=h)).json()[
        "counts"
    ]
    assert counts["rap_group"] == 1
    assert counts["total"] == 1


async def test_citation_checks_the_rap_group(client, db_session):
    h, uni = await _ctx(client, db_session)
    _, other = await _ctx(client, db_session)
    foreign = await _group(client, h, other, name="Abroad Crew")
    src = (
        await client.post(
            "/api/v1/sources/",
            json={"universe_id": uni, "title": "A page", "url": f"https://e.x/{_uid()}"},
            headers=h,
        )
    ).json()["id"]
    url = f"/api/v1/citations/?universe_id={uni}"
    missing = await client.post(
        url,
        json={"source_id": src, "entity_type": "rap_group", "entity_id": str(uuid.uuid4())},
        headers=h,
    )
    assert missing.status_code == 404
    crossed = await client.post(
        url,
        json={"source_id": src, "entity_type": "rap_group", "entity_id": foreign["id"]},
        headers=h,
    )
    assert crossed.status_code == 422


async def test_citation_and_media_need_exactly_one_target(client, db_session):
    h, uni = await _ctx(client, db_session)
    g = await _group(client, h, uni, name="Chk Crew")
    m = await _member(client, h, uni, f"Chk{_uid()}")
    src = (
        await client.post(
            "/api/v1/sources/",
            json={"universe_id": uni, "title": "P", "url": f"https://e.x/{_uid()}"},
            headers=h,
        )
    ).json()["id"]
    for sql in (
        "INSERT INTO citation (id, universe_id, source_id, rap_group_id, member_id, position, "
        "created_at, updated_at) VALUES (gen_random_uuid(), :u, :s, :g, :m, 0, now(), now())",
        "INSERT INTO media (id, universe_id, rap_group_id, member_id, kind, is_primary, "
        "created_at) VALUES (gen_random_uuid(), :u, :g, :m, 'R2', false, now())",
    ):
        with pytest.raises(IntegrityError):
            await db_session.execute(text(sql), {"u": uni, "s": src, "g": g["id"], "m": m["id"]})
            await db_session.flush()
        await db_session.rollback()
    # A rap group alone is a valid media target, and it has a primary photo.
    await db_session.execute(
        text(
            "INSERT INTO media (id, universe_id, rap_group_id, kind, external_url, is_primary, "
            "created_at) VALUES (gen_random_uuid(), :u, :g, 'EXTERNAL_URL', "
            "'https://img.example/a.jpg', true, now())"
        ),
        {"u": uni, "g": g["id"]},
    )
    await db_session.commit()
    media = await client.get(f"/api/v1/media/?universe_id={uni}&rap_group_id={g['id']}", headers=h)
    assert media.status_code == 200
    assert [x["rap_group_id"] for x in media.json()] == [g["id"]]
    d = (await _get(client, h, uni, g["id"])).json()
    assert d["primary_photo_url"] == "https://img.example/a.jpg"
    listed = (await client.get(f"{G}?universe_id={uni}", headers=h)).json()["items"]
    assert listed[0]["primary_photo_url"] == "https://img.example/a.jpg"


# ── list shape, delete, audit ──────────────────────────────────────────────


async def test_list_item_shape(client, db_session):
    h, uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, f"Shape{_uid()}")
    await _group(
        client, h, uni, name_variants=VARIANTS, members=[{"member_id": m["id"]}], kind="LABEL"
    )
    page = (await client.get(f"{G}?universe_id={uni}", headers=h)).json()
    assert page["total"] == 1
    item = page["items"][0]
    assert set(item) == {
        "id",
        "slug",
        "name",
        "name_variants",
        "kind",
        "status",
        "active_from",
        "active_to",
        "municipality",
        "member_count",
        "primary_photo_url",
    }
    assert item["member_count"] == 1
    assert item["kind"] == "LABEL"
    d = (await _get(client, h, uni, item["id"])).json()
    assert set(d) == set(item) | {
        "bio",
        "members",
        "sets_represented",
        "relationships",
        "incidents",
        "citations",
        "created_at",
        "updated_at",
    }


async def test_delete_is_admin_only_and_cleans_up(client, db_session):
    h, uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, f"Del{_uid()}")
    a = await _group(client, h, uni, name="Del A", members=[{"member_id": m["id"]}])
    b = await _group(client, h, uni, name="Del B", friend_ids=[a["id"]])
    email = f"plain_{_uid()}@example.com"
    await create_user(db_session, email, "pass1234", GlobalRole.USER)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    ).json()["access_token"]
    user_h = {"Authorization": f"Bearer {token}"}
    denied = await client.delete(f"{G}{a['id']}?universe_id={uni}", headers=user_h)
    assert denied.status_code in (401, 403)
    ok = await client.delete(f"{G}{a['id']}?universe_id={uni}", headers=h)
    assert ok.status_code == 204
    assert (await _get(client, h, uni, a["id"])).status_code == 404
    assert (await _get(client, h, uni, b["id"])).json()["relationships"] == []
    detail = (await client.get(f"/api/v1/members/{m['id']}?universe_id={uni}", headers=h)).json()
    assert detail["rap_groups"] == []
    assert (await client.delete(f"{G}{a['id']}?universe_id={uni}", headers=h)).status_code == 404


async def test_writes_reach_the_audit_log(client, db_session):
    attach_audit_listeners()
    h, uni = await _ctx(client, db_session)
    m = await _member(client, h, uni, f"Aud{_uid()}")
    g = await _group(client, h, uni, name="Audit Crew", members=[{"member_id": m["id"]}])
    await _group(client, h, uni, name="Audit Rival", enemy_ids=[g["id"]])
    kinds = {
        row[0]
        for row in (
            await db_session.execute(
                text(
                    "SELECT DISTINCT entity_type FROM audit_log "
                    "WHERE diff_json->>'rap_group_id' = :g OR diff_json->>'rap_group_a_id' = :g "
                    "OR diff_json->>'rap_group_b_id' = :g OR entity_id::text = :g"
                ),
                {"g": g["id"]},
            )
        ).all()
    }
    assert kinds == {"rap_group", "rap_group_member", "rap_group_relationship"}
