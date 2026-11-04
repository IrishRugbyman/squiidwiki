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

    async def cite(self, source: dict, member: dict, **fields) -> dict:
        return await self.post(
            f"/api/v1/citations/?universe_id={self.uni}",
            {
                "source_id": source["id"],
                "entity_type": "member",
                "entity_id": member["id"],
                **fields,
            },
        )

    async def merge(self, keep: str, drop: str, **body):
        return await self.c.post(
            f"/api/v1/members/{keep}/merge?universe_id={self.uni}",
            json={"drop_id": drop, **body},
            headers=self.h,
        )


async def _world(client: AsyncClient, session: AsyncSession, role=GlobalRole.ADMIN) -> World:
    email = f"u_{_uid()}@example.com"
    await create_user(session, email, "pass1234", role)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    if role == GlobalRole.ADMIN:
        uni = (
            await client.post(
                "/api/v1/universes/",
                json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
                headers=h,
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
        "/api/v1/sources/",
        {"url": "https://example.com/x", "title": "Digest", "reliability": "HIGH"},
    )
    keep = await w.member(
        nickname="Orrel", affiliations=[{"set_id": set_a["id"], "is_primary": True}]
    )
    drop = await w.member(
        nickname="Orrell",
        legal_name="Tobin Vask",
        biography="Ran the dice game behind the laundromat.",
        dob=Y(1994),
        affiliations=[{"set_id": set_b["id"], "is_primary": True}],
    )
    await w.cite(src, drop)
    inc = await w.post(
        "/api/v1/incidents/",
        {
            "type": "SHOOTING",
            "date": Y(2019),
            "participants": [{"member_id": drop["id"], "role": "SHOOTER"}],
        },
    )

    resp = await w.merge(keep["id"], drop["id"])
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert report["moved"]["incident_participations"] == 1
    assert report["moved"]["set_spells"] == 1
    assert report["moved"]["citations"] == 1
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
    assert [c["source_id"] for c in got["citations"]] == [src["id"]]
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
    assert (await w.get(f"/api/v1/members/{keep['id']}")).json()[
        "biography"
    ] == "The longer, better account."


async def test_same_incident_and_same_open_set_are_conflicts(
    client: AsyncClient, db_session: AsyncSession
):
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


async def test_family_is_repointed_and_self_links_dropped(
    client: AsyncClient, db_session: AsyncSession
):
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


async def test_killed_on_the_dropped_record_is_flagged(
    client: AsyncClient, db_session: AsyncSession
):
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
        f"/api/v1/members/{a['id']}/merge?universe_id={w.uni}",
        json={"drop_id": b["id"]},
        headers=user.h,
    )
    assert resp.status_code == 403


async def test_merge_moves_what_would_cascade_away(client: AsyncClient, db_session: AsyncSession):
    """Citations, rap groups, note pins, photo tags, court cases and alliances founded.

    The first four cascade from `member`, so anything the merge left on `drop`
    would be deleted with it; court case rows and founders would be emptied.
    """
    from app.models.media import Media, MediaMember

    w = await _world(client, db_session)
    keep = await w.member(nickname="Halvard")
    drop = await w.member(nickname="Halvardd")
    other = await w.member(nickname="Ostrel")
    shared = await w.post(
        "/api/v1/sources/", {"url": f"https://example.com/{_uid()}", "title": "Shared"}
    )
    only_drop = await w.post(
        "/api/v1/sources/", {"url": f"https://example.com/{_uid()}", "title": "Only"}
    )
    await w.cite(shared, keep)
    await w.cite(shared, drop, locator="p. 7", note="Names him.")
    await w.cite(only_drop, drop)

    group = await w.post(
        "/api/v1/rap-groups/",
        {"name": f"Glassline {_uid()}", "members": [{"member_id": drop["id"]}]},
    )
    note = await w.post(
        "/api/v1/research/", {"title": "Lead", "pins": [{"kind": "member", "id": drop["id"]}]}
    )
    alliance = await w.post(
        "/api/v1/alliances/", {"name": f"Tidewater {_uid()}", "founder_id": drop["id"]}
    )
    inc = await w.post(
        "/api/v1/incidents/",
        {
            "type": "SHOOTING",
            "date": Y(2018),
            "participants": [{"member_id": drop["id"], "role": "SHOOTER"}],
        },
    )
    case = await w.post(
        "/api/v1/court-cases/",
        {
            "name": f"People v. Test {_uid()}",
            "jurisdiction": "US_STATE",
            "court": "Test Circuit Court",
            "incident_ids": [inc["id"]],
        },
    )
    resp = await w.c.post(
        f"/api/v1/court-cases/{case['id']}/defendants?universe_id={w.uni}",
        json={"member_id": drop["id"], "disposition": "ACQUITTED"},
        headers=w.h,
    )
    assert resp.status_code == 201, resp.text

    # A photo of `other` that tags drop, and one of drop's own that tags keep.
    uni = uuid.UUID(w.uni)
    theirs = Media(
        universe_id=uni,
        member_id=uuid.UUID(other["id"]),
        kind="EXTERNAL_URL",
        external_url="https://example.com/a.jpg",
    )
    drops = Media(
        universe_id=uni,
        member_id=uuid.UUID(drop["id"]),
        kind="EXTERNAL_URL",
        external_url="https://example.com/b.jpg",
    )
    db_session.add_all([theirs, drops])
    await db_session.flush()
    db_session.add_all(
        [
            MediaMember(media_id=theirs.id, member_id=uuid.UUID(drop["id"])),
            MediaMember(media_id=drops.id, member_id=uuid.UUID(keep["id"])),
        ]
    )
    await db_session.commit()

    resp = await w.merge(keep["id"], drop["id"])
    assert resp.status_code == 200, resp.text
    moved = resp.json()["moved"]
    assert (moved["citations"], moved["rap_groups"], moved["note_pins"]) == (1, 1, 1)
    assert (moved["court_cases"], moved["photo_tags"], moved["alliances_founded"]) == (1, 1, 1)

    got = (await w.get(f"/api/v1/members/{keep['id']}")).json()
    cites = {c["source_id"]: c for c in got["citations"]}
    assert set(cites) == {shared["id"], only_drop["id"]}
    # keep's citation stands, its empty fields filled from drop's.
    assert (cites[shared["id"]]["locator"], cites[shared["id"]]["note"]) == ("p. 7", "Names him.")
    assert [g["id"] for g in got["rap_groups"]] == [group["id"]]

    pinned = (await w.get(f"/api/v1/research/pinned?member_id={keep['id']}")).json()
    assert [n["id"] for n in pinned] == [note["id"]]
    assert (await w.get(f"/api/v1/alliances/{alliance['id']}")).json()["founder_id"] == keep["id"]

    detail = (await w.get(f"/api/v1/court-cases/{case['id']}")).json()
    assert [d["member_id"] for d in detail["defendants"]] == [keep["id"]]
    parts = (await w.get(f"/api/v1/incidents/{inc['id']}")).json()["participants"]
    assert [(p["member_id"], p["acquitted"]) for p in parts] == [(keep["id"], True)]

    from sqlalchemy import select

    tags = (await db_session.execute(select(MediaMember.media_id, MediaMember.member_id))).all()
    # drop's tag on other's photo moved to keep; keep's tag on what is now its own photo is gone.
    assert (theirs.id, uuid.UUID(keep["id"])) in tags
    assert all(m != drops.id for m, _ in tags)


# ── Incarceration spells ─────────────────────────────────────────────────────
# Two records of one person, each imported from OTIS, hold the same sentences.
# The merge folds a spell into the kept record's matching one (court file,
# offense line, start date, by count) instead of moving a second copy across.
# Every court file and offense below is invented; the expected values are typed
# by hand, not produced by the code under test.

FIREARM = "Offense: Weapons - Felony Firearms"
DRUG = "Offense: Controlled Substance-Delivery/Manf."


def _ymd(y: int, m: int, d: int) -> dict:
    return {"year": y, "month": m, "day": d, "precision": "YMD", "approx": False}


MAR_1_2099 = {**_ymd(2099, 3, 1), "circa_text": None}
NOV_1_2098 = {**_ymd(2098, 11, 1), "circa_text": None}
DEC_15_2098 = {**_ymd(2098, 12, 15), "circa_text": None}


async def _spell(w: World, member: dict, **body) -> dict:
    return await w.post(f"/api/v1/members/{member['id']}/incarcerations?universe_id={w.uni}", body)


async def _spells(w: World, member: dict) -> list[dict]:
    resp = await w.get(f"/api/v1/members/{member['id']}/incarcerations")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _firearm(**kw) -> dict:
    return {
        "case_id": "2099-000001-FC",
        "notes": FIREARM,
        "from_date": _ymd(2099, 3, 1),
        **kw,
    }


def _drug(**kw) -> dict:
    return {
        "case_id": "2098-000002-FH",
        "notes": DRUG,
        "from_date": _ymd(2098, 5, 1),
        **kw,
    }


async def test_merge_folds_a_sentence_both_records_hold(
    client: AsyncClient, db_session: AsyncSession
):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Pellow")
    drop = await w.member(nickname="Pelloe")
    kept = await _spell(w, keep, **_firearm())
    await _spell(w, drop, **_firearm())

    resp = await w.merge(keep["id"], drop["id"])
    assert resp.status_code == 200, resp.text
    rows = await _spells(w, keep)
    assert [r["id"] for r in rows] == [kept["id"]]

    report = resp.json()
    assert report["moved"]["incarcerations"] == 0
    assert report["moved"]["incarcerations_matched"] == 1
    assert report["spell_differences"] == []
    assert report["spell_fills"] == []


async def test_merge_matches_spells_by_count(client: AsyncClient, db_session: AsyncSession):
    """One firearm count on the kept record, two identical ones on the other: two stay."""
    w = await _world(client, db_session)
    keep = await w.member(nickname="Dunmore")
    drop = await w.member(nickname="Dunmoor")
    kept = await _spell(w, keep, **_firearm())
    await _spell(w, drop, **_firearm())
    second = await _spell(w, drop, **_firearm())

    report = (await w.merge(keep["id"], drop["id"])).json()
    rows = await _spells(w, keep)
    assert len(rows) == 2
    assert {r["notes"] for r in rows} == {FIREARM}
    assert {r["id"] for r in rows} == {kept["id"], second["id"]}
    assert (report["moved"]["incarcerations"], report["moved"]["incarcerations_matched"]) == (1, 1)


async def test_merge_never_overwrites_a_spell_and_reports_the_difference(
    client: AsyncClient, db_session: AsyncSession
):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Garrow")
    drop = await w.member(nickname="Garrowe")
    kept = await _spell(w, keep, **_drug(to_date=_ymd(2098, 11, 1)))
    dropped = await _spell(w, drop, **_drug(to_date=_ymd(2098, 12, 15)))
    expected = [
        {
            "spell_id": kept["id"],
            "dropped_spell_id": dropped["id"],
            "field": "to_date",
            "kept": NOV_1_2098,
            "dropped": DEC_15_2098,
        }
    ]

    preview = (await w.merge(keep["id"], drop["id"], dry_run=True)).json()
    assert len(await _spells(w, drop)) == 1  # the dry run changed nothing

    report = (await w.merge(keep["id"], drop["id"])).json()
    rows = await _spells(w, keep)
    assert [(r["id"], r["to_date"]) for r in rows] == [(kept["id"], NOV_1_2098)]
    assert report["spell_differences"] == expected
    assert preview["spell_differences"] == expected


async def test_merge_fills_a_spell_gap_from_the_dropped_record(
    client: AsyncClient, db_session: AsyncSession
):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Ferrin")
    drop = await w.member(nickname="Ferrinn")
    case = await w.post(
        "/api/v1/court-cases/",
        {
            "name": f"People v. Test {_uid()}",
            "jurisdiction": "US_STATE",
            "court": "Test Circuit Court",
        },
    )
    kept = await _spell(w, keep, **_drug())
    dropped = await _spell(
        w,
        drop,
        **_drug(
            to_date=_ymd(2098, 11, 1),
            facility="Test Correctional Facility",
            court_case_id=case["id"],
        ),
    )
    assert kept["court_case_id"] is None

    report = (await w.merge(keep["id"], drop["id"])).json()
    rows = await _spells(w, keep)
    assert len(rows) == 1
    got = rows[0]
    assert got["id"] == kept["id"]
    assert (got["to_date"], got["facility"], got["court_case_id"]) == (
        NOV_1_2098,
        "Test Correctional Facility",
        case["id"],
    )

    assert report["spell_differences"] == []
    assert sorted((f["field"], f["value"]) for f in report["spell_fills"]) == [
        ("court_case_id", case["id"]),
        ("facility", "Test Correctional Facility"),
        ("to_date", NOV_1_2098),
    ]
    assert {(f["spell_id"], f["dropped_spell_id"]) for f in report["spell_fills"]} == {
        (kept["id"], dropped["id"])
    }


async def test_merge_keeps_the_kept_spells_court_case(
    client: AsyncClient, db_session: AsyncSession
):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Holloway")
    drop = await w.member(nickname="Hollowey")
    cases = [
        await w.post(
            "/api/v1/court-cases/",
            {
                "name": f"People v. Test {_uid()}",
                "jurisdiction": "US_STATE",
                "court": "Test Circuit Court",
            },
        )
        for _ in range(2)
    ]
    kept = await _spell(w, keep, **_drug(court_case_id=cases[0]["id"]))
    dropped = await _spell(w, drop, **_drug(court_case_id=cases[1]["id"]))

    report = (await w.merge(keep["id"], drop["id"])).json()
    assert [r["court_case_id"] for r in await _spells(w, keep)] == [cases[0]["id"]]
    assert report["spell_differences"] == [
        {
            "spell_id": kept["id"],
            "dropped_spell_id": dropped["id"],
            "field": "court_case_id",
            "kept": cases[0]["id"],
            "dropped": cases[1]["id"],
        }
    ]


async def test_merge_moves_spells_that_match_nothing(client: AsyncClient, db_session: AsyncSession):
    w = await _world(client, db_session)
    keep = await w.member(nickname="Tarrant")
    drop = await w.member(nickname="Tarrent")
    kept = await _spell(w, keep, **_firearm())
    moved = [
        await _spell(w, drop, **_drug()),  # another court file
        await _spell(w, drop, **_firearm(notes="Offense: Carrying Concealed Weapon")),
        await _spell(w, drop, **_firearm(from_date=_ymd(2099, 4, 1))),  # another start
    ]

    report = (await w.merge(keep["id"], drop["id"])).json()
    rows = await _spells(w, keep)
    assert {r["id"] for r in rows} == {kept["id"], *(m["id"] for m in moved)}
    assert (report["moved"]["incarcerations"], report["moved"]["incarcerations_matched"]) == (3, 0)
    assert report["spell_differences"] == []
