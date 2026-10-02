"""A set can claim several gangs: set_gang, with sets.gang_id mirroring the first."""

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


async def _gang(client: AsyncClient, h: dict, universe_id: str, name: str) -> str:
    resp = await client.post(
        "/api/v1/gangs/", json={"universe_id": universe_id, "name": name}, headers=h
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _set(client: AsyncClient, h: dict, universe_id: str, **fields) -> dict:
    resp = await client.post(
        "/api/v1/sets/",
        json={"universe_id": universe_id, "name": f"Set {_uid()}", **fields},
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _patch(client: AsyncClient, h: dict, universe_id: str, set_id: str, body: dict):
    return await client.patch(
        f"/api/v1/sets/{set_id}?universe_id={universe_id}", json=body, headers=h
    )


async def test_create_with_two_gangs_keeps_order_and_mirrors_primary(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    gd = await _gang(client, h, uni, "Gangster Disciples")
    sd = await _gang(client, h, uni, "Satan Disciples")

    created = await _set(client, h, uni, gang_ids=[gd, sd])
    assert created["gang_ids"] == [gd, sd]
    assert created["gang_id"] == gd

    detail = (
        await client.get(f"/api/v1/sets/{created['id']}/detail?universe_id={uni}", headers=h)
    ).json()
    assert [g["name"] for g in detail["gangs"]] == ["Gangster Disciples", "Satan Disciples"]
    assert detail["gang_name"] == "Gangster Disciples"

    plain = (await client.get(f"/api/v1/sets/{created['id']}?universe_id={uni}", headers=h)).json()
    assert plain["gang_ids"] == [gd, sd]


async def test_duplicate_gang_ids_are_collapsed(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    gd = await _gang(client, h, uni, "GD")
    sd = await _gang(client, h, uni, "SD")
    created = await _set(client, h, uni, gang_ids=[sd, gd, sd])
    assert created["gang_ids"] == [sd, gd]


async def test_gang_filter_matches_a_secondary_gang(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    gd = await _gang(client, h, uni, "GD")
    sd = await _gang(client, h, uni, "SD")
    both = await _set(client, h, uni, gang_ids=[gd, sd])
    only_gd = await _set(client, h, uni, gang_ids=[gd])
    none = await _set(client, h, uni)

    by_sd = (await client.get(f"/api/v1/sets/?universe_id={uni}&gang_id={sd}", headers=h)).json()
    assert {s["id"] for s in by_sd["items"]} == {both["id"]}
    assert by_sd["total"] == 1

    by_gd = (await client.get(f"/api/v1/sets/?universe_id={uni}&gang_id={gd}", headers=h)).json()
    assert {s["id"] for s in by_gd["items"]} == {both["id"], only_gd["id"]}

    unassigned = (
        await client.get(f"/api/v1/sets/?universe_id={uni}&gang_id=none", headers=h)
    ).json()
    # Also holds the universe's reserved system sets, which claim no gang either.
    ids = {s["id"] for s in unassigned["items"]}
    assert none["id"] in ids
    assert both["id"] not in ids and only_gd["id"] not in ids

    row = next(s for s in by_gd["items"] if s["id"] == both["id"])
    assert [g["id"] for g in row["gangs"]] == [gd, sd]


async def test_patch_gang_ids_replaces_the_list(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a = await _gang(client, h, uni, "A")
    b = await _gang(client, h, uni, "B")
    c = await _gang(client, h, uni, "C")
    s = await _set(client, h, uni, gang_ids=[a, b])

    resp = await _patch(client, h, uni, s["id"], {"gang_ids": [c, a]})
    assert resp.status_code == 200
    assert resp.json()["gang_ids"] == [c, a]
    assert resp.json()["gang_id"] == c

    resp = await _patch(client, h, uni, s["id"], {"gang_ids": []})
    assert resp.json()["gang_ids"] == []
    assert resp.json()["gang_id"] is None


async def test_legacy_gang_id_becomes_primary_and_keeps_the_others(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a = await _gang(client, h, uni, "A")
    b = await _gang(client, h, uni, "B")
    c = await _gang(client, h, uni, "C")
    s = await _set(client, h, uni, gang_ids=[a, b])

    resp = await _patch(client, h, uni, s["id"], {"gang_id": b})
    assert resp.json()["gang_ids"] == [b, a]

    resp = await _patch(client, h, uni, s["id"], {"gang_id": c})
    assert resp.json()["gang_ids"] == [c, b, a]

    resp = await _patch(client, h, uni, s["id"], {"gang_id": None})
    assert resp.json()["gang_ids"] == []
    assert resp.json()["gang_id"] is None


async def test_patch_without_gang_fields_leaves_gangs_alone(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a = await _gang(client, h, uni, "A")
    b = await _gang(client, h, uni, "B")
    s = await _set(client, h, uni, gang_ids=[a, b])
    resp = await _patch(client, h, uni, s["id"], {"bio": "x"})
    assert resp.json()["gang_ids"] == [a, b]


async def test_legacy_create_with_gang_id(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a = await _gang(client, h, uni, "A")
    s = await _set(client, h, uni, gang_id=a)
    assert s["gang_ids"] == [a]
    assert s["gang_id"] == a


async def test_gang_from_another_universe_is_refused(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    other = await _universe(client, h)
    foreign = await _gang(client, h, other, "Foreign")
    resp = await client.post(
        "/api/v1/sets/", json={"universe_id": uni, "name": "X", "gang_ids": [foreign]}, headers=h
    )
    assert resp.status_code == 422
    assert foreign in resp.text


async def test_deleting_the_primary_gang_promotes_the_next(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    a = await _gang(client, h, uni, "A")
    b = await _gang(client, h, uni, "B")
    s = await _set(client, h, uni, gang_ids=[a, b])
    usage = (await client.get(f"/api/v1/gangs/{a}/usage?universe_id={uni}", headers=h)).json()
    assert usage["sets"] == 1

    resp = await client.delete(f"/api/v1/gangs/{a}?universe_id={uni}", headers=h)
    assert resp.status_code == 204

    after = (await client.get(f"/api/v1/sets/{s['id']}?universe_id={uni}", headers=h)).json()
    assert after["gang_ids"] == [b]
    assert after["gang_id"] == b
