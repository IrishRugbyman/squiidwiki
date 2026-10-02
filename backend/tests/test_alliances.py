"""API integration tests for the /api/v1/alliances/ vertical slice."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _admin_token(client: AsyncClient, session: AsyncSession) -> str:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return resp.json()["access_token"]


async def _user_token(client: AsyncClient, session: AsyncSession) -> str:
    email = f"user_{_uid()}@example.com"
    await create_user(session, email, "userpass", GlobalRole.USER)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "userpass"})
    return resp.json()["access_token"]


async def _make_universe(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_alliance(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/alliances/",
        json={"universe_id": universe_id, "name": "East Side Coalition", "status": "ACTIVE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "East Side Coalition"
    assert data["status"] == "ACTIVE"


async def test_list_alliances(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/alliances/",
        json={"universe_id": universe_id, "name": "West Coalition"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/alliances/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_alliance(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "North Bloc"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "North Bloc"
    assert "set_ids" in data
    assert "territory_ids" in data


async def test_get_alliance_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/alliances/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_alliance(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "Original"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        json={"status": "DORMANT"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DORMANT"


async def test_delete_alliance_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "DeleteMe"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_alliance_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": "Protected"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/alliances/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_search_alliances(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/alliances/",
        json={"universe_id": universe_id, "name": "SkylineAlliance"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/alliances/search?universe_id={universe_id}&q=Skyline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_alliance_members_includes_members_of_its_sets(
    client: AsyncClient, db_session: AsyncSession
):
    """An alliance's roster is its sets' members, not only directly-tagged ones.

    Regression: the query filtered on Member.alliance_id alone, so an alliance
    whose sets were full reported zero members, and every count derived from
    that list on the alliance page read 0.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    alliance_id = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": f"Coalition {_uid()}"},
            headers=auth,
        )
    ).json()["id"]

    set_id = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": f"Set {_uid()}", "alliance_id": alliance_id},
            headers=auth,
        )
    ).json()["id"]

    # In one of the alliance's sets, but not tagged to the alliance directly.
    via_set = (
        await client.post(
            "/api/v1/members/",
            json={
                "universe_id": universe_id,
                "nickname": "ViaSet",
                "affiliations": [{"set_id": set_id, "is_primary": True}],
            },
            headers=auth,
        )
    ).json()["id"]

    # Tagged straight to the alliance with no set at all.
    direct = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Direct", "alliance_id": alliance_id},
            headers=auth,
        )
    ).json()["id"]

    # In neither, and must not appear.
    outsider = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Outsider"},
            headers=auth,
        )
    ).json()["id"]

    resp = await client.get(
        f"/api/v1/alliances/{alliance_id}/members",
        params={"universe_id": universe_id, "limit": 100},
        headers=auth,
    )
    assert resp.status_code == 200
    ids = {m["id"] for m in resp.json()["items"]}
    assert via_set in ids
    assert direct in ids
    assert outsider not in ids


async def test_alliance_incidents_includes_incidents_of_its_sets_members(
    client: AsyncClient, db_session: AsyncSession
):
    """Same union for incidents: a set member's incident belongs to the alliance.

    Regression: the join filtered on Member.alliance_id, so an alliance whose
    sets' members were incident participants showed no incidents at all.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    alliance_id = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": f"Coalition {_uid()}"},
            headers=auth,
        )
    ).json()["id"]
    set_id = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": f"Set {_uid()}", "alliance_id": alliance_id},
            headers=auth,
        )
    ).json()["id"]
    member_id = (
        await client.post(
            "/api/v1/members/",
            json={
                "universe_id": universe_id,
                "nickname": "ViaSet",
                "affiliations": [{"set_id": set_id, "is_primary": True}],
            },
            headers=auth,
        )
    ).json()["id"]

    incident_id = (
        await client.post(
            "/api/v1/incidents/",
            json={
                "universe_id": universe_id,
                "type": "SHOOTING",
                "date": {"year": 2020, "month": 5, "day": 1, "precision": "YMD", "approx": False},
                "participants": [{"member_id": member_id, "role": "VICTIM", "outcome": "INJURED"}],
            },
            headers=auth,
        )
    ).json()["id"]

    resp = await client.get(
        f"/api/v1/alliances/{alliance_id}/incidents",
        params={"universe_id": universe_id, "limit": 100},
        headers=auth,
    )
    assert resp.status_code == 200
    rows = {i["id"]: i for i in resp.json()["items"]}
    assert incident_id in rows
    # Enriched like the main incident list: returned bare, this came back [].
    assert rows[incident_id]["victim_names"] == ["ViaSet"]


async def test_alliance_list_counts_sets_and_members_once(
    client: AsyncClient, db_session: AsyncSession
):
    """List rows carry set and member counts matching the alliance's roster.

    A member both tagged to the alliance and in one of its sets counts once;
    a member who left a set (until_date set) does not count; an alliance with
    nothing in it reads 0, not a missing key.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    async def post(path: str, body: dict) -> str:
        resp = await client.post(path, json={"universe_id": universe_id, **body}, headers=auth)
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    full = await post("/api/v1/alliances/", {"name": "B Full Coalition"})
    empty = await post("/api/v1/alliances/", {"name": "A Empty Coalition"})
    set_a = await post("/api/v1/sets/", {"name": f"Set {_uid()}", "alliance_id": full})
    set_b = await post("/api/v1/sets/", {"name": f"Set {_uid()}", "alliance_id": full})

    # In set A only.
    await post("/api/v1/members/", {"nickname": "One", "affiliations": [{"set_id": set_a}]})
    # In both sets and tagged directly: still one person.
    await post(
        "/api/v1/members/",
        {
            "nickname": "Two",
            "alliance_id": full,
            "affiliations": [{"set_id": set_a, "is_primary": True}, {"set_id": set_b}],
        },
    )
    # Tagged directly, no set.
    await post("/api/v1/members/", {"nickname": "Three", "alliance_id": full})
    # Left set B: a former member is not on the roster.
    former = await post(
        "/api/v1/members/", {"nickname": "Former", "affiliations": [{"set_id": set_b}]}
    )
    member = (
        await client.get(
            f"/api/v1/members/{former}", params={"universe_id": universe_id}, headers=auth
        )
    ).json()
    spell = member["affiliations"][0]["id"]
    ended = await client.post(
        f"/api/v1/members/{former}/affiliations/{spell}/end",
        params={"universe_id": universe_id},
        json={"until_date": {"year": 2020, "precision": "Y"}},
        headers=auth,
    )
    assert ended.status_code == 204, ended.text

    resp = await client.get(
        "/api/v1/alliances/", params={"universe_id": universe_id, "limit": 100}, headers=auth
    )
    assert resp.status_code == 200
    rows = resp.json()["items"]
    # Ordered by name.
    assert [r["name"] for r in rows] == ["A Empty Coalition", "B Full Coalition"]
    by_id = {r["id"]: r for r in rows}
    assert by_id[full]["set_count"] == 2
    assert by_id[full]["member_count"] == 3
    assert by_id[empty]["set_count"] == 0
    assert by_id[empty]["member_count"] == 0


async def test_delete_alliance_with_directly_tagged_member(
    client: AsyncClient, db_session: AsyncSession
):
    """A member tagged straight to an alliance must not block deleting it.

    Regression: delete detached sets but not members, and member.alliance_id
    has no ON DELETE, so the delete failed on the foreign key.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}
    alliance_id = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": universe_id, "name": f"Coalition {_uid()}"},
            headers=auth,
        )
    ).json()["id"]
    member_id = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Tagged", "alliance_id": alliance_id},
            headers=auth,
        )
    ).json()["id"]

    resp = await client.delete(
        f"/api/v1/alliances/{alliance_id}", params={"universe_id": universe_id}, headers=auth
    )
    assert resp.status_code == 204, resp.text
    member = await client.get(
        f"/api/v1/members/{member_id}", params={"universe_id": universe_id}, headers=auth
    )
    assert member.status_code == 200
    assert member.json()["alliance_id"] is None


async def test_delete_alliance_with_territory(client: AsyncClient, db_session: AsyncSession):
    """An alliance with a city on file must be deletable.

    Regression: alliance_municipality has no ON DELETE and delete_alliance left
    its rows in place, so the delete failed on the foreign key with a 500.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}
    city = await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": universe_id, "name": f"City {_uid()}"},
        headers=auth,
    )
    assert city.status_code == 201, city.text
    alliance = await client.post(
        "/api/v1/alliances/",
        json={
            "universe_id": universe_id,
            "name": f"Coalition {_uid()}",
            "territory_ids": [city.json()["id"]],
        },
        headers=auth,
    )
    assert alliance.status_code == 201, alliance.text
    got = await client.get(
        f"/api/v1/alliances/{alliance.json()['id']}",
        params={"universe_id": universe_id},
        headers=auth,
    )
    assert got.json()["territory_ids"] == [city.json()["id"]]

    resp = await client.delete(
        f"/api/v1/alliances/{alliance.json()['id']}",
        params={"universe_id": universe_id},
        headers=auth,
    )
    assert resp.status_code == 204, resp.text
