"""API integration tests for the /api/v1/municipalities/ vertical slice."""

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


async def test_create_municipality(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": universe_id, "name": "Detroit"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Detroit"
    assert data["parent_id"] is None


async def test_create_municipality_with_parent(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    parent = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "Detroit"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": universe_id, "name": "Midtown", "parent_id": parent["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["parent_id"] == parent["id"]


async def test_list_municipalities(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": universe_id, "name": "Flint"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"/api/v1/municipalities/?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_municipality(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "Pontiac"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.get(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pontiac"


async def test_get_municipality_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    resp = await client.get(
        f"/api/v1/municipalities/{uuid.uuid4()}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_municipality(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "OldName"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        json={"name": "NewName"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"


async def test_delete_municipality_admin(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "DeleteMe"},
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


async def test_delete_municipality_forbidden_for_user(
    client: AsyncClient, db_session: AsyncSession
):
    admin_token = await _admin_token(client, db_session)
    user_token = await _user_token(client, db_session)
    universe_id = await _make_universe(client, admin_token)
    created = (
        await client.post(
            "/api/v1/municipalities/",
            json={"universe_id": universe_id, "name": "Protected"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/municipalities/{created['id']}?universe_id={universe_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_list_rolls_district_incidents_into_the_city(
    client: AsyncClient, db_session: AsyncSession
):
    """A city's total counts its districts' incidents; set_count follows anchor and territory.

    Regression: the list showed only incidents filed on the city itself, and
    incidents are usually filed under a district, so Detroit read 23 of 42.
    """
    token = await _admin_token(client, db_session)
    universe_id = await _make_universe(client, token)
    auth = {"Authorization": f"Bearer {token}"}

    async def post(path: str, body: dict) -> str:
        resp = await client.post(path, json={"universe_id": universe_id, **body}, headers=auth)
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    city = await post("/api/v1/municipalities/", {"name": "Detroit"})
    district = await post("/api/v1/municipalities/", {"name": "48205", "parent_id": city})
    other = await post("/api/v1/municipalities/", {"name": "Flint"})
    await post("/api/v1/incidents/", {"type": "SHOOTING", "municipality_id": city})
    for _ in range(2):
        await post("/api/v1/incidents/", {"type": "SHOOTING", "municipality_id": district})
    # One set, anchored on the city and claiming the district as territory.
    await post(
        "/api/v1/sets/",
        {"name": f"Set {_uid()}", "municipality_id": city, "territory_ids": [district]},
    )

    resp = await client.get(
        "/api/v1/municipalities/", params={"universe_id": universe_id, "limit": 1000}, headers=auth
    )
    assert resp.status_code == 200
    rows = {r["id"]: r for r in resp.json()["items"]}
    assert rows[city]["incident_count"] == 1
    assert rows[city]["total_incident_count"] == 3
    assert rows[district]["total_incident_count"] == 2
    assert rows[other]["total_incident_count"] == 0
    assert rows[city]["set_count"] == 1
    assert rows[district]["set_count"] == 1
    assert rows[other]["set_count"] == 0


# --- Intel: kind, aliases, region, description, sources ---------------------


async def _post_muni(client: AsyncClient, token: str, **body) -> dict:
    resp = await client.post(
        "/api/v1/municipalities/", json=body, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_kind_follows_parent(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    city = await _post_muni(client, token, universe_id=uni, name="Detroit")
    zip_ = await _post_muni(client, token, universe_id=uni, name="48206", parent_id=city["id"])
    hood = await _post_muni(
        client,
        token,
        universe_id=uni,
        name="Dexter-Linwood",
        parent_id=city["id"],
        kind="NEIGHBORHOOD",
    )
    assert (city["kind"], zip_["kind"], hood["kind"]) == ("CITY", "DISTRICT", "NEIGHBORHOOD")


async def test_kind_parent_mismatch_refused(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    h = {"Authorization": f"Bearer {token}"}
    orphan = await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": uni, "name": "Brightmoor", "kind": "NEIGHBORHOOD"},
        headers=h,
    )
    assert orphan.status_code == 422
    city = await _post_muni(client, token, universe_id=uni, name="Detroit")
    zip_ = await _post_muni(client, token, universe_id=uni, name="48219", parent_id=city["id"])
    nested = await client.post(
        "/api/v1/municipalities/",
        json={"universe_id": uni, "name": "Brightmoor", "parent_id": zip_["id"]},
        headers=h,
    )
    assert nested.status_code == 422
    # A city holding districts cannot itself be moved under another city.
    other = await _post_muni(client, token, universe_id=uni, name="Wayne County")
    moved = await client.patch(
        f"/api/v1/municipalities/{city['id']}?universe_id={uni}",
        json={"parent_id": other["id"]},
        headers=h,
    )
    assert moved.status_code == 422


async def test_detaching_district_makes_it_a_city(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    city = await _post_muni(client, token, universe_id=uni, name="Detroit")
    hood = await _post_muni(
        client,
        token,
        universe_id=uni,
        name="Highland Park",
        parent_id=city["id"],
        kind="NEIGHBORHOOD",
    )
    resp = await client.patch(
        f"/api/v1/municipalities/{hood['id']}?universe_id={uni}",
        json={"parent_id": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["kind"] == "CITY"


async def test_intel_fields_round_trip(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    h = {"Authorization": f"Bearer {token}"}
    city = await _post_muni(
        client,
        token,
        universe_id=uni,
        name="River Rouge",
        aliases=[" The Hole ", "the hole", "", "Rouge"],
        region="Downriver",
        description="Incorporated as a city in 1922.",
    )
    assert city["aliases"] == ["The Hole", "Rouge"]
    got = (
        await client.get(f"/api/v1/municipalities/{city['id']}?universe_id={uni}", headers=h)
    ).json()
    assert got["region"] == "Downriver"
    assert got["description"] == "Incorporated as a city in 1922."
    listed = (await client.get(f"/api/v1/municipalities/?universe_id={uni}", headers=h)).json()
    item = next(m for m in listed["items"] if m["id"] == city["id"])
    assert (item["kind"], item["aliases"], item["region"]) == (
        "CITY",
        ["The Hole", "Rouge"],
        "Downriver",
    )


async def test_search_matches_alias(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    city = await _post_muni(client, token, universe_id=uni, name="Hamtramck", aliases=["HAMTOWN"])
    resp = await client.get(
        f"/api/v1/municipalities/search?universe_id={uni}&q=hamto",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert [m["id"] for m in resp.json()] == [city["id"]]


async def test_sources_link_and_replace(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    h = {"Authorization": f"Bearer {token}"}
    src = []
    for title in ("Map placemark", "City history"):
        r = await client.post(
            "/api/v1/sources/",
            json={"universe_id": uni, "title": title, "url": f"https://e.x/{_uid()}"},
            headers=h,
        )
        assert r.status_code == 201, r.text
        src.append(r.json()["id"])
    city = await _post_muni(client, token, universe_id=uni, name="Ecorse", source_ids=[src[0]])
    url = f"/api/v1/municipalities/{city['id']}?universe_id={uni}"
    assert [s["id"] for s in (await client.get(url, headers=h)).json()["sources"]] == [src[0]]

    resp = await client.patch(url, json={"source_ids": [src[1]]}, headers=h)
    assert [s["title"] for s in resp.json()["sources"]] == ["City history"]
    # A PATCH without source_ids leaves the links alone.
    resp = await client.patch(url, json={"region": "Downriver"}, headers=h)
    assert [s["id"] for s in resp.json()["sources"]] == [src[1]]

    bad = await client.patch(url, json={"source_ids": [str(uuid.uuid4())]}, headers=h)
    assert bad.status_code == 422
    assert [s["id"] for s in (await client.get(url, headers=h)).json()["sources"]] == [src[1]]


async def test_geojson_kind_filter(client: AsyncClient, db_session: AsyncSession):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    square = {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}
    city = await _post_muni(client, token, universe_id=uni, name="Detroit", geometry=square)
    await _post_muni(
        client, token, universe_id=uni, name="48206", parent_id=city["id"], geometry=square
    )
    await _post_muni(
        client,
        token,
        universe_id=uni,
        name="Zone 6",
        parent_id=city["id"],
        geometry=square,
        kind="NEIGHBORHOOD",
    )
    h = {"Authorization": f"Bearer {token}"}
    base = f"/api/v1/municipalities/geojson?universe_id={uni}&parent_id={city['id']}"

    def names(r):
        return sorted(f["properties"]["name"] for f in r.json()["features"])

    assert names(await client.get(base, headers=h)) == ["48206", "Zone 6"]
    assert names(await client.get(base + "&kind=DISTRICT", headers=h)) == ["48206"]
    assert names(await client.get(base + "&kind=NEIGHBORHOOD", headers=h)) == ["Zone 6"]


async def test_population_reads_back_with_its_year_and_source(
    client: AsyncClient, db_session: AsyncSession
):
    # Written only by app/scripts/import_populations.py, so set it on the row.
    from app.models.municipality import Municipality

    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    city = await _post_muni(client, token, universe_id=uni, name="River Rouge")
    row = await db_session.get(Municipality, uuid.UUID(city["id"]))
    row.population, row.population_year = 6814, 2025
    row.population_source = "US Census Bureau, Vintage 2025 estimates"
    await db_session.commit()

    h = {"Authorization": f"Bearer {token}"}
    got = (
        await client.get(f"/api/v1/municipalities/{city['id']}?universe_id={uni}", headers=h)
    ).json()
    assert (got["population"], got["population_year"], got["population_source"]) == (
        6814,
        2025,
        "US Census Bureau, Vintage 2025 estimates",
    )
    listed = (await client.get(f"/api/v1/municipalities/?universe_id={uni}", headers=h)).json()
    item = next(m for m in listed["items"] if m["id"] == city["id"])
    assert (item["population"], item["population_year"]) == (6814, 2025)


def _square(x0: float, y0: float, x1: float, y1: float) -> dict:
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]]]}


async def test_neighborhood_overlaps_follow_the_outlines(
    client: AsyncClient, db_session: AsyncSession
):
    token = await _admin_token(client, db_session)
    uni = await _make_universe(client, token)
    h = {"Authorization": f"Bearer {token}"}
    city = await _post_muni(client, token, universe_id=uni, name="Detroit")
    west = await _post_muni(
        client,
        token,
        universe_id=uni,
        name="48206",
        parent_id=city["id"],
        geometry=_square(0, 0, 1, 1),
    )
    east = await _post_muni(
        client,
        token,
        universe_id=uni,
        name="48238",
        parent_id=city["id"],
        geometry=_square(1, 0, 2, 1),
    )
    # 70% in the west district, 30% in the east one.
    hood = await _post_muni(
        client,
        token,
        universe_id=uni,
        name="Dexter-Linwood",
        parent_id=city["id"],
        kind="NEIGHBORHOOD",
        geometry=_square(0.3, 0, 1.3, 1),
    )

    def url(m):
        return f"/api/v1/municipalities/{m['id']}?universe_id={uni}"

    got = (await client.get(url(hood), headers=h)).json()["overlaps"]
    assert [(o["name"], round(o["share_of_neighborhood"], 2)) for o in got] == [
        ("48206", 0.7),
        ("48238", 0.3),
    ]
    from_zip = (await client.get(url(east), headers=h)).json()["overlaps"]
    assert [(o["name"], o["kind"], round(o["share_of_district"], 2)) for o in from_zip] == [
        ("Dexter-Linwood", "NEIGHBORHOOD", 0.3)
    ]

    # Moving the outline recomputes both sides; a 1% sliver is not an overlap.
    await client.patch(url(hood), json={"geometry": _square(0, 0, 0.99, 1)}, headers=h)
    got = (await client.get(url(hood), headers=h)).json()["overlaps"]
    assert [(o["name"], round(o["share_of_neighborhood"], 2)) for o in got] == [("48206", 1.0)]
    await client.patch(url(hood), json={"geometry": _square(0.985, 0, 1.985, 1)}, headers=h)
    got = (await client.get(url(hood), headers=h)).json()["overlaps"]
    assert [o["name"] for o in got] == ["48238"]
    assert (await client.get(url(west), headers=h)).json()["overlaps"] == []

    # Moving a district recomputes the neighborhoods nobody touched.
    await client.patch(url(west), json={"geometry": _square(1, 0, 2, 1)}, headers=h)
    got = (await client.get(url(hood), headers=h)).json()["overlaps"]
    assert sorted(o["name"] for o in got) == ["48206", "48238"]
