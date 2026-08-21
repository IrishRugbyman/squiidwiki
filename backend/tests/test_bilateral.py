"""100% coverage on bilateral set relationship logic per the plan."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole, SetRelationshipType
from app.crud.gang_set import (
    add_set_relationship,
    create_gang_set,
    list_set_relationships,
    remove_set_relationship,
    update_gang_set,
)
from app.crud.universe import create_universe
from app.schemas.gang_set import SetCreate, SetUpdate
from app.schemas.universe import UniverseCreate

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _setup(session: AsyncSession):
    user = await create_user(session, f"u{uuid.uuid4().hex[:6]}@x.com", "pw", GlobalRole.ADMIN)
    universe = await create_universe(
        session, UniverseCreate(name="Test", slug=f"t-{uuid.uuid4().hex[:6]}"), user.id
    )
    set_a = await create_gang_set(
        session, SetCreate(universe_id=universe.id, name="Set A"), user.id
    )
    set_b = await create_gang_set(
        session, SetCreate(universe_id=universe.id, name="Set B"), user.id
    )
    return universe, set_a, set_b


@pytest.mark.asyncio
async def test_add_friend_relationship(db_session: AsyncSession):
    universe, set_a, set_b = await _setup(db_session)
    await add_set_relationship(
        db_session, set_a.id, set_b.id, SetRelationshipType.FRIEND, universe.id
    )
    friends, enemies = await list_set_relationships(db_session, set_a.id, universe.id)
    assert set_b.id in friends
    assert set_b.id not in enemies


@pytest.mark.asyncio
async def test_add_enemy_relationship(db_session: AsyncSession):
    universe, set_a, set_b = await _setup(db_session)
    await add_set_relationship(
        db_session, set_a.id, set_b.id, SetRelationshipType.ENEMY, universe.id
    )
    friends, enemies = await list_set_relationships(db_session, set_a.id, universe.id)
    assert set_b.id in enemies
    assert set_b.id not in friends


@pytest.mark.asyncio
async def test_relationship_is_bilateral(db_session: AsyncSession):
    universe, set_a, set_b = await _setup(db_session)
    await add_set_relationship(
        db_session, set_a.id, set_b.id, SetRelationshipType.FRIEND, universe.id
    )
    # visible from both sides
    friends_a, _ = await list_set_relationships(db_session, set_a.id, universe.id)
    friends_b, _ = await list_set_relationships(db_session, set_b.id, universe.id)
    assert set_b.id in friends_a
    assert set_a.id in friends_b


@pytest.mark.asyncio
async def test_conflict_raises(db_session: AsyncSession):
    from fastapi import HTTPException

    universe, set_a, set_b = await _setup(db_session)
    await add_set_relationship(
        db_session, set_a.id, set_b.id, SetRelationshipType.FRIEND, universe.id
    )
    with pytest.raises(HTTPException) as exc_info:
        await add_set_relationship(
            db_session, set_a.id, set_b.id, SetRelationshipType.ENEMY, universe.id
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_remove_relationship(db_session: AsyncSession):
    universe, set_a, set_b = await _setup(db_session)
    await add_set_relationship(
        db_session, set_a.id, set_b.id, SetRelationshipType.FRIEND, universe.id
    )
    ok = await remove_set_relationship(db_session, set_a.id, set_b.id, universe.id)
    assert ok is True
    friends, _ = await list_set_relationships(db_session, set_a.id, universe.id)
    assert set_b.id not in friends


@pytest.mark.asyncio
async def test_remove_nonexistent_returns_false(db_session: AsyncSession):
    universe, set_a, set_b = await _setup(db_session)
    ok = await remove_set_relationship(db_session, set_a.id, set_b.id, universe.id)
    assert ok is False


@pytest.mark.asyncio
async def test_normalization_commutative(db_session: AsyncSession):
    """Insert with B,A order should still store as (min,max) and be found."""
    universe, set_a, set_b = await _setup(db_session)
    # Insert with reversed arg order
    await add_set_relationship(
        db_session, set_b.id, set_a.id, SetRelationshipType.ENEMY, universe.id
    )
    _, enemies = await list_set_relationships(db_session, set_a.id, universe.id)
    assert set_b.id in enemies


@pytest.mark.asyncio
async def test_sync_is_idempotent_across_both_endpoints(db_session: AsyncSession):
    """Saving B's list must not collide with the edge A's save already wrote.

    Regression: _sync_set_relationships used to delete every current row and
    re-add the wanted ones. SQLAlchemy flushes INSERTs before DELETEs, so
    re-adding a pair that was still wanted hit uq_set_relationship_current and
    surfaced as a 500. Bilateral edges make that the normal case, not an edge
    case: saving either end re-asserts the same pair.
    """
    universe, set_a, set_b = await _setup(db_session)

    await update_gang_set(db_session, set_a.id, universe.id, SetUpdate(friend_ids=[set_b.id]))
    # Same edge from the other side - this is what used to raise.
    await update_gang_set(db_session, set_b.id, universe.id, SetUpdate(friend_ids=[set_a.id]))
    # And again, unchanged.
    await update_gang_set(db_session, set_a.id, universe.id, SetUpdate(friend_ids=[set_b.id]))

    friends, enemies = await list_set_relationships(db_session, set_a.id, universe.id)
    assert friends == [set_b.id]
    assert enemies == []
    friends_b, _ = await list_set_relationships(db_session, set_b.id, universe.id)
    assert friends_b == [set_a.id]


@pytest.mark.asyncio
async def test_sync_flips_relationship_type(db_session: AsyncSession):
    """A pair that changes side is deleted and re-inserted, not duplicated."""
    universe, set_a, set_b = await _setup(db_session)
    await update_gang_set(db_session, set_a.id, universe.id, SetUpdate(friend_ids=[set_b.id]))
    await update_gang_set(db_session, set_a.id, universe.id, SetUpdate(enemy_ids=[set_b.id]))
    friends, enemies = await list_set_relationships(db_session, set_a.id, universe.id)
    assert friends == []
    assert enemies == [set_b.id]


@pytest.mark.asyncio
async def test_sync_drops_edges_left_out_of_the_list(db_session: AsyncSession):
    universe, set_a, set_b = await _setup(db_session)
    await update_gang_set(db_session, set_a.id, universe.id, SetUpdate(friend_ids=[set_b.id]))
    await update_gang_set(db_session, set_a.id, universe.id, SetUpdate(friend_ids=[], enemy_ids=[]))
    friends, enemies = await list_set_relationships(db_session, set_a.id, universe.id)
    assert friends == []
    assert enemies == []
