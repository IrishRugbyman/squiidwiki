"""Gang cards: reference fields, the parent hierarchy, counts and the detail page."""

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


async def _gang(client: AsyncClient, h: dict, uni: str, name: str, **fields) -> dict:
    """Create a gang. Names link to a shared card across universes, so each
    test uses its own names unless it is testing that sharing."""
    resp = await client.post(
        "/api/v1/gangs/", json={"universe_id": uni, "name": name, **fields}, headers=h
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _patch_gang(client, h, uni, gang_id, body):
    return await client.patch(f"/api/v1/gangs/{gang_id}?universe_id={uni}", json=body, headers=h)


async def test_create_keeps_every_reference_field(client: AsyncClient, db_session: AsyncSession):
    """Colours used to be dropped on create; every field must now round-trip."""
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    g = await _gang(
        client,
        h,
        uni,
        f"Satan Disciples {_uid()}",
        aliases=["SD"],
        color="#FFEF00",
        color_secondary="#000000",
        nation="FOLK",
        origin="Chicago, Pilsen",
        founded_at={"year": 1960, "precision": "Y", "approx": True},
        symbols=["pitchfork", " pitchfork ", "devil head", ""],
    )
    assert g["color"] == "#ffef00"
    assert g["color_secondary"] == "#000000"
    assert g["nation"] == "FOLK"
    assert g["origin"] == "Chicago, Pilsen"
    assert g["founded_at"]["year"] == 1960
    assert g["founded_at"]["approx"] is True
    assert g["symbols"] == ["pitchfork", "devil head"]

    again = (await client.get(f"/api/v1/gangs/{g['id']}?universe_id={uni}", headers=h)).json()
    assert again["color"] == "#ffef00"
    assert again["symbols"] == ["pitchfork", "devil head"]


async def test_bad_nation_is_refused(client: AsyncClient, db_session: AsyncSession):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    resp = await client.post(
        "/api/v1/gangs/", json={"universe_id": uni, "name": "X", "nation": "CRIP"}, headers=h
    )
    assert resp.status_code == 422


async def test_parent_must_not_be_self_foreign_or_a_loop(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    other = await _universe(client, h)
    bloods = await _gang(client, h, uni, f"Bloods {_uid()}")
    pirus = await _gang(client, h, uni, f"Pirus {_uid()}", parent_id=bloods["id"])
    skyline = await _gang(client, h, uni, f"Skyline {_uid()}", parent_id=pirus["id"])
    foreign = await _gang(client, h, other, f"Foreign {_uid()}")

    resp = await _patch_gang(client, h, uni, bloods["id"], {"parent_id": bloods["id"]})
    assert resp.status_code == 422

    # Bloods under its own grandchild would be a loop.
    resp = await _patch_gang(client, h, uni, bloods["id"], {"parent_id": skyline["id"]})
    assert resp.status_code == 422

    resp = await _patch_gang(client, h, uni, pirus["id"], {"parent_id": foreign["id"]})
    assert resp.status_code == 422

    # Clearing a parent is always allowed.
    resp = await _patch_gang(client, h, uni, skyline["id"], {"parent_id": None})
    assert resp.status_code == 200
    assert resp.json()["parent_id"] is None


async def test_detail_lineage_branches_sets_and_counts(
    client: AsyncClient, db_session: AsyncSession
):
    h = await _admin(client, db_session)
    uni = await _universe(client, h)
    bloods = await _gang(client, h, uni, f"Bloods {_uid()}")
    pirus = await _gang(client, h, uni, f"Pirus {_uid()}", parent_id=bloods["id"])
    skyline = await _gang(client, h, uni, f"Skyline {_uid()}", parent_id=pirus["id"])
    crips = await _gang(client, h, uni, f"Crips {_uid()}")

    only_pirus = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": uni, "name": "A Set", "gang_ids": [pirus["id"]]},
            headers=h,
        )
    ).json()
    hybrid = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": uni, "name": "B Set", "gang_ids": [crips["id"], pirus["id"]]},
            headers=h,
        )
    ).json()
    alliance = (
        await client.post(
            "/api/v1/alliances/",
            json={"universe_id": uni, "name": "Red Bloc", "gang_id": pirus["id"]},
            headers=h,
        )
    ).json()
    # One person in both Piru sets, one tagged straight to the card: two people.
    in_both = await client.post(
        "/api/v1/members/",
        json={
            "universe_id": uni,
            "nickname": f"Both {_uid()}",
            "affiliations": [
                {"set_id": only_pirus["id"], "is_primary": True},
                {"set_id": hybrid["id"], "is_primary": False},
            ],
        },
        headers=h,
    )
    assert in_both.status_code == 201, in_both.text
    tagged = await client.post(
        "/api/v1/members/",
        json={"universe_id": uni, "nickname": f"Tag {_uid()}", "gang_id": pirus["id"]},
        headers=h,
    )
    assert tagged.status_code == 201, tagged.text

    d = (
        await client.get(f"/api/v1/gangs/{pirus['slug']}/detail?universe_id={uni}", headers=h)
    ).json()
    assert d["name"] == pirus["name"]
    assert d["parent"]["id"] == bloods["id"]
    assert [a["id"] for a in d["ancestors"]] == [bloods["id"]]
    assert [b["id"] for b in d["branches"]] == [skyline["id"]]
    assert {s["id"]: s["is_primary"] for s in d["sets"]} == {
        only_pirus["id"]: True,
        hybrid["id"]: False,
    }
    assert [a["id"] for a in d["alliances"]] == [alliance["id"]]
    assert d["set_count"] == 2
    assert d["alliance_count"] == 1
    assert d["member_count"] == 2

    sky = (
        await client.get(f"/api/v1/gangs/{skyline['id']}/detail?universe_id={uni}", headers=h)
    ).json()
    assert [a["id"] for a in sky["ancestors"]] == [pirus["id"], bloods["id"]]

    listing = (await client.get(f"/api/v1/gangs/?universe_id={uni}", headers=h)).json()
    by_id = {g["id"]: g for g in listing["items"]}
    assert by_id[pirus["id"]]["set_count"] == 2
    assert by_id[crips["id"]]["set_count"] == 1
    assert by_id[bloods["id"]]["set_count"] == 0


async def test_same_name_in_two_universes_shares_one_card(
    client: AsyncClient, db_session: AsyncSession
):
    """Colours set in one universe show in the other; local notes stay local."""
    h = await _admin(client, db_session)
    mi = await _universe(client, h)
    il = await _universe(client, h)
    name = f"Latin Kings {_uid()}"
    parent_name = f"Kings Nation {_uid()}"
    mi_parent = await _gang(client, h, mi, parent_name)
    il_parent = await _gang(client, h, il, parent_name)
    mi_lk = await _gang(
        client, h, mi, name, color="#ffd700", nation="PEOPLE", card_description="National."
    )
    il_lk = await _gang(client, h, il, name, description="Chicago note.")
    assert mi_lk["card_id"] == il_lk["card_id"]
    assert il_lk["color"] == "#ffd700"
    assert il_lk["nation"] == "PEOPLE"
    assert il_lk["card_description"] == "National."
    assert il_lk["description"] == "Chicago note."

    # A shared field edited from Illinois reaches Michigan.
    resp = await _patch_gang(
        client, h, il, il_lk["id"], {"color_secondary": "#000000", "symbols": ["crown"]}
    )
    assert resp.status_code == 200
    mi_now = (await client.get(f"/api/v1/gangs/{mi_lk['id']}?universe_id={mi}", headers=h)).json()
    assert mi_now["color_secondary"] == "#000000"
    assert mi_now["symbols"] == ["crown"]

    # A local note edited in Michigan stays in Michigan.
    await _patch_gang(client, h, mi, mi_lk["id"], {"description": "Detroit note."})
    il_now = (await client.get(f"/api/v1/gangs/{il_lk['id']}?universe_id={il}", headers=h)).json()
    assert il_now["description"] == "Chicago note."

    # The parent is part of the card: set in Michigan, it applies in Illinois
    # to Illinois's own gang for the parent card.
    await _patch_gang(client, h, mi, mi_lk["id"], {"parent_id": mi_parent["id"]})
    il_now = (await client.get(f"/api/v1/gangs/{il_lk['id']}?universe_id={il}", headers=h)).json()
    assert il_now["parent_id"] == il_parent["id"]
    mi_now = (await client.get(f"/api/v1/gangs/{mi_lk['id']}?universe_id={mi}", headers=h)).json()
    assert mi_now["parent_id"] == mi_parent["id"]


async def test_a_new_parent_gang_adopts_existing_branches(
    client: AsyncClient, db_session: AsyncSession
):
    """A universe that gains the parent card later sees its branch file under it."""
    h = await _admin(client, db_session)
    a = await _universe(client, h)
    b = await _universe(client, h)
    parent_name, child_name = f"Bloods {_uid()}", f"Pirus {_uid()}"
    a_parent = await _gang(client, h, a, parent_name)
    await _gang(client, h, a, child_name, parent_id=a_parent["id"])
    b_child = await _gang(client, h, b, child_name)
    assert b_child["parent_id"] is None  # universe b has no parent gang yet
    b_parent = await _gang(client, h, b, parent_name)
    b_child_now = (
        await client.get(f"/api/v1/gangs/{b_child['id']}?universe_id={b}", headers=h)
    ).json()
    assert b_child_now["parent_id"] == b_parent["id"]
