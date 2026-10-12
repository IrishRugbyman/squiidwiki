"""Alliances carry what sets carry: names in slots, emojis, several gangs, a
founder, lineage, stats and an activity feed."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")

A = "/api/v1/alliances/"


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _ctx(client: AsyncClient, session: AsyncSession) -> tuple[dict, str]:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    uni = (
        await client.post(
            "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=h
        )
    ).json()["id"]
    return h, uni


async def _alliance(client: AsyncClient, h: dict, uni: str, **body) -> dict:
    r = await client.post(A, json={"universe_id": uni, **body}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def _get(client: AsyncClient, h: dict, uni: str, ref: str):
    return client.get(f"{A}{ref}?universe_id={uni}", headers=h)


def _patch(client: AsyncClient, h: dict, uni: str, aid: str, body: dict):
    return client.patch(f"{A}{aid}?universe_id={uni}", json=body, headers=h)


HGH = [
    {
        "number": "444",
        "initials": "HGH",
        "name": "Hustle Gutta Hogg",
        "lead": "number",
        "is_primary": True,
    },
    {"number": "4224"},
]


async def test_name_is_the_primary_variant_display(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _alliance(client, h, uni, name_variants=HGH)
    assert a["name"] == "444"
    assert a["slug"] == "444"
    assert a["name_variants"][1]["is_primary"] is False
    # A name sent alongside must agree with the primary's display.
    bad = await client.post(
        A, json={"universe_id": uni, "name": "HGH", "name_variants": HGH}, headers=h
    )
    assert bad.status_code == 422
    assert "derived from its primary variant" in bad.text


async def test_combined_lead_shows_both_slots(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _alliance(
        client,
        h,
        uni,
        name_variants=[
            {
                "initials": "OES",
                "number": "187",
                "name": "HeadHunters",
                "lead": ["initials", "number", "name"],
            }
        ],
    )
    assert a["name"] == "OES 187 HeadHunters"


async def test_name_alone_on_patch_is_refused_and_rename_reslugs(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _alliance(client, h, uni, name="Cash Flow Posse")
    assert (await _patch(client, h, uni, a["id"], {"name": "CFP"})).status_code == 422
    # Adding initials without changing the lead keeps name and slug.
    same = await _patch(
        client,
        h,
        uni,
        a["id"],
        {
            "name_variants": [
                {"name": "Cash Flow Posse", "initials": "CFP", "lead": "name", "is_primary": True}
            ]
        },
    )
    assert same.status_code == 200, same.text
    assert (same.json()["name"], same.json()["slug"]) == ("Cash Flow Posse", "cash-flow-posse")
    renamed = await _patch(
        client,
        h,
        uni,
        a["id"],
        {
            "name_variants": [
                {
                    "name": "Cash Flow Posse",
                    "initials": "CFP",
                    "lead": "initials",
                    "is_primary": True,
                }
            ]
        },
    )
    assert (renamed.json()["name"], renamed.json()["slug"]) == ("CFP", "cfp")
    assert (await _patch(client, h, uni, a["id"], {"name_variants": []})).status_code == 422


async def test_stale_fields_are_refused(client, db_session):
    h, uni = await _ctx(client, db_session)
    r = await client.post(A, json={"universe_id": uni, "name": "X", "aliases": ["Y"]}, headers=h)
    assert r.status_code == 422
    a = await _alliance(client, h, uni, name="Bloc")
    assert (await _patch(client, h, uni, a["id"], {"gang_id": None})).status_code == 422


async def test_emojis_are_normalised_and_text_refused(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _alliance(client, h, uni, name="Bloc", emojis=[" 🔥 ", "🔥", "💯"])
    assert a["emojis"] == ["🔥", "💯"]
    r = await client.post(A, json={"universe_id": uni, "name": "B", "emojis": ["HGH"]}, headers=h)
    assert r.status_code == 422


async def test_search_matches_any_slot(client, db_session):
    h, uni = await _ctx(client, db_session)
    a = await _alliance(client, h, uni, name_variants=HGH)
    for q in ("Gutta", "HGH", "4224"):
        r = await client.get(f"{A}search?universe_id={uni}&q={q}", headers=h)
        assert [x["id"] for x in r.json()] == [a["id"]], q


async def _gang(client, h, uni, name):
    r = await client.post("/api/v1/gangs/", json={"universe_id": uni, "name": name}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


async def test_several_gangs_mirror_and_delete_promotes_next(client, db_session):
    h, uni = await _ctx(client, db_session)
    g1, g2 = (
        await _gang(client, h, uni, f"G1 {_uid()}"),
        await _gang(client, h, uni, f"G2 {_uid()}"),
    )
    a = await _alliance(client, h, uni, name="Bloc", gang_ids=[g1["id"], g2["id"]])
    assert a["gang_ids"] == [g1["id"], g2["id"]] and a["gang_id"] == g1["id"]
    detail = (await _get(client, h, uni, a["id"])).json()
    assert [g["id"] for g in detail["gangs"]] == [g1["id"], g2["id"]]
    # Both gang pages list it.
    for g in (g1, g2):
        d = (
            await client.get(f"/api/v1/gangs/{g['id']}/detail?universe_id={uni}", headers=h)
        ).json()
        assert a["id"] in [x["id"] for x in d["alliances"]]
    assert (
        await client.delete(f"/api/v1/gangs/{g1['id']}?universe_id={uni}", headers=h)
    ).status_code == 204
    after = (await _get(client, h, uni, a["id"])).json()
    assert after["gang_ids"] == [g2["id"]] and after["gang_id"] == g2["id"]
    # Foreign gang refused.
    _, other = await _ctx(client, db_session)
    foreign = await _gang(client, h, other, "Elsewhere")
    assert (await _patch(client, h, uni, a["id"], {"gang_ids": [foreign["id"]]})).status_code == 422


async def _member(client, h, uni, **body):
    r = await client.post(
        "/api/v1/members/", json={"universe_id": uni, "nickname": f"M {_uid()}", **body}, headers=h
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_founder_and_detail_stats(client, db_session):
    h, uni = await _ctx(client, db_session)
    s = (
        await client.post(
            "/api/v1/sets/", json={"universe_id": uni, "name": f"S {_uid()}"}, headers=h
        )
    ).json()
    a = await _alliance(client, h, uni, name="Bloc", set_ids=[s["id"]])
    in_set = await _member(
        client, h, uni, status="LOCKED", affiliations=[{"set_id": s["id"], "is_primary": True}]
    )
    await _member(client, h, uni, status="DEAD", alliance_id=a["id"])
    patched = await _patch(
        client,
        h,
        uni,
        a["id"],
        {
            "founder_id": in_set["id"],
            "founded_at": {"year": 2014, "precision": "Y", "approx": False},
        },
    )
    assert patched.status_code == 200, patched.text
    d = (await _get(client, h, uni, a["slug"])).json()
    assert d["founder_display_name"] == in_set["display_name"]
    assert d["founded_at"]["year"] == 2014
    assert d["stats"]["member_count"] == 2
    assert (d["stats"]["locked_members"], d["stats"]["dead_members"]) == (1, 1)
    # A founder from another universe is refused.
    _, other = await _ctx(client, db_session)
    stranger = await _member(client, h, other)
    assert (
        await _patch(client, h, uni, a["id"], {"founder_id": stranger["id"]})
    ).status_code == 422


async def test_lineage_both_sides_and_cycles(client, db_session):
    h, uni = await _ctx(client, db_session)
    old = await _alliance(client, h, uni, name="Old Bloc")
    new = await _alliance(client, h, uni, name="New Bloc")
    url = f"{A}{new['id']}/lineage?universe_id={uni}"
    r = await client.post(
        url,
        json={"other_id": old["id"], "kind": "SPLINTERED_FROM", "direction": "parent"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert (r.json()["direction"], r.json()["other_name"]) == ("parent", "Old Bloc")
    seen_from_old = (
        await client.get(f"{A}{old['id']}/lineage?universe_id={uni}", headers=h)
    ).json()
    assert [(x["direction"], x["other_name"]) for x in seen_from_old] == [("child", "New Bloc")]
    # The reverse edge would make each its own ancestor.
    loop = await client.post(
        f"{A}{old['id']}/lineage?universe_id={uni}",
        json={"other_id": new["id"], "kind": "SPLINTERED_FROM", "direction": "parent"},
        headers=h,
    )
    assert loop.status_code == 409
    lid = r.json()["id"]
    end = await client.post(
        f"{A}{new['id']}/lineage/{lid}/end?universe_id={uni}",
        json={"until_date": {"year": 2020, "precision": "Y", "approx": False}},
        headers=h,
    )
    assert end.status_code == 204
    detail = (await _get(client, h, uni, new["id"])).json()
    assert detail["lineage"][0]["is_current"] is False
    assert (
        await client.delete(f"{A}{new['id']}/lineage/{lid}?universe_id={uni}", headers=h)
    ).status_code == 204
    # Deleting an alliance takes its lineage with it.
    again = await client.post(
        url, json={"other_id": old["id"], "kind": "RENAMED_FROM", "direction": "parent"}, headers=h
    )
    assert again.status_code == 201
    assert (await client.delete(f"{A}{old['id']}?universe_id={uni}", headers=h)).status_code == 204
    assert (await client.get(url, headers=h)).json() == []


async def test_activity_feed_covers_alliance_and_its_sets(client, db_session):
    attach_audit_listeners()
    h, uni = await _ctx(client, db_session)
    s = (
        await client.post(
            "/api/v1/sets/", json={"universe_id": uni, "name": f"S {_uid()}"}, headers=h
        )
    ).json()
    a = await _alliance(client, h, uni, name="Bloc", set_ids=[s["id"]])
    await _patch(client, h, uni, a["id"], {"description": "x"})
    feed = (await client.get(f"{A}{a['id']}/activity?universe_id={uni}", headers=h)).json()
    kinds = {e["entity_type"] for e in feed}
    assert "alliance" in kinds
    assert any(e["entity_type"] == "alliance" and "description" in e["diff_keys"] for e in feed)
