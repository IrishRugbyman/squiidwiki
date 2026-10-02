"""A set in more than one alliance: `alliance_set`, with `sets.alliance_id` as the
mirror of the primary (position 0)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _admin(client: AsyncClient, session: AsyncSession) -> dict:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _universe(client: AsyncClient, h: dict) -> str:
    resp = await client.post(
        "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=h
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _alliance(client: AsyncClient, h: dict, uni: str, name: str, **fields) -> str:
    resp = await client.post(
        "/api/v1/alliances/", json={"universe_id": uni, "name": name, **fields}, headers=h
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _set(client: AsyncClient, h: dict, uni: str, **fields) -> dict:
    resp = await client.post(
        "/api/v1/sets/", json={"universe_id": uni, "name": f"Set {_uid()}", **fields}, headers=h
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _get(client: AsyncClient, h: dict, uni: str, set_id: str) -> dict:
    resp = await client.get(f"/api/v1/sets/{set_id}?universe_id={uni}", headers=h)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _patch(client: AsyncClient, h: dict, uni: str, set_id: str, body: dict):
    return await client.patch(f"/api/v1/sets/{set_id}?universe_id={uni}", json=body, headers=h)


async def test_two_alliances_keep_order_and_mirror_the_primary(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    tmcne, rhn = await _alliance(client, h, uni, "TMCNE"), await _alliance(client, h, uni, "RHN")
    tmc = await _set(client, h, uni, alliance_ids=[tmcne, rhn])
    assert (tmc["alliance_ids"], tmc["alliance_id"]) == ([tmcne, rhn], tmcne)

    listed = (
        await client.get(f"/api/v1/sets/?universe_id={uni}&alliance_id={rhn}", headers=h)
    ).json()["items"]
    # The filter matches a set on any of its alliances, not only the primary.
    assert [s["id"] for s in listed] == [tmc["id"]]
    assert [a["name"] for a in listed[0]["alliances"]] == ["TMCNE", "RHN"]
    assert listed[0]["alliance_name"] == "TMCNE"

    for aid in (tmcne, rhn):
        page = (await client.get(f"/api/v1/alliances/{aid}?universe_id={uni}", headers=h)).json()
        assert page["set_ids"] == [tmc["id"]]


async def test_legacy_alliance_id_promotes_and_keeps_the_rest(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a, b = await _alliance(client, h, uni, "A"), await _alliance(client, h, uni, "B")
    s = await _set(client, h, uni, alliance_id=a)
    assert s["alliance_ids"] == [a]

    r = await _patch(client, h, uni, s["id"], {"alliance_id": b})
    assert (r.json()["alliance_ids"], r.json()["alliance_id"]) == ([b, a], b)
    # A PATCH that does not mention alliances leaves them alone.
    r = await _patch(client, h, uni, s["id"], {"bio": "x"})
    assert r.json()["alliance_ids"] == [b, a]
    r = await _patch(client, h, uni, s["id"], {"alliance_id": None})
    assert (r.json()["alliance_ids"], r.json()["alliance_id"]) == ([], None)


async def test_alliance_side_edits_leave_the_sets_other_alliances(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a, b = await _alliance(client, h, uni, "A"), await _alliance(client, h, uni, "B")
    s = await _set(client, h, uni, alliance_ids=[a])

    # Joining B from B's page adds it after A; A stays primary.
    await client.patch(
        f"/api/v1/alliances/{b}?universe_id={uni}", json={"set_ids": [s["id"]]}, headers=h
    )
    got = await _get(client, h, uni, s["id"])
    assert (got["alliance_ids"], got["alliance_id"]) == ([a, b], a)

    # Dropping it from A's page promotes B.
    await client.patch(f"/api/v1/alliances/{a}?universe_id={uni}", json={"set_ids": []}, headers=h)
    got = await _get(client, h, uni, s["id"])
    assert (got["alliance_ids"], got["alliance_id"]) == ([b], b)

    # Deleting B leaves the set with none.
    resp = await client.delete(f"/api/v1/alliances/{b}?universe_id={uni}", headers=h)
    assert resp.status_code == 204
    got = await _get(client, h, uni, s["id"])
    assert (got["alliance_ids"], got["alliance_id"]) == ([], None)


async def test_joining_a_second_alliance_befriends_its_sets(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a, b = await _alliance(client, h, uni, "A"), await _alliance(client, h, uni, "B")
    in_a = await _set(client, h, uni, alliance_ids=[a])
    in_b = await _set(client, h, uni, alliance_ids=[b])
    s = await _set(client, h, uni, alliance_ids=[a])
    r = await _patch(client, h, uni, s["id"], {"alliance_ids": [a, b]})
    assert r.status_code == 200, r.text
    got = await _get(client, h, uni, s["id"])
    assert set(got["friend_ids"]) >= {in_a["id"], in_b["id"]}


async def test_foreign_alliance_is_refused(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni, other = await _universe(client, h), await _universe(client, h)
    foreign = await _alliance(client, h, other, "Elsewhere")
    s = await _set(client, h, uni)
    r = await _patch(client, h, uni, s["id"], {"alliance_ids": [foreign]})
    assert r.status_code == 422


async def test_set_inherits_links_from_every_alliance(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a, b, rival = (
        await _alliance(client, h, uni, "A"),
        await _alliance(client, h, uni, "B"),
        await _alliance(client, h, uni, "Rival"),
    )
    s = await _set(client, h, uni, alliance_ids=[a, b])
    resp = await client.post(
        f"/api/v1/alliances/{b}/relationships?universe_id={uni}",
        json={"target_alliance_id": rival, "type": "ENEMY"},
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    links = (
        await client.get(
            f"/api/v1/sets/{s['id']}/alliance-relationships?universe_id={uni}", headers=h
        )
    ).json()
    assert [(x["other_name"], x["via_alliance_name"]) for x in links] == [("Rival", "B")]

    # A set in the alliance cannot be named as its enemy, whatever its position.
    resp = await client.post(
        f"/api/v1/alliances/{b}/relationships?universe_id={uni}",
        json={"target_set_id": s["id"], "type": "ENEMY"},
        headers=h,
    )
    assert resp.status_code == 422
