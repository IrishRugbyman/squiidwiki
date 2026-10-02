"""A set's territory: one GeoJSON Polygon, or a MultiPolygon for ground in several pieces.

1000 TG holds three separate pieces (its first East Warren block and two in
Mount Clemens), which a single Polygon cannot carry. Expected values come from
the GeoJSON spec (RFC 7946 3.1.6-3.1.7), not from running the code: every ring
of every polygon closes on its first position and has at least four.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _square(x: float, y: float) -> list[list[float]]:
    return [[x, y], [x + 0.01, y], [x + 0.01, y + 0.01], [x, y + 0.01], [x, y]]


async def _setup(client: AsyncClient, session: AsyncSession) -> tuple[dict, str, str]:
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    tag = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/v1/universes/", json={"name": f"Uni {tag}", "slug": f"uni-{tag}"}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    universe_id = resp.json()["id"]
    set_id = (
        await client.post(
            "/api/v1/sets/",
            json={"universe_id": universe_id, "name": f"Set {uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
    ).json()["id"]
    return headers, universe_id, set_id


async def _patch(client, headers, universe_id, set_id, polygon):
    return await client.patch(
        f"/api/v1/sets/{set_id}?universe_id={universe_id}",
        json={"territory_polygon": polygon},
        headers=headers,
    )


async def test_multipolygon_territory_is_stored_and_served(
    client: AsyncClient, db_session: AsyncSession
):
    headers, universe_id, set_id = await _setup(client, db_session)
    pieces = {
        "type": "MultiPolygon",
        "coordinates": [
            [_square(-82.99, 42.40)],
            [_square(-82.87, 42.58)],
            [_square(-82.86, 42.60)],
        ],
    }

    resp = await _patch(client, headers, universe_id, set_id, pieces)
    assert resp.status_code == 200, resp.text

    served = (
        await client.get(
            f"/api/v1/sets/territory-polygons?universe_id={universe_id}", headers=headers
        )
    ).json()
    mine = next(s for s in served if s["id"] == set_id)
    assert mine["territory_polygon"] == pieces


async def test_single_polygon_still_accepted(client: AsyncClient, db_session: AsyncSession):
    headers, universe_id, set_id = await _setup(client, db_session)
    one = {"type": "Polygon", "coordinates": [_square(-83.0, 42.4)]}
    resp = await _patch(client, headers, universe_id, set_id, one)
    assert resp.status_code == 200, resp.text


@pytest.mark.parametrize(
    "bad",
    [
        # A piece whose ring does not close on its first position.
        {"type": "MultiPolygon", "coordinates": [[_square(0, 0)], [_square(1, 1)[:-1] + [[9, 9]]]]},
        # A piece with a three-position ring.
        {"type": "MultiPolygon", "coordinates": [[[[0, 0], [1, 0], [0, 0]]]]},
        # No pieces at all.
        {"type": "MultiPolygon", "coordinates": []},
        # A piece that is a bare ring, one nesting level short.
        {"type": "MultiPolygon", "coordinates": [_square(0, 0)]},
        # Not an area at all.
        {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
    ],
)
async def test_malformed_territory_is_refused(
    client: AsyncClient, db_session: AsyncSession, bad: dict
):
    headers, universe_id, set_id = await _setup(client, db_session)
    resp = await _patch(client, headers, universe_id, set_id, bad)
    assert resp.status_code == 422, resp.text
