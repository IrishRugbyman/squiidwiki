"""A set's name is derived from its primary name variant, never set on its own.

The expected strings here are written out by hand from the rule (lead slots,
in order, joined by a space), not computed with app.core.set_names, so a bug in
that module cannot make its own tests pass.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole
from app.core.set_names import display_name, normalize_lead, variant_display

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _auth(client: AsyncClient, session: AsyncSession) -> dict:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _universe(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ---- the display rule, without the API -------------------------------------


@pytest.mark.parametrize(
    ("variant", "expected"),
    [
        ({"name": "Helmet Crew", "initials": "HMC", "number": "462", "lead": "initials"}, "HMC"),
        ({"initials": "CFP", "number": "2400", "lead": ["initials", "number"]}, "CFP 2400"),
        ({"name": "Young Money", "number": "051", "lead": ["number", "name"]}, "051 Young Money"),
        ({"name": "No Limit", "number": "083", "lead": ["name", "number"]}, "No Limit 083"),
        (
            {"name": "Central & Navy", "initials": "CFP", "lead": ["initials", "name"]},
            "CFP Central & Navy",
        ),
        # No lead: name, then initials, then number.
        ({"name": "Trust No One", "initials": "TNO"}, "Trust No One"),
        ({"initials": "TNO", "number": "826"}, "TNO"),
        ({"number": "700"}, "700"),
        # A lead slot the variant leaves empty is skipped, never shown blank.
        ({"name": "Waxx Gang", "lead": ["number", "name"]}, "Waxx Gang"),
        ({"name": "Waxx Gang", "lead": "initials"}, "Waxx Gang"),
    ],
)
def test_variant_display(variant, expected):
    assert variant_display(variant) == expected


def test_normalize_lead_shapes():
    v = {"name": "No Limit", "number": "083"}
    assert normalize_lead(["name", "number"], v) == ["name", "number"]
    assert normalize_lead(["number"], v) == "number"
    assert normalize_lead(["initials", "name", "name"], v) == "name"
    assert normalize_lead("initials", v) is None
    assert normalize_lead(None, v) is None
    with pytest.raises(ValueError):
        normalize_lead("nickname", v)
    with pytest.raises(ValueError):
        normalize_lead(7, v)


def test_display_name_uses_the_primary():
    variants = [
        {"name": "Bemis Boyz"},
        {"name": "Bemis Boys", "number": "726", "is_primary": True},
    ]
    assert display_name(variants) == "Bemis Boys"
    assert display_name([{"name": "Bemis Boyz"}]) == "Bemis Boyz"
    assert display_name([]) == ""
    assert display_name(None) == ""


# ---- through the API -------------------------------------------------------


async def test_create_derives_name_from_combined_lead(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    resp = await client.post(
        "/api/v1/sets/",
        json={
            "universe_id": uni,
            "name_variants": [
                {
                    "initials": "CFP",
                    "number": "2400",
                    "lead": ["initials", "number"],
                    "is_primary": True,
                },
            ],
        },
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "CFP 2400"
    assert body["slug"] == "cfp-2400"
    assert body["name_variants"][0]["lead"] == ["initials", "number"]


async def test_create_with_name_only_seeds_the_primary_variant(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    resp = await client.post(
        "/api/v1/sets/", json={"universe_id": uni, "name": "Vinewood"}, headers=h
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Vinewood"
    assert len(body["name_variants"]) == 1
    assert body["name_variants"][0]["name"] == "Vinewood"
    assert body["name_variants"][0]["is_primary"] is True


async def test_create_refuses_a_name_the_variant_does_not_display(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    resp = await client.post(
        "/api/v1/sets/",
        json={
            "universe_id": uni,
            "name": "TNO",
            "name_variants": [{"name": "Trust No One", "initials": "TNO", "is_primary": True}],
        },
        headers=h,
    )
    assert resp.status_code == 422
    assert "Trust No One" in resp.text


async def test_create_with_nothing_is_refused(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    resp = await client.post("/api/v1/sets/", json={"universe_id": uni}, headers=h)
    assert resp.status_code == 422


async def test_saving_the_variants_unchanged_keeps_name_and_slug(client: AsyncClient, db_session):
    """The regression: four Cash Flow Posse sets each collapsing to "CFP" on Save."""
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    variants = [
        {"initials": "CFP", "number": "2400", "lead": ["initials", "number"], "is_primary": True},
        {"name": "The Flows"},
    ]
    created = (
        await client.post(
            "/api/v1/sets/", json={"universe_id": uni, "name_variants": variants}, headers=h
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/sets/{created['id']}?universe_id={uni}",
        json={"name": "CFP 2400", "name_variants": created["name_variants"], "bio": "x"},
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "CFP 2400"
    assert resp.json()["slug"] == created["slug"]


async def test_editing_the_primary_renames_and_reslugs(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    created = (
        await client.post(
            "/api/v1/sets/",
            json={
                "universe_id": uni,
                "name_variants": [{"name": "Trust No One", "initials": "TNO", "is_primary": True}],
            },
            headers=h,
        )
    ).json()
    assert created["name"] == "Trust No One"
    resp = await client.patch(
        f"/api/v1/sets/{created['id']}?universe_id={uni}",
        json={
            "name_variants": [
                {"name": "Trust No One", "initials": "TNO", "lead": "initials", "is_primary": True}
            ]
        },
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "TNO"
    assert resp.json()["slug"] == "tno"


async def test_patch_name_alone_is_refused(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    created = (
        await client.post("/api/v1/sets/", json={"universe_id": uni, "name": "Starlife"}, headers=h)
    ).json()
    resp = await client.patch(
        f"/api/v1/sets/{created['id']}?universe_id={uni}", json={"name": "Star Life"}, headers=h
    )
    assert resp.status_code == 422
    unchanged = (
        await client.get(f"/api/v1/sets/{created['id']}?universe_id={uni}", headers=h)
    ).json()
    assert unchanged["name"] == "Starlife"


async def test_patch_cannot_clear_the_variants(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    created = (
        await client.post("/api/v1/sets/", json={"universe_id": uni, "name": "Starlife"}, headers=h)
    ).json()
    resp = await client.patch(
        f"/api/v1/sets/{created['id']}?universe_id={uni}", json={"name_variants": []}, headers=h
    )
    assert resp.status_code == 422


async def test_patch_without_names_leaves_them_alone(client: AsyncClient, db_session):
    h = await _auth(client, db_session)
    uni = await _universe(client, h)
    created = (
        await client.post("/api/v1/sets/", json={"universe_id": uni, "name": "Starlife"}, headers=h)
    ).json()
    resp = await client.patch(
        f"/api/v1/sets/{created['id']}?universe_id={uni}", json={"bio": "Eastside crew."}, headers=h
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Starlife"
    assert resp.json()["slug"] == created["slug"]
