"""Citations and the source API built on them (2026-10-04 refactor).

Every expected value is written from the request in the test, never copied
from a response.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


class _Api:
    def __init__(self, client: AsyncClient, token: str, universe_id: str):
        self.client = client
        self.h = {"Authorization": f"Bearer {token}"}
        self.uid = universe_id

    async def post(self, path: str, body: dict, expect: int = 201) -> dict:
        r = await self.client.post(
            path, params={"universe_id": self.uid}, json=body, headers=self.h
        )
        assert r.status_code == expect, r.text
        return r.json()

    async def get(self, path: str, **params) -> dict:
        r = await self.client.get(path, params={"universe_id": self.uid, **params}, headers=self.h)
        assert r.status_code == 200, r.text
        return r.json()

    async def source(self, title: str, url: str | None = None, **kw) -> str:
        body = {"universe_id": self.uid, "title": title, "url": url or f"https://e.x/{_uid()}"}
        return (await self.post("/api/v1/sources/", {**body, **kw}))["id"]

    async def member(self, nickname: str) -> str:
        return (
            await self.post("/api/v1/members/", {"universe_id": self.uid, "nickname": nickname})
        )["id"]

    async def cite(self, source_id: str, entity_type: str, entity_id: str, **kw) -> dict:
        body = {"source_id": source_id, "entity_type": entity_type, "entity_id": entity_id}
        return await self.post("/api/v1/citations/", {**body, **kw})


async def _api(client: AsyncClient, session: AsyncSession, role=GlobalRole.ADMIN) -> _Api:
    email = f"c_{_uid()}@example.com"
    await create_user(session, email, "pw-citations", role)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "pw-citations"})
    ).json()["access_token"]
    r = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return _Api(client, token, r.json()["id"])


# --- citing -----------------------------------------------------------------------


async def test_a_citation_carries_its_detail_onto_the_record(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Indictment", publication="USAO", reliability="HIGH")
    m = await api.member("Person A")
    await api.cite(src, "member", m, locator="p. 12", quote="the words", note="names the set")
    (c,) = (await api.get(f"/api/v1/members/{m}"))["citations"]
    assert (c["locator"], c["quote"], c["note"]) == ("p. 12", "the words", "names the set")
    assert c["source"]["title"] == "Indictment"
    assert c["source"]["publication"] == "USAO"
    assert c["source"]["domain"] == "e.x"


async def test_citing_the_same_source_twice_is_a_conflict_with_the_existing_id(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Doc")
    m = await api.member("Person B")
    first = await api.cite(src, "member", m)
    again = await api.post(
        "/api/v1/citations/",
        {"source_id": src, "entity_type": "member", "entity_id": m},
        expect=409,
    )
    assert again["code"] == "citation_exists"
    assert again["citation_id"] == first["id"]


async def test_a_source_from_another_universe_is_refused(client, db_session):
    here = await _api(client, db_session)
    there = await _api(client, db_session)
    foreign = await there.source("Elsewhere")
    m = await here.member("Person C")
    await here.post(
        "/api/v1/citations/",
        {"source_id": foreign, "entity_type": "member", "entity_id": m},
        expect=422,
    )


async def test_a_record_from_another_universe_is_refused(client, db_session):
    here = await _api(client, db_session)
    there = await _api(client, db_session)
    src = await here.source("Here")
    foreign_member = await there.member("Person D")
    await here.post(
        "/api/v1/citations/",
        {"source_id": src, "entity_type": "member", "entity_id": foreign_member},
        expect=422,
    )


async def test_new_citations_go_after_the_last(client, db_session):
    api = await _api(client, db_session)
    m = await api.member("Person E")
    for title in ("one", "two", "three"):
        await api.cite(await api.source(title), "member", m)
    got = (await api.get(f"/api/v1/members/{m}"))["citations"]
    assert [(c["source"]["title"], c["position"]) for c in got] == [
        ("one", 0),
        ("two", 1),
        ("three", 2),
    ]


async def test_reorder_needs_every_citation_exactly_once(client, db_session):
    api = await _api(client, db_session)
    m = await api.member("Person F")
    a = await api.cite(await api.source("a"), "member", m)
    await api.cite(await api.source("b"), "member", m)
    r = await client.put(
        "/api/v1/citations/order",
        params={"universe_id": api.uid},
        json={"entity_type": "member", "entity_id": m, "ids": [a["id"]]},
        headers=api.h,
    )
    assert r.status_code == 422


async def test_editing_a_citation_and_repointing_it(client, db_session):
    api = await _api(client, db_session)
    m = await api.member("Person G")
    old, new = await api.source("old"), await api.source("new")
    c = await api.cite(old, "member", m)
    r = await client.patch(
        f"/api/v1/citations/{c['id']}",
        params={"universe_id": api.uid},
        json={"locator": "§ 4", "source_id": new},
        headers=api.h,
    )
    assert r.status_code == 200, r.text
    assert (r.json()["locator"], r.json()["source"]["title"]) == ("§ 4", "new")


async def test_batch_is_all_or_nothing(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Batch")
    m = await api.member("Person H")
    items = [
        {"source_id": src, "entity_type": "member", "entity_id": m},
        {"source_id": src, "entity_type": "member", "entity_id": str(uuid.uuid4())},
    ]
    r = await client.post(
        "/api/v1/citations/batch",
        params={"universe_id": api.uid},
        json={"items": items},
        headers=api.h,
    )
    assert r.status_code == 422
    assert (await api.get(f"/api/v1/members/{m}"))["citations"] == []


async def test_batch_update_overwrites_detail_of_an_existing_citation(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Batch")
    m = await api.member("Person I")
    first = await api.cite(src, "member", m)
    r = await client.post(
        "/api/v1/citations/batch",
        params={"universe_id": api.uid},
        json={
            "items": [
                {"source_id": src, "entity_type": "member", "entity_id": m, "locator": "12345-039"}
            ],
            "on_conflict": "update",
        },
        headers=api.h,
    )
    assert r.json() == {"created": [], "updated": [first["id"]], "skipped": []}
    (c,) = (await api.get(f"/api/v1/members/{m}"))["citations"]
    assert c["locator"] == "12345-039"


async def test_deleting_a_record_deletes_its_citations(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Doc")
    m = await api.member("Person J")
    await api.cite(src, "member", m)
    r = await client.delete(f"/api/v1/members/{m}", params={"universe_id": api.uid}, headers=api.h)
    assert r.status_code == 204, r.text
    assert (await api.get(f"/api/v1/sources/{src}"))["counts"]["member"] == 0


async def test_citation_writes_are_audited_with_what_they_linked(client, db_session):
    from app.core.audit import attach_audit_listeners

    attach_audit_listeners()
    api = await _api(client, db_session)
    src = await api.source("Audited")
    m = await api.member("Person K")
    c = await api.cite(src, "member", m)
    await client.delete(
        f"/api/v1/citations/{c['id']}", params={"universe_id": api.uid}, headers=api.h
    )
    rows = (
        await db_session.execute(
            text(
                "SELECT action::text, diff_json FROM audit_log "
                "WHERE entity_type = 'citation' AND entity_id = :id ORDER BY created_at"
            ),
            {"id": c["id"]},
        )
    ).all()
    assert [a for a, _ in rows] == ["CREATE", "DELETE"]
    assert rows[1][1]["member_id"] == m and rows[1][1]["source_id"] == src


async def test_alliances_can_be_cited(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Bloc history")
    alliance = await api.post("/api/v1/alliances/", {"universe_id": api.uid, "name": f"A {_uid()}"})
    await api.cite(src, "alliance", alliance["id"])
    got = await api.get(f"/api/v1/alliances/{alliance['id']}")
    assert [c["source"]["title"] for c in got["citations"]] == ["Bloc history"]


# --- sources --------------------------------------------------------------------------


async def test_a_url_already_on_file_is_a_conflict_unless_allowed(client, db_session):
    api = await _api(client, db_session)
    first = await api.source("Story", url="https://news.example.com/a/")
    dup = await api.post(
        "/api/v1/sources/",
        {"universe_id": api.uid, "title": "Same", "url": "HTTPS://news.example.com/a?utm_source=x"},
        expect=409,
    )
    assert (dup["code"], dup["existing_id"]) == ("duplicate_url", first)
    await api.post(
        "/api/v1/sources/",
        {
            "universe_id": api.uid,
            "title": "Same",
            "url": "https://news.example.com/a",
            "allow_duplicate": True,
        },
    )


async def test_a_lookup_url_points_at_the_system_source_with_the_number(client, db_session):
    api = await _api(client, db_session)
    bop = await api.source("BOP inmate locator", url="https://www.bop.gov/inmateloc/")
    deep = (
        "https://www.bop.gov/PublicInfo/execute/inmateloc?todo=query&output=json"
        "&inmateNum=12345-039&inmateNumType=IRN"
    )
    refused = await api.post(
        "/api/v1/sources/", {"universe_id": api.uid, "title": "x", "url": deep}, expect=409
    )
    assert (refused["code"], refused["existing_id"]) == ("lookup_source", bop)
    assert refused["suggested_locator"] == "12345-039"
    look = await api.get("/api/v1/sources/lookup", url=deep)
    assert look["lookup"]["source"]["id"] == bop
    assert look["lookup"]["suggested_locator"] == "12345-039"


async def test_kind_is_derived_from_the_url_and_can_be_overridden(client, db_session):
    api = await _api(client, db_session)
    ig = await api.source("Post", url="https://www.instagram.com/p/abc/")
    doj = await api.source("Release", url="https://www.justice.gov/x", kind="PRESS")
    assert (await api.get(f"/api/v1/sources/{ig}"))["kind"] == "SOCIAL"
    assert (await api.get(f"/api/v1/sources/{doj}"))["kind"] == "PRESS"


async def test_no_published_date_is_sql_null(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Undated")
    n = (
        await db_session.execute(
            text("SELECT count(*) FROM source WHERE id = :id AND published_at IS NULL"),
            {"id": src},
        )
    ).scalar_one()
    assert n == 1


async def test_list_filters_facets_and_search(client, db_session):
    api = await _api(client, db_session)
    await api.source("Court opinion", url="https://www.courtlistener.com/a", reliability="HIGH")
    await api.source("Thread", url="https://www.reddit.com/r/x/1", reliability="LOW")
    await api.source("Another thread", url="https://www.reddit.com/r/x/2", reliability="LOW")
    page = await api.get("/api/v1/sources/", kind="SOCIAL")
    assert page["total"] == 2
    # Each facet is counted under the other filters but not its own.
    assert page["facets"]["kind"] == {"COURT": 1, "SOCIAL": 2}
    assert page["facets"]["reliability"] == {"LOW": 2}
    found = await api.get("/api/v1/sources/search", q="courtlistener")
    assert [s["title"] for s in found] == ["Court opinion"]


async def test_uncited_filter(client, db_session):
    api = await _api(client, db_session)
    cited = await api.source("cited")
    await api.source("idle")
    await api.cite(cited, "member", await api.member("Person L"))
    page = await api.get("/api/v1/sources/", uncited=True)
    assert [s["title"] for s in page["items"]] == ["idle"]


async def test_source_citations_page_through_records(client, db_session):
    api = await _api(client, db_session)
    src = await api.source("Wide")
    for n in range(3):
        await api.cite(src, "member", await api.member(f"Member {n}"), locator=f"p. {n}")
    first = await api.get(f"/api/v1/sources/{src}/citations", entity_type="member", limit=2)
    rest = await api.get(
        f"/api/v1/sources/{src}/citations", entity_type="member", limit=2, offset=2
    )
    assert first["total"] == 3
    labels = [r["entity"]["label"] for r in first["items"] + rest["items"]]
    assert labels == ["Member 0", "Member 1", "Member 2"]
    assert first["items"][0]["locator"] == "p. 0"


async def test_merge_moves_citations_and_combines_a_collision(client, db_session):
    api = await _api(client, db_session)
    keep, fold = await api.source("keep"), await api.source("fold")
    both, only = await api.member("Both"), await api.member("Only")
    await api.cite(keep, "member", both, locator="1")
    await api.cite(fold, "member", both, locator="2")
    await api.cite(fold, "member", only)
    out = await api.post(f"/api/v1/sources/{fold}/merge", {"into_id": keep}, expect=200)
    assert (out["moved"], out["combined"]) == (1, 1)
    (c,) = (await api.get(f"/api/v1/members/{both}"))["citations"]
    assert (c["source_id"], c["locator"]) == (keep, "1; 2")
    r = await client.get(f"/api/v1/sources/{fold}", params={"universe_id": api.uid}, headers=api.h)
    assert r.status_code == 404


async def test_deleting_a_source_is_admin_only(client, db_session):
    admin = await _api(client, db_session)
    src = await admin.source("mine")
    email = f"u_{_uid()}@example.com"
    await create_user(db_session, email, "pw-citations", GlobalRole.USER)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "pw-citations"})
    ).json()["access_token"]
    r = await client.delete(
        f"/api/v1/sources/{src}",
        params={"universe_id": admin.uid},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
