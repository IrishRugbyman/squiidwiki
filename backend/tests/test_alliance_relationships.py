"""Alliance-level allies and enemies: /alliances/{id}/relationships and the set view.

An alliance can hold a link to another alliance or to one set. The expectations
below are written from the rules, not read back from the code: a link is one row
seen from both ends, a set inherits its alliance's links, and a set cannot be
the far side of its own alliance's link.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _setup(client: AsyncClient, session: AsyncSession) -> tuple[dict, str]:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers=headers,
    )
    assert resp.status_code == 201
    return headers, resp.json()["id"]


async def _alliance(client: AsyncClient, h: dict, uid: str, name: str) -> str:
    resp = await client.post(
        "/api/v1/alliances/", json={"universe_id": uid, "name": name}, headers=h
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _set(
    client: AsyncClient, h: dict, uid: str, name: str, alliance_id: str | None = None
) -> str:
    resp = await client.post(
        "/api/v1/sets/",
        json={"universe_id": uid, "name": name, "alliance_id": alliance_id},
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _rels(client: AsyncClient, h: dict, uid: str, alliance_id: str, ended=False) -> list:
    resp = await client.get(
        f"/api/v1/alliances/{alliance_id}/relationships",
        params={"universe_id": uid, "include_ended": ended},
        headers=h,
    )
    assert resp.status_code == 200
    return resp.json()


async def _set_rels(client: AsyncClient, h: dict, uid: str, set_id: str) -> list:
    resp = await client.get(
        f"/api/v1/sets/{set_id}/alliance-relationships", params={"universe_id": uid}, headers=h
    )
    assert resp.status_code == 200
    return resp.json()


async def _add(client: AsyncClient, h: dict, uid: str, alliance_id: str, body: dict):
    return await client.post(
        f"/api/v1/alliances/{alliance_id}/relationships",
        params={"universe_id": uid},
        json=body,
        headers=h,
    )


async def test_alliance_to_alliance_is_one_link_seen_from_both_ends(
    client: AsyncClient, db_session: AsyncSession
):
    h, uid = await _setup(client, db_session)
    north = await _alliance(client, h, uid, "North Bloc")
    south = await _alliance(client, h, uid, "South Bloc")

    resp = await _add(client, h, uid, north, {"target_alliance_id": south, "type": "ENEMY"})
    assert resp.status_code == 201
    created = resp.json()
    assert created["other_kind"] == "alliance"
    assert created["other_id"] == south
    assert created["other_name"] == "South Bloc"

    from_south = await _rels(client, h, uid, south)
    assert [(r["id"], r["other_id"], r["type"]) for r in from_south] == [
        (created["id"], north, "ENEMY")
    ]

    # Recording it again from the other end is the same fact, not a second row.
    again = await _add(client, h, uid, south, {"target_alliance_id": north, "type": "ENEMY"})
    assert again.status_code == 201
    assert again.json()["id"] == created["id"]
    assert len(await _rels(client, h, uid, north)) == 1


async def test_opposite_type_on_an_open_link_is_a_conflict(
    client: AsyncClient, db_session: AsyncSession
):
    h, uid = await _setup(client, db_session)
    a = await _alliance(client, h, uid, "A")
    b = await _alliance(client, h, uid, "B")
    assert (
        await _add(client, h, uid, a, {"target_alliance_id": b, "type": "FRIEND"})
    ).status_code == 201
    resp = await _add(client, h, uid, b, {"target_alliance_id": a, "type": "ENEMY"})
    assert resp.status_code == 409


async def test_set_sees_links_naming_it_and_links_its_alliance_holds(
    client: AsyncClient, db_session: AsyncSession
):
    h, uid = await _setup(client, db_session)
    north = await _alliance(client, h, uid, "North")
    south = await _alliance(client, h, uid, "South")
    clique = await _set(client, h, uid, "North Clique", north)
    rival = await _set(client, h, uid, "Loose Rival")
    friend = await _set(client, h, uid, "Loose Friend")

    await _add(client, h, uid, north, {"target_alliance_id": south, "type": "ENEMY"})
    await _add(client, h, uid, north, {"target_set_id": rival, "type": "ENEMY"})
    await _add(client, h, uid, north, {"target_set_id": friend, "type": "FRIEND"})

    # The clique inherits all three, each marked as coming through North.
    seen = {
        (r["other_kind"], r["other_id"], r["type"], r["via_alliance_id"])
        for r in await _set_rels(client, h, uid, clique)
    }
    assert seen == {
        ("alliance", south, "ENEMY", north),
        ("set", rival, "ENEMY", north),
        ("set", friend, "FRIEND", north),
    }

    # The rival sees the alliance at war with it, held by no alliance of its own.
    [row] = await _set_rels(client, h, uid, rival)
    assert (row["other_kind"], row["other_id"], row["type"]) == ("alliance", north, "ENEMY")
    assert row["via_alliance_id"] is None

    # And the alliance sees the set as a set.
    kinds = {(r["other_kind"], r["other_name"]) for r in await _rels(client, h, uid, north)}
    assert kinds == {("alliance", "South"), ("set", "Loose Rival"), ("set", "Loose Friend")}


async def test_refused_targets(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    a = await _alliance(client, h, uid, "A")
    b = await _alliance(client, h, uid, "B")
    own_set = await _set(client, h, uid, "Inside A", a)
    loose = await _set(client, h, uid, "Loose")
    _, other_uid = await _setup(client, db_session)
    foreign = await _alliance(client, h, other_uid, "Elsewhere")

    cases = [
        ({"target_alliance_id": a, "type": "ENEMY"}, 422),  # itself
        ({"target_set_id": own_set, "type": "ENEMY"}, 422),  # its own set
        ({"target_alliance_id": b, "target_set_id": loose, "type": "ENEMY"}, 422),  # both
        ({"type": "ENEMY"}, 422),  # neither
        ({"target_alliance_id": foreign, "type": "ENEMY"}, 404),  # other universe
        ({"target_set_id": str(uuid.uuid4()), "type": "ENEMY"}, 404),
    ]
    for body, code in cases:
        resp = await _add(client, h, uid, a, body)
        assert resp.status_code == code, (body, resp.text)
    assert await _rels(client, h, uid, a) == []


async def test_ending_keeps_history_and_allows_a_new_spell(
    client: AsyncClient, db_session: AsyncSession
):
    h, uid = await _setup(client, db_session)
    a = await _alliance(client, h, uid, "A")
    b = await _alliance(client, h, uid, "B")
    rel = (await _add(client, h, uid, a, {"target_alliance_id": b, "type": "FRIEND"})).json()

    resp = await client.post(
        f"/api/v1/alliances/{b}/relationships/{rel['id']}/end",
        params={"universe_id": uid},
        json={"until_date": {"year": 2015, "precision": "Y"}},
        headers=h,
    )
    assert resp.status_code == 204

    assert await _rels(client, h, uid, a) == []
    [past] = await _rels(client, h, uid, a, ended=True)
    assert past["is_current"] is False
    assert past["until_date"]["year"] == 2015

    # Allies until 2015, enemies since: the ended spell no longer blocks the pair.
    resp = await _add(client, h, uid, a, {"target_alliance_id": b, "type": "ENEMY"})
    assert resp.status_code == 201
    assert len(await _rels(client, h, uid, a, ended=True)) == 2


async def test_delete_removes_the_row(client: AsyncClient, db_session: AsyncSession):
    h, uid = await _setup(client, db_session)
    a = await _alliance(client, h, uid, "A")
    loose = await _set(client, h, uid, "Loose")
    rel = (await _add(client, h, uid, a, {"target_set_id": loose, "type": "ENEMY"})).json()

    url = f"/api/v1/alliances/{a}/relationships/{rel['id']}"
    assert (await client.delete(url, params={"universe_id": uid}, headers=h)).status_code == 204
    assert (await client.delete(url, params={"universe_id": uid}, headers=h)).status_code == 404
    assert await _set_rels(client, h, uid, loose) == []


async def test_deleting_either_end_takes_the_link_with_it(
    client: AsyncClient, db_session: AsyncSession
):
    h, uid = await _setup(client, db_session)
    a = await _alliance(client, h, uid, "A")
    b = await _alliance(client, h, uid, "B")
    loose = await _set(client, h, uid, "Loose")
    await _add(client, h, uid, a, {"target_alliance_id": b, "type": "ENEMY"})
    await _add(client, h, uid, a, {"target_set_id": loose, "type": "ENEMY"})

    resp = await client.delete(f"/api/v1/alliances/{b}", params={"universe_id": uid}, headers=h)
    assert resp.status_code == 204
    resp = await client.delete(f"/api/v1/sets/{loose}", params={"universe_id": uid}, headers=h)
    assert resp.status_code == 204
    assert await _rels(client, h, uid, a, ended=True) == []


async def test_set_with_relationships_and_lineage_can_be_deleted(
    client: AsyncClient, db_session: AsyncSession
):
    """set_relationships and set_lineage have no ON DELETE: this used to 500."""
    h, uid = await _setup(client, db_session)
    doomed = await _set(client, h, uid, "Doomed")
    other = await _set(client, h, uid, "Other")
    resp = await client.post(
        f"/api/v1/sets/{doomed}/relationships",
        params={"universe_id": uid},
        json={"target_id": other, "type": "ENEMY"},
        headers=h,
    )
    assert resp.status_code == 200
    resp = await client.post(
        f"/api/v1/sets/{doomed}/lineage",
        params={"universe_id": uid},
        json={"other_id": other, "kind": "SPLINTERED_FROM", "direction": "parent"},
        headers=h,
    )
    assert resp.status_code == 201

    resp = await client.delete(f"/api/v1/sets/{doomed}", params={"universe_id": uid}, headers=h)
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/sets/{other}", params={"universe_id": uid}, headers=h)
    assert resp.json()["enemy_ids"] == []
    assert resp.json()["lineage"] == []
