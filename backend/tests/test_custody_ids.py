"""API integration tests for member custody numbers.

A custody number is a number one system issued to one person. The table exists
because people pass through several systems (state prison, federal prison, a
county jail, an arrest tracking number) and some systems issue a new number per
arrest, so the model is one row per number and the rules are about which
duplicates mean "the same person entered twice".

MDOC and BOP still live on member columns during the transition; the table
mirrors them. Those tests pin the mirror's behaviour so retiring the columns
later is a visible change, not a silent one.
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


async def _auth(client: AsyncClient, session: AsyncSession) -> dict:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _universe(client: AsyncClient, auth: dict) -> str:
    resp = await client.post(
        "/api/v1/universes/", json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"}, headers=auth
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _member(client: AsyncClient, auth: dict, universe_id: str, **extra) -> str:
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": f"Subject {_uid()}", **extra},
        headers=auth,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _add(client: AsyncClient, auth: dict, universe_id: str, member_id: str, **body):
    return await client.post(
        f"/api/v1/members/{member_id}/custody-ids?universe_id={universe_id}",
        json=body,
        headers=auth,
    )


async def _numbers(client: AsyncClient, auth: dict, universe_id: str, member_id: str) -> set:
    resp = await client.get(f"/api/v1/members/{member_id}?universe_id={universe_id}", headers=auth)
    assert resp.status_code == 200, resp.text
    return {(c["system"], c["number"]) for c in resp.json()["custody_ids"]}


async def test_one_member_holds_numbers_from_several_systems(
    client: AsyncClient, db_session: AsyncSession
):
    """MDOC and BOP from the columns, a GDC ID and two OTNs by hand: all five on one person."""
    auth = await _auth(client, db_session)
    uni = await _universe(client, auth)
    mid = await _member(client, auth, uni, mdoc_number="852685", bop_register_number="12347-039")
    assert (
        await _add(client, auth, uni, mid, system="GDC", number="1003795315")
    ).status_code == 201
    # An OTN is issued per arrest, so two in one system on one person is normal.
    assert (
        await _add(client, auth, uni, mid, system="GA_OTN", number="88440470915")
    ).status_code == 201
    assert (
        await _add(client, auth, uni, mid, system="GA_OTN", number="88440470999")
    ).status_code == 201

    assert await _numbers(client, auth, uni, mid) == {
        ("MDOC", "852685"),
        ("BOP", "12347-039"),
        ("GDC", "1003795315"),
        ("GA_OTN", "88440470915"),
        ("GA_OTN", "88440470999"),
    }


async def test_leading_zeros_and_whitespace(client: AsyncClient, db_session: AsyncSession):
    """GDC IDs like 0001238843 are real; nothing may turn them into integers."""
    auth = await _auth(client, db_session)
    uni = await _universe(client, auth)
    mid = await _member(client, auth, uni)
    resp = await _add(client, auth, uni, mid, system="GDC", number=" 0001238843 ")
    assert resp.status_code == 201, resp.text
    assert resp.json()["number"] == "0001238843"

    empty = await _add(client, auth, uni, mid, system="GDC", number="   ")
    assert empty.status_code == 422, empty.text
    unknown = await _add(client, auth, uni, mid, system="TEXAS", number="1")
    assert unknown.status_code == 422, unknown.text


async def test_a_number_is_one_person_within_a_universe(
    client: AsyncClient, db_session: AsyncSession
):
    """Two members holding one GDC ID are one man entered twice; another universe is its own namespace."""
    auth = await _auth(client, db_session)
    uni_a, uni_b = await _universe(client, auth), await _universe(client, auth)
    first, second = await _member(client, auth, uni_a), await _member(client, auth, uni_a)
    elsewhere = await _member(client, auth, uni_b)

    assert (
        await _add(client, auth, uni_a, first, system="GDC", number="5550001")
    ).status_code == 201
    dup = await _add(client, auth, uni_a, second, system="GDC", number="5550001")
    assert dup.status_code == 409, dup.text
    again = await _add(client, auth, uni_a, first, system="GDC", number="5550001")
    assert again.status_code == 409, again.text
    other = await _add(client, auth, uni_b, elsewhere, system="GDC", number="5550001")
    assert other.status_code == 201, other.text
    # The same digits in a different system are a different number.
    otn = await _add(client, auth, uni_a, second, system="GA_OTN", number="5550001")
    assert otn.status_code == 201, otn.text


async def test_mdoc_stays_exempt_from_the_cross_member_check(
    client: AsyncClient, db_session: AsyncSession
):
    """The MDOC column was never unique ("OTIS is the authority on collisions"), and the mirror keeps that."""
    auth = await _auth(client, db_session)
    uni = await _universe(client, auth)
    a = await _member(client, auth, uni, mdoc_number="700001")
    b = await _member(client, auth, uni, mdoc_number="700001")
    assert ("MDOC", "700001") in await _numbers(client, auth, uni, a)
    assert ("MDOC", "700001") in await _numbers(client, auth, uni, b)


async def test_mdoc_and_bop_are_written_through_their_columns(
    client: AsyncClient, db_session: AsyncSession
):
    """Adding MDOC or BOP here is refused, so the column and the table cannot disagree."""
    auth = await _auth(client, db_session)
    uni = await _universe(client, auth)
    mid = await _member(client, auth, uni)
    for system, number in (("MDOC", "123456"), ("BOP", "12348-039")):
        resp = await _add(client, auth, uni, mid, system=system, number=number)
        assert resp.status_code == 422, (system, resp.text)
    assert await _numbers(client, auth, uni, mid) == set()


async def test_the_mirror_follows_the_column(client: AsyncClient, db_session: AsyncSession):
    """Changing the BOP column replaces the mirrored row; clearing it removes it; GDC is untouched."""
    auth = await _auth(client, db_session)
    uni = await _universe(client, auth)
    mid = await _member(client, auth, uni, bop_register_number="12349-039")
    assert (await _add(client, auth, uni, mid, system="GDC", number="5550002")).status_code == 201

    moved = await client.patch(
        f"/api/v1/members/{mid}?universe_id={uni}",
        json={"bop_register_number": "12350-039"},
        headers=auth,
    )
    assert moved.status_code == 200, moved.text
    assert await _numbers(client, auth, uni, mid) == {("BOP", "12350-039"), ("GDC", "5550002")}

    cleared = await client.patch(
        f"/api/v1/members/{mid}?universe_id={uni}", json={"bop_register_number": ""}, headers=auth
    )
    assert cleared.status_code == 200, cleared.text
    assert await _numbers(client, auth, uni, mid) == {("GDC", "5550002")}

    # A PATCH that never mentions the columns leaves the mirror alone.
    set_mdoc = await client.patch(
        f"/api/v1/members/{mid}?universe_id={uni}", json={"mdoc_number": "700002"}, headers=auth
    )
    assert set_mdoc.status_code == 200
    renamed = await client.patch(
        f"/api/v1/members/{mid}?universe_id={uni}",
        json={"nickname": f"Renamed {_uid()}"},
        headers=auth,
    )
    assert renamed.status_code == 200
    assert ("MDOC", "700002") in await _numbers(client, auth, uni, mid)


async def test_delete(client: AsyncClient, db_session: AsyncSession):
    """A hand-added number deletes; a mirrored one points back at its column."""
    auth = await _auth(client, db_session)
    uni = await _universe(client, auth)
    mid = await _member(client, auth, uni, mdoc_number="700003")
    gdc = (await _add(client, auth, uni, mid, system="GDC", number="5550003")).json()
    rows = (
        await client.get(f"/api/v1/members/{mid}/custody-ids?universe_id={uni}", headers=auth)
    ).json()
    mirrored = next(r for r in rows if r["system"] == "MDOC")

    refused = await client.delete(
        f"/api/v1/members/{mid}/custody-ids/{mirrored['id']}?universe_id={uni}", headers=auth
    )
    assert refused.status_code == 422, refused.text
    gone = await client.delete(
        f"/api/v1/members/{mid}/custody-ids/{gdc['id']}?universe_id={uni}", headers=auth
    )
    assert gone.status_code == 204, gone.text
    assert await _numbers(client, auth, uni, mid) == {("MDOC", "700003")}


async def test_deleting_the_member_frees_the_number(client: AsyncClient, db_session: AsyncSession):
    """The row goes with its member, so the number can be recorded on the right person."""
    auth = await _auth(client, db_session)
    uni = await _universe(client, auth)
    wrong = await _member(client, auth, uni)
    assert (await _add(client, auth, uni, wrong, system="GDC", number="5550004")).status_code == 201
    resp = await client.delete(f"/api/v1/members/{wrong}?universe_id={uni}", headers=auth)
    assert resp.status_code == 204, resp.text
    right = await _member(client, auth, uni)
    assert (await _add(client, auth, uni, right, system="GDC", number="5550004")).status_code == 201
