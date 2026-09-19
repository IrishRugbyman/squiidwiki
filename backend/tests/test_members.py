"""API integration tests for the /api/v1/members/ vertical slice."""

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


async def test_create_member(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": "Ghost", "status": "FREE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["display_name"] == "Ghost"
    assert data["status"] == "FREE"


async def test_create_member_nickname_unknown(client: AsyncClient, db_session: AsyncSession):
    """When nickname_unknown=True, display_name should use legal name."""
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_id,
            "legal_name": "John Doe",
            "nickname_unknown": True,
            "status": "FREE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["display_name"] == "John Doe"


async def test_list_members(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": "Spooky"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/members/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) >= 1


async def test_get_member(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Shadow"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Shadow"
    assert "source_ids" in data


async def test_get_member_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/members/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_member(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Lil D"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        json={"status": "LOCKED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "LOCKED"


async def test_delete_member_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "DeleteMe"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_member_forbidden_for_user(client: AsyncClient, db_session: AsyncSession):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Protected"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_search_members(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": "Tornado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/members/search?universe_id={universe_id}&q=Tornado",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_member_stats(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "StatsGuy"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/members/{created['id']}/stats?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "shootings" in data
    assert "kills" in data
    assert data["shootings"] == 0


async def test_member_with_fuzzy_dob(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_id,
            "nickname": "OldTimer",
            "dob": {"year": 1990, "precision": "Y", "approx": True},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["dob"]["year"] == 1990
    assert data["dob"]["approx"] is True


async def test_search_returns_the_members_set(client: AsyncClient, db_session: AsyncSession):
    """Search must carry affiliations, not just the bare member row.

    Regression: search_members returned Members straight from the query without
    calling _attach_affiliations, so the schema serialised affiliations as [] and
    every primary_set_* field as null. The set column went blank in the UI while
    the data was intact in the database, and the old test passed because it only
    asserted a 200 and a list.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    headers = {"Authorization": f"Bearer {token}"}

    set_id = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": "Searchable Set"},
            headers=headers,
        )
    ).json()["id"]
    await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_id,
            "nickname": "FindMe",
            "affiliations": [{"set_id": set_id, "is_primary": True}],
        },
        headers=headers,
    )

    found = (
        await client.get(
            f"/api/v1/members/search?universe_id={universe_id}&q=FindMe", headers=headers
        )
    ).json()
    assert len(found) == 1
    hit = found[0]
    assert hit["primary_set_id"] == set_id
    assert hit["primary_set_name"] == "Searchable Set"
    assert [a["set_name"] for a in hit["affiliations"]] == ["Searchable Set"]

    # The list endpoint has always done this; search must agree with it.
    listed = (
        await client.get(f"/api/v1/members/?universe_id={universe_id}&q=FindMe", headers=headers)
    ).json()
    row = (listed["items"] if isinstance(listed, dict) else listed)[0]
    assert row["primary_set_name"] == hit["primary_set_name"]


async def test_mdoc_number_round_trips_through_create_and_read(
    client: AsyncClient, db_session: AsyncSession
):
    """The MDOC number must survive the read path, not just the write.

    It is assembled into MemberRead by hand in the router rather than dumped
    from the ORM object, so a field can persist correctly and still come back
    null. That happened once; this pins it.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Numbered", "mdoc_number": "123456"},
            headers=auth,
        )
    ).json()
    assert created["mdoc_number"] == "123456"

    fetched = await client.get(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}", headers=auth
    )
    assert fetched.status_code == 200
    assert fetched.json()["mdoc_number"] == "123456"


async def test_member_without_an_mdoc_number_still_reads(
    client: AsyncClient, db_session: AsyncSession
):
    """Most members have no MDOC number, so absent must read back as null.

    Note what this does *not* prove: the field's `= None` default on MemberRead
    is belt-and-braces, and removing it keeps these tests green, because the
    router now always passes the key. The router line is the load-bearing part.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}
    created = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": "Unnumbered"},
            headers=auth,
        )
    ).json()
    fetched = await client.get(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}", headers=auth
    )
    assert fetched.status_code == 200
    assert fetched.json()["mdoc_number"] is None


async def test_bop_register_number_is_normalised_and_round_trips(
    client: AsyncClient, db_session: AsyncSession
):
    """A register number keeps the BOP's own NNNNN-NNN shape whatever was typed.

    Written with and without the hyphen, and with stray spaces, it has to land as
    the one spelling the locator answers to, or a lookup by number misses and a
    duplicate check compares two spellings of the same man.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_id,
            "nickname": "Federal",
            "bop_register_number": " 12345000 ",
        },
        headers=auth,
    )
    assert created.status_code == 201, created.text
    assert created.json()["bop_register_number"] == "12345-000"

    fetched = await client.get(
        f"/api/v1/members/{created.json()['id']}?universe_id={universe_id}", headers=auth
    )
    assert fetched.json()["bop_register_number"] == "12345-000"


async def test_bop_register_number_rejects_what_is_not_one(
    client: AsyncClient, db_session: AsyncSession
):
    """An MDOC number or a docket number in this field is refused, not stored.

    Both have been misfiled as register numbers before (a docket in `case_id`, a
    register number in notes); a malformed value here would pass for a key.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}
    for bad in ("123456", "2:00-cr-00000", "12345-00", "1234-5000"):
        r = await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_id, "nickname": f"Bad {bad}", "bop_register_number": bad},
            headers=auth,
        )
        assert r.status_code == 422, (bad, r.status_code, r.text)


async def test_bop_register_number_is_unique_within_a_universe_only(
    client: AsyncClient, db_session: AsyncSession
):
    """One register number is one person: a second row with it is a duplicate.

    The BOP assigns the number once for life, so two members of one universe
    holding it are the same man entered twice. A different universe is a
    different namespace and may legitimately hold its own row for him.
    """
    token = await _admin_token(client, db_session)
    auth = {"Authorization": f"Bearer {token}"}
    universe_a = await _make_universe(client, token)
    universe_b = await _make_universe(client, token)

    first = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_a, "nickname": "Once", "bop_register_number": "12346-000"},
        headers=auth,
    )
    assert first.status_code == 201, first.text

    again = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_a, "nickname": "Twice", "bop_register_number": "12346-000"},
        headers=auth,
    )
    assert again.status_code == 409, again.text

    other = await client.post(
        "/api/v1/members/",
        json={
            "universe_id": universe_b,
            "nickname": "Elsewhere",
            "bop_register_number": "12346-000",
        },
        headers=auth,
    )
    assert other.status_code == 201, other.text

    # Moving an existing member onto a number another member holds is the same
    # duplicate by another route.
    third = (
        await client.post(
            "/api/v1/members/",
            json={"universe_id": universe_a, "nickname": "Third"},
            headers=auth,
        )
    ).json()
    moved = await client.patch(
        f"/api/v1/members/{third['id']}?universe_id={universe_a}",
        json={"bop_register_number": "12346000"},
        headers=auth,
    )
    assert moved.status_code == 409, moved.text


async def test_bop_register_number_can_be_cleared(client: AsyncClient, db_session: AsyncSession):
    """An empty string clears the number, as the member form sends when emptied."""
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}
    created = (
        await client.post(
            "/api/v1/members/",
            json={
                "universe_id": universe_id,
                "nickname": "Cleared",
                "bop_register_number": "12347-000",
            },
            headers=auth,
        )
    ).json()
    patched = await client.patch(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        json={"bop_register_number": ""},
        headers=auth,
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["bop_register_number"] is None
    # The same member may now take the number back without tripping the check.
    back = await client.patch(
        f"/api/v1/members/{created['id']}?universe_id={universe_id}",
        json={"bop_register_number": "12347-000"},
        headers=auth,
    )
    assert back.status_code == 200, back.text
