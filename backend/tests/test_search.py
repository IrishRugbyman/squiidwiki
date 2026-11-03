"""Fuzzy (pg_trgm) name search, the duplicate check, and full-text search.

Every name here is invented; nothing in this repository may name a person.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole
from app.crud.text_search import _segments

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _setup(client: AsyncClient, session: AsyncSession) -> tuple[dict, str]:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    token = (await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=headers
    )
    assert resp.status_code == 201
    return headers, resp.json()["id"]


async def _member(client, headers, universe_id, **fields) -> dict:
    resp = await client.post("/api/v1/members/", json={"universe_id": universe_id, **fields}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _names(client, headers, path: str) -> list[str]:
    resp = await client.get(path, headers=headers)
    assert resp.status_code == 200, resp.text
    return [r.get("display_name") or r.get("name") or r.get("title") for r in resp.json()]


# ── Fuzzy name search ─────────────────────────────────────────────────────────


async def test_member_search_finds_a_misspelling(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    await _member(client, headers, uid, nickname="Lil Quorvy")
    await _member(client, headers, uid, nickname="Zephyr")
    names = await _names(client, headers, f"/api/v1/members/search?universe_id={uid}&q=Lil%20Quorvo")
    assert names == ["Lil Quorvy"]


async def test_member_search_ranks_substring_hits_before_near_misses(
    client: AsyncClient, db_session: AsyncSession
):
    headers, uid = await _setup(client, db_session)
    await _member(client, headers, uid, nickname="Brannoc")  # near miss
    await _member(client, headers, uid, nickname="Big Brannock")  # contains the query
    names = await _names(client, headers, f"/api/v1/members/search?universe_id={uid}&q=Brannock")
    assert names == ["Big Brannock", "Brannoc"]


async def test_member_search_scores_legal_names_and_alias_rows(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    m = await _member(client, headers, uid, nickname="Ghosty", legal_name="Orrin Vellacott")
    other = await _member(client, headers, uid, nickname="Quill")
    resp = await client.post(
        f"/api/v1/members/{other['id']}/aliases?universe_id={uid}",
        json={"alias": "Thimblewick"},
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text
    assert await _names(client, headers, f"/api/v1/members/search?universe_id={uid}&q=Orin%20Velacott") == [
        m["display_name"]
    ]
    assert await _names(client, headers, f"/api/v1/members/search?universe_id={uid}&q=Thimblewik") == [
        "Quill"
    ]


async def test_member_search_does_not_join_unrelated_names(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    await _member(client, headers, uid, nickname="Pellinor")
    assert await _names(client, headers, f"/api/v1/members/search?universe_id={uid}&q=Pastomir") == []


async def test_short_queries_stay_substring_only(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    await _member(client, headers, uid, nickname="Kx")
    await _member(client, headers, uid, nickname="Kqzz")
    assert await _names(client, headers, f"/api/v1/members/search?universe_id={uid}&q=Kx") == ["Kx"]


async def test_set_alliance_and_source_search_are_fuzzy(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    assert (
        await client.post(
            "/api/v1/sets/", json={"universe_id": uid, "name": "Marrowgate Boys"}, headers=headers
        )
    ).status_code == 201
    assert (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": uid, "name": "Quellmere Union", "status": "ACTIVE"},
            headers=headers,
        )
    ).status_code == 201
    assert (
        await client.post(
            "/api/v1/sources/",
            json={
                "universe_id": uid,
                "url": "https://example.com/a",
                "title": "Harrowfield Gazette report",
                "reliability": "HIGH",
            },
            headers=headers,
        )
    ).status_code == 201
    assert await _names(client, headers, f"/api/v1/sets/search?universe_id={uid}&q=Marowgate") == [
        "Marrowgate Boys"
    ]
    assert await _names(client, headers, f"/api/v1/alliances/search?universe_id={uid}&q=Quelmere") == [
        "Quellmere Union"
    ]
    assert await _names(client, headers, f"/api/v1/sources/search?universe_id={uid}&q=Harowfield") == [
        "Harrowfield Gazette report"
    ]


async def test_set_search_ignores_variant_key_names(client: AsyncClient, db_session: AsyncSession):
    """name_variants is JSON; its keys ("initials", "number") must not match."""
    headers, uid = await _setup(client, db_session)
    await client.post("/api/v1/sets/", json={"universe_id": uid, "name": "Velvet Crew"}, headers=headers)
    assert await _names(client, headers, f"/api/v1/sets/search?universe_id={uid}&q=initals") == []


async def test_search_stays_in_its_universe(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    _, other_uid = await _setup(client, db_session)
    await _member(client, headers, other_uid, nickname="Farrowind")
    assert await _names(client, headers, f"/api/v1/members/search?universe_id={uid}&q=Farowind") == []


# ── Duplicate check ───────────────────────────────────────────────────────────


async def test_similar_members_flags_a_near_duplicate(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    existing = await _member(client, headers, uid, nickname="Dorian Wexford")
    await _member(client, headers, uid, nickname="Pellam")
    resp = await client.get(
        f"/api/v1/members/similar?universe_id={uid}&name=Dorian%20Wexley", headers=headers
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert [r["member"]["id"] for r in rows] == [existing["id"]]
    assert 0.5 <= rows[0]["score"] < 1.0


async def test_similar_members_exact_match_scores_one_and_exclude_id(
    client: AsyncClient, db_session: AsyncSession
):
    headers, uid = await _setup(client, db_session)
    m = await _member(client, headers, uid, nickname="Corvane")
    rows = (
        await client.get(f"/api/v1/members/similar?universe_id={uid}&name=Corvane", headers=headers)
    ).json()
    assert rows[0]["score"] == 1.0
    rows = (
        await client.get(
            f"/api/v1/members/similar?universe_id={uid}&name=Corvane&exclude_id={m['id']}", headers=headers
        )
    ).json()
    assert rows == []


# ── Full-text search ──────────────────────────────────────────────────────────


async def test_text_search_finds_biography_words_with_stemming(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    m = await _member(
        client,
        headers,
        uid,
        nickname="Tessaly",
        biography="Ran the corner store on the north block and took the charges for his crew.",
    )
    await _member(client, headers, uid, nickname="Other", biography="Nothing relevant here.")
    resp = await client.get(f"/api/v1/search/text?universe_id={uid}&q=charged%20crew", headers=headers)
    assert resp.status_code == 200, resp.text
    hits = resp.json()
    assert [(h["entity_type"], h["id"]) for h in hits] == [("member", m["id"])]
    assert hits[0]["label"] == "Tessaly"
    assert any(s["hit"] for s in hits[0]["snippet"])
    assert "".join(s["text"] for s in hits[0]["snippet"]).find("took the charges") >= 0


async def test_text_search_covers_sources_and_incidents(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    src = (
        await client.post(
            "/api/v1/sources/",
            json={
                "universe_id": uid,
                "url": "https://example.com/b",
                "title": "Weekly digest",
                "reliability": "MEDIUM",
                "notes": "Mentions a teenager from the lantern district.",
            },
            headers=headers,
        )
    ).json()
    inc = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": uid,
                "type": "SHOOTING",
                "narrative": "Shots fired outside the lantern district bakery.",
                "date": {"year": 2022, "precision": "Y", "approx": False},
            },
            headers=headers,
        )
    ).json()
    hits = (
        await client.get(f"/api/v1/search/text?universe_id={uid}&q=lantern%20district", headers=headers)
    ).json()
    assert {(h["entity_type"], h["id"]) for h in hits} == {("source", src["id"]), ("incident", inc["id"])}
    only = (
        await client.get(f"/api/v1/search/text?universe_id={uid}&q=lantern&types=source", headers=headers)
    ).json()
    assert [h["entity_type"] for h in only] == ["source"]


async def test_text_search_phrase_and_exclusion_syntax(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    a = await _member(client, headers, uid, nickname="Alder", biography="Known for the silver coupe.")
    await _member(client, headers, uid, nickname="Birch", biography="Silver chain, red coupe.")
    hits = (
        await client.get(f'/api/v1/search/text?universe_id={uid}&q="silver coupe"', headers=headers)
    ).json()
    assert [h["id"] for h in hits] == [a["id"]]
    hits = (
        await client.get(f"/api/v1/search/text?universe_id={uid}&q=coupe%20-chain", headers=headers)
    ).json()
    assert [h["id"] for h in hits] == [a["id"]]


async def test_text_search_short_query_and_other_universe(client: AsyncClient, db_session: AsyncSession):
    headers, uid = await _setup(client, db_session)
    _, other = await _setup(client, db_session)
    await _member(client, headers, other, nickname="Elsewhere", biography="Ferryman of the quarry road.")
    assert (
        await client.get(f"/api/v1/search/text?universe_id={uid}&q=ferryman", headers=headers)
    ).json() == []
    assert (await client.get(f"/api/v1/search/text?universe_id={other}&q=fe", headers=headers)).json() == []


async def test_segments_split_on_markers():
    assert _segments("a b c") == [
        {"text": "a ", "hit": False},
        {"text": "b", "hit": True},
        {"text": " c", "hit": False},
    ]
    assert _segments("") == []
