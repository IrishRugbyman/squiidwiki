"""Regression tests for the follow-ups to the 2026-11 correctness review.

Each test states the documented contract or HTTP rule it checks. All names
and numbers are invented.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.audit import attach_audit_listeners
from app.core.enums import GlobalRole

# The ASGI test client skips the lifespan, where the audit listeners attach.
attach_audit_listeners()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _admin(client: AsyncClient, session: AsyncSession) -> dict:
    email = f"followup_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _post(client: AsyncClient, h: dict, path: str, body: dict) -> dict:
    resp = await client.post(path, json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _universe(client: AsyncClient, h: dict) -> str:
    return (
        await _post(
            client, h, "/api/v1/universes/", {"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}
        )
    )["id"]


async def _status(session: AsyncSession, call) -> tuple[int, str]:
    """Status of a request, with an unhandled server error counted as a 500.

    The ASGI transport re-raises what the app did not handle, and a failed
    flush leaves the shared session unusable for the tests after this one.
    """
    try:
        resp = await call
    except Exception as e:  # noqa: BLE001 - the point is to see any crash
        await session.rollback()
        return 500, repr(e)
    return resp.status_code, resp.text


async def _member(client: AsyncClient, h: dict, uni: str, nickname: str) -> str:
    return (await _post(client, h, "/api/v1/members/", {"universe_id": uni, "nickname": nickname}))[
        "id"
    ]


# --- 1. duplicate participants ------------------------------------------------


async def test_the_same_member_twice_in_an_incident_is_a_422(
    client: AsyncClient, db_session: AsyncSession
):
    """A member takes part in an incident once (incident_participant's key is
    incident + member), with one role and one outcome. Listing him twice is bad
    input, so a 422 that says so, on create and on update, and nothing written."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    twice = await _member(client, h, uni, "Followup Twice")
    once = await _member(client, h, uni, "Followup Once")
    participants = [
        {"member_id": twice, "role": "SHOOTER", "outcome": "UNHARMED"},
        {"member_id": once, "role": "VICTIM", "outcome": "INJURED"},
        {"member_id": twice, "role": "VICTIM", "outcome": "KILLED"},
    ]

    code, body = await _status(
        db_session,
        client.post(
            "/api/v1/incidents/",
            json={"universe_id": uni, "type": "SHOOTING", "participants": participants},
            headers=h,
        ),
    )
    assert code == 422, body
    assert twice in body and "more than once" in body

    incident = await _post(
        client,
        h,
        "/api/v1/incidents/",
        {"universe_id": uni, "type": "SHOOTING", "participants": participants[:2]},
    )
    code, body = await _status(
        db_session,
        client.patch(
            f"/api/v1/incidents/{incident['id']}?universe_id={uni}",
            json={"participants": participants},
            headers=h,
        ),
    )
    assert code == 422, body
    assert twice in body and "more than once" in body

    got = (
        await client.get(f"/api/v1/incidents/{incident['id']}?universe_id={uni}", headers=h)
    ).json()
    assert sorted(p["member_id"] for p in got["participants"]) == sorted([twice, once])
    # The refused edit marked nobody dead.
    member = (await client.get(f"/api/v1/members/{twice}?universe_id={uni}", headers=h)).json()
    assert member["status"] != "DEAD"


async def test_the_same_set_twice_in_an_incident_is_a_422(
    client: AsyncClient, db_session: AsyncSession
):
    """incident_set_participant is keyed on incident + set the same way."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    s = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Crew {_uid()}"})
    sets = [
        {"set_id": s["id"], "role": "SHOOTER"},
        {"set_id": s["id"], "role": "VICTIM"},
    ]
    code, body = await _status(
        db_session,
        client.post(
            "/api/v1/incidents/",
            json={"universe_id": uni, "type": "SHOOTING", "set_participants": sets},
            headers=h,
        ),
    )
    assert code == 422, body
    assert s["id"] in body

    incident = await _post(client, h, "/api/v1/incidents/", {"universe_id": uni, "type": "FIGHT"})
    code, body = await _status(
        db_session,
        client.patch(
            f"/api/v1/incidents/{incident['id']}?universe_id={uni}",
            json={"set_participants": sets},
            headers=h,
        ),
    )
    assert code == 422, body


# --- 2. null into a NOT NULL column -------------------------------------------


async def _make(client: AsyncClient, h: dict, db_session: AsyncSession, uni: str, kind: str) -> str:
    """Create one record of `kind` and return the path a PATCH goes to."""
    q = f"?universe_id={uni}"
    if kind == "incident":
        i = await _post(client, h, "/api/v1/incidents/", {"universe_id": uni, "type": "FIGHT"})
        return f"/api/v1/incidents/{i['id']}{q}"
    if kind == "member":
        return f"/api/v1/members/{await _member(client, h, uni, f'Followup {_uid()}')}{q}"
    if kind == "set":
        s = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Crew {_uid()}"})
        return f"/api/v1/sets/{s['id']}{q}"
    if kind == "alliance":
        a = await _post(
            client, h, "/api/v1/alliances/", {"universe_id": uni, "name": f"Bloc {_uid()}"}
        )
        return f"/api/v1/alliances/{a['id']}{q}"
    if kind == "gang":
        g = await _post(client, h, "/api/v1/gangs/", {"universe_id": uni, "name": f"G {_uid()}"})
        return f"/api/v1/gangs/{g['id']}{q}"
    if kind == "universe":
        return f"/api/v1/universes/{uni}"
    if kind == "municipality":
        m = await _post(
            client, h, "/api/v1/municipalities/", {"universe_id": uni, "name": f"Town {_uid()}"}
        )
        return f"/api/v1/municipalities/{m['id']}{q}"
    if kind == "source":
        s = await _post(
            client,
            h,
            "/api/v1/sources/",
            {"universe_id": uni, "url": f"https://example.com/{_uid()}", "title": "A page"},
        )
        return f"/api/v1/sources/{s['id']}{q}"
    if kind == "research":
        n = await _post(client, h, "/api/v1/research/", {"universe_id": uni, "title": "A note"})
        return f"/api/v1/research/{n['id']}{q}"
    if kind == "business":
        b = await _post(
            client,
            h,
            "/api/v1/businesses/",
            {"universe_id": uni, "name": f"Shop {_uid()}", "business_type": "NIGHTLIFE"},
        )
        return f"/api/v1/businesses/{b['id']}{q}"
    if kind == "media":
        from app.models.media import Media

        mid = await _member(client, h, uni, f"Followup {_uid()}")
        m = Media(
            universe_id=uuid.UUID(uni),
            member_id=uuid.UUID(mid),
            kind="EXTERNAL_URL",
            external_url="https://example.com/photo.jpg",
        )
        db_session.add(m)
        await db_session.commit()
        return f"/api/v1/media/{m.id}{q}"
    raise AssertionError(kind)


# PATCH fields whose column is NOT NULL and whose update wrote a null into it
# (a 500). Null is not a value these columns can hold, and nothing documents
# it as "reset to the default", so a PATCH sending it is bad input: a 422
# naming the field. Fields whose update already reads null as "no change" or
# "empty list" (municipality kind, citation source, court case and defendant
# fields, a spell's life_sentence) are not listed: they never failed.
NOT_NULL_FIELDS = [
    ("incident", "type"),
    ("incident", "verified"),
    ("member", "nickname_unknown"),
    ("member", "is_rapper"),
    ("member", "is_snitch"),
    ("member", "status"),
    ("member", "biography"),
    ("set", "status"),
    ("alliance", "status"),
    ("gang", "name"),
    ("universe", "name"),
    ("universe", "slug"),
    ("municipality", "name"),
    ("source", "url"),
    ("source", "title"),
    ("source", "reliability"),
    ("source", "kind"),
    ("research", "title"),
    ("research", "content"),
    ("research", "kind"),
    ("business", "name"),
    ("business", "business_type"),
    ("business", "status"),
    ("media", "is_primary"),
]


@pytest.mark.parametrize(("kind", "field"), NOT_NULL_FIELDS)
async def test_patching_a_required_field_to_null_is_a_422(
    client: AsyncClient, db_session: AsyncSession, kind: str, field: str
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    path = await _make(client, h, db_session, uni, kind)
    code, body = await _status(db_session, client.patch(path, json={field: None}, headers=h))
    assert code == 422, (kind, field, code, body)
    assert field in body


# --- 3. join-table changes reach History --------------------------------------


async def _history(client: AsyncClient, h: dict, uni: str, kind: str, eid: str) -> list[dict]:
    resp = await client.get(f"/api/v1/history/{kind}/{eid}?universe_id={uni}", headers=h)
    assert resp.status_code == 200, resp.text
    return resp.json()["items"]


def _links(items: list[dict], link: str) -> list[dict]:
    return [e for e in items if e["link"] == link]


async def _link_rows(session: AsyncSession, entity_type: str, eid: str) -> list[dict]:
    """The link-change audit rows written on one entity, oldest first."""
    from sqlalchemy import text

    rows = (
        await session.execute(
            text(
                "SELECT diff_json FROM audit_log WHERE entity_type = :t AND entity_id = :i "
                "AND diff_json ? '_link' ORDER BY created_at, id"
            ),
            {"t": entity_type, "i": eid},
        )
    ).scalars()
    return list(rows)


async def test_set_ally_and_enemy_edits_reach_history(
    client: AsyncClient, db_session: AsyncSession
):
    """Every join-table sync calls record_link_change (backend/CLAUDE.md). A
    set's allies and enemies are a join table, so editing them shows on its
    History, and on the other set's through _related."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)

    async def crew() -> str:
        return (
            await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"Crew {_uid()}"})
        )["id"]

    me, friend, foe = await crew(), await crew(), await crew()
    resp = await client.patch(
        f"/api/v1/sets/{me}?universe_id={uni}",
        json={"friend_ids": [friend], "enemy_ids": [foe]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    items = await _history(client, h, uni, "set", me)
    assert [r["set_id"] for e in _links(items, "allies") for r in e["added"]] == [friend]
    assert [r["set_id"] for e in _links(items, "enemies") for r in e["added"]] == [foe]
    # The other side sees it too.
    theirs = _links(await _history(client, h, uni, "set", foe), "enemies")
    assert len(theirs) == 1 and theirs[0]["entity_id"] == me

    # The ally turns enemy: off one list, onto the other.
    resp = await client.patch(
        f"/api/v1/sets/{me}?universe_id={uni}",
        json={"friend_ids": [], "enemy_ids": [foe, friend]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    items = await _history(client, h, uni, "set", me)
    assert [r["set_id"] for e in _links(items, "allies") for r in e["removed"]] == [friend]
    newest_enemies = _links(items, "enemies")[0]  # newest first
    assert [r["set_id"] for r in newest_enemies["added"]] == [friend]

    # A save that changes nothing records nothing.
    before = len(await _history(client, h, uni, "set", me))
    resp = await client.patch(
        f"/api/v1/sets/{me}?universe_id={uni}",
        json={"friend_ids": [], "enemy_ids": [foe, friend]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    assert len(await _history(client, h, uni, "set", me)) == before


async def test_allies_made_by_joining_an_alliance_reach_history(
    client: AsyncClient, db_session: AsyncSession
):
    """Joining an alliance befriends its sets (CLAUDE.md). Those allies are
    written to the same join table, so they reach History the same way, whether
    the set joins (set PATCH) or the alliance takes it in (alliance PATCH)."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    bloc = await _post(
        client, h, "/api/v1/alliances/", {"universe_id": uni, "name": f"Bloc {_uid()}"}
    )
    elder = await _post(
        client,
        h,
        "/api/v1/sets/",
        {"universe_id": uni, "name": f"Elder {_uid()}", "alliance_ids": [bloc["id"]]},
    )
    joiner = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"J {_uid()}"})
    resp = await client.patch(
        f"/api/v1/sets/{joiner['id']}?universe_id={uni}",
        json={"alliance_ids": [bloc["id"]]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    allies = _links(await _history(client, h, uni, "set", joiner["id"]), "allies")
    assert [r["set_id"] for e in allies for r in e["added"]] == [elder["id"]]
    assert _links(await _history(client, h, uni, "set", elder["id"]), "allies")

    # From the alliance's side: its set_ids gain a set.
    late = await _post(client, h, "/api/v1/sets/", {"universe_id": uni, "name": f"L {_uid()}"})
    resp = await client.patch(
        f"/api/v1/alliances/{bloc['id']}?universe_id={uni}",
        json={"set_ids": [elder["id"], joiner["id"], late["id"]]},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    # Each new pair is recorded once, on one of its sets; the other sees it
    # through _related, filtered to the rows about itself.
    allies = _links(await _history(client, h, uni, "set", late["id"]), "allies")
    got = sorted(
        r["set_id"] if e["is_self"] else e["entity_id"] for e in allies for r in e["added"]
    )
    assert got == sorted([elder["id"], joiner["id"]])
