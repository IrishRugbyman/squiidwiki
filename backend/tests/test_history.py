"""GET /history/{entity_type}/{entity_id}: per-entity change history from audit_log."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners, link_delta
from app.core.enums import GlobalRole
from app.crud.history import diff_snapshots

# No module-level asyncio mark: asyncio_mode=auto (pytest.ini) runs the async
# tests on the session loop, and the pure tests below are synchronous.
# The ASGI test client skips the app lifespan, where the listeners are attached.
attach_audit_listeners()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _login(client: AsyncClient, session: AsyncSession, role: GlobalRole) -> tuple[dict, str]:
    email = f"hist_{_uid()}@example.com"
    await create_user(session, email, "pass1234", role)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}, email


async def _universe(client: AsyncClient, h: dict) -> str:
    resp = await client.post(
        "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=h
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _post(client: AsyncClient, h: dict, path: str, body: dict) -> dict:
    resp = await client.post(path, json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _history(client, h, uni, kind, eid, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    return await client.get(f"/api/v1/history/{kind}/{eid}?universe_id={uni}&{q}", headers=h)


# --- pure helpers ----------------------------------------------------------


def test_diff_snapshots_reports_only_changed_fields():
    prev = {"id": "x", "nickname": "A", "biography": "", "status": "FREE", "updated_at": "t1"}
    cur = {
        "id": "x",
        "nickname": "A",
        "biography": "New text",
        "status": "DEAD",
        "updated_at": "t2",
    }
    changes = {c.field: c for c in diff_snapshots(prev, cur)}
    assert set(changes) == {"biography", "status"}
    assert changes["biography"].kind == "text"
    assert (changes["status"].old, changes["status"].new, changes["status"].kind) == (
        "FREE",
        "DEAD",
        "scalar",
    )


def test_diff_snapshots_treats_empty_values_as_equal():
    assert diff_snapshots({"aliases": None}, {"aliases": []}) == []


def test_link_delta_added_removed_changed():
    before = [{"set_id": "a", "rank": None}, {"set_id": "b", "rank": None}]
    after = [{"set_id": "b", "rank": "OG"}, {"set_id": "c", "rank": None}]
    d = link_delta("set_id", before, after)
    assert d["added"] == [{"set_id": "c", "rank": None}]
    assert d["removed"] == [{"set_id": "a", "rank": None}]
    assert d["changed"] == [{"key": "b", "from": {"rank": None}, "to": {"rank": "OG"}}]
    assert d["_related"] == ["a", "b", "c"]
    assert link_delta("set_id", after, after) is None


# --- endpoint --------------------------------------------------------------


async def test_member_history_shows_field_diffs_newest_first(
    client: AsyncClient, db_session: AsyncSession
):
    h, email = await _login(client, db_session, GlobalRole.ADMIN)
    uni = await _universe(client, h)
    m = await _post(client, h, "/api/v1/members/", {"universe_id": uni, "nickname": "Member A"})
    resp = await client.patch(
        f"/api/v1/members/{m['id']}?universe_id={uni}",
        json={"biography": "Opened a studio.", "status": "LOCKED"},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    # A save that changes nothing visible adds no entry.
    await client.patch(
        f"/api/v1/members/{m['id']}?universe_id={uni}", json={"status": "LOCKED"}, headers=h
    )

    resp = await _history(client, h, uni, "member", m["id"])
    assert resp.status_code == 200, resp.text
    page = resp.json()
    assert page["total"] == 2
    newest, created = page["items"]
    assert newest["action"] == "UPDATE" and created["action"] == "CREATE"
    assert newest["actor"]["email"] == email
    changes = {c["field"]: c for c in newest["changes"]}
    assert set(changes) == {"biography", "status"}
    assert changes["biography"]["kind"] == "text"
    assert (changes["status"]["old"], changes["status"]["new"]) == ("UNKNOWN", "LOCKED")
    assert "nickname" in {c["field"] for c in created["changes"]}


async def test_who_put_a_member_in_a_set_is_on_both_pages(
    client: AsyncClient, db_session: AsyncSession
):
    h, email = await _login(client, db_session, GlobalRole.ADMIN)
    uni = await _universe(client, h)
    s1 = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Set {_uid()}"})
    s2 = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Set {_uid()}"})
    m = await _post(client, h, "/api/v1/members/", {"universe_id": uni, "nickname": "Member B"})

    url = f"/api/v1/members/{m['id']}?universe_id={uni}"
    await client.patch(url, json={"affiliations": [{"set_id": s1["id"]}]}, headers=h)
    # Re-saving the same list is not a change.
    await client.patch(url, json={"affiliations": [{"set_id": s1["id"]}]}, headers=h)
    await client.patch(
        url,
        json={"affiliations": [{"set_id": s1["id"], "rank": "CEO"}, {"set_id": s2["id"]}]},
        headers=h,
    )

    page = (await _history(client, h, uni, "member", m["id"])).json()
    links = [e for e in page["items"] if e["link"] == "sets"]
    assert len(links) == 2
    latest, first = links
    assert first["actor"]["email"] == email
    assert [r["set_id"] for r in first["added"]] == [s1["id"]]
    assert [r["set_id"] for r in latest["added"]] == [s2["id"]]
    assert [c["key"] for c in latest["changed"]] == [s1["id"]]
    assert (latest["changed"][0]["from"]["rank"], latest["changed"][0]["to"]["rank"]) == (
        None,
        "CEO",
    )
    assert page["labels"][s2["id"]]["label"] == s2["name"]

    # The set's own page sees the member being added, scoped to that set only.
    page = (await _history(client, h, uni, "set", s2["id"])).json()
    via = [e for e in page["items"] if not e["is_self"]]
    assert len(via) == 1
    assert via[0]["entity_type"] == "member" and via[0]["entity_id"] == m["id"]
    assert [r["set_id"] for r in via[0]["added"]] == [s2["id"]]
    assert via[0]["changed"] == []
    assert page["labels"][m["id"]]["label"] == "Member B"

    # Ending the spell is recorded as a change to that link.
    member = (await client.get(url, headers=h)).json()
    aff = next(a for a in member["affiliations"] if a["set_id"] == s2["id"])
    resp = await client.post(
        f"/api/v1/members/{m['id']}/affiliations/{aff['id']}/end?universe_id={uni}",
        json={"until_date": {"year": 2024, "precision": "Y"}},
        headers=h,
    )
    assert resp.status_code == 204, resp.text
    latest = (await _history(client, h, uni, "member", m["id"])).json()["items"][0]
    assert latest["link"] == "sets"
    assert latest["changed"][0]["key"] == s2["id"]
    assert latest["changed"][0]["to"]["until_date"]["year"] == 2024


async def test_incident_participants_show_on_member_history(
    client: AsyncClient, db_session: AsyncSession
):
    h, _ = await _login(client, db_session, GlobalRole.ADMIN)
    uni = await _universe(client, h)
    m = await _post(client, h, "/api/v1/members/", {"universe_id": uni, "nickname": "Member C"})
    src = await _post(
        client,
        h,
        "/api/v1/sources/",
        {"universe_id": uni, "url": "https://example.com/a", "title": "Test Article"},
    )
    inc = await _post(
        client,
        h,
        "/api/v1/incidents/",
        {
            "universe_id": uni,
            "type": "SHOOTING",
            "date": {"year": 2022, "precision": "Y"},
            "participants": [{"member_id": m["id"], "role": "VICTIM", "outcome": "INJURED"}],
            "source_ids": [src["id"]],
        },
    )
    page = (await _history(client, h, uni, "incident", inc["id"])).json()
    assert {e["link"] for e in page["items"] if e["link"]} == {"participants", "sources"}
    assert page["labels"][src["id"]]["label"] == "Test Article"

    page = (await _history(client, h, uni, "member", m["id"])).json()
    via = [e for e in page["items"] if e["link"] == "participants"]
    assert len(via) == 1 and via[0]["entity_id"] == inc["id"]
    assert via[0]["added"][0]["role"] == "VICTIM"
    assert page["labels"][inc["id"]]["type"] == "incident"


async def test_history_paginates(client: AsyncClient, db_session: AsyncSession):
    h, _ = await _login(client, db_session, GlobalRole.ADMIN)
    uni = await _universe(client, h)
    m = await _post(client, h, "/api/v1/members/", {"universe_id": uni, "nickname": "Member D"})
    for i in range(4):
        await client.patch(
            f"/api/v1/members/{m['id']}?universe_id={uni}",
            json={"biography": f"Version {i}"},
            headers=h,
        )
    first = (await _history(client, h, uni, "member", m["id"], limit=2)).json()
    second = (await _history(client, h, uni, "member", m["id"], limit=2, offset=2)).json()
    assert first["total"] == second["total"] == 5
    assert [len(first["items"]), len(second["items"])] == [2, 2]
    assert first["items"][0]["changes"][0]["new"] == "Version 3"
    assert {e["id"] for e in first["items"]}.isdisjoint({e["id"] for e in second["items"]})


async def test_history_is_admin_only_and_universe_scoped(
    client: AsyncClient, db_session: AsyncSession
):
    admin, _ = await _login(client, db_session, GlobalRole.ADMIN)
    user, _ = await _login(client, db_session, GlobalRole.USER)
    uni = await _universe(client, admin)
    other = await _universe(client, admin)
    m = await _post(client, admin, "/api/v1/members/", {"universe_id": uni, "nickname": "Member E"})

    assert (await _history(client, user, uni, "member", m["id"])).status_code == 403
    assert (await _history(client, admin, other, "member", m["id"])).status_code == 404
    assert (await _history(client, admin, uni, "member", uuid.uuid4())).status_code == 404
    assert (await _history(client, admin, uni, "widget", m["id"])).status_code == 422
