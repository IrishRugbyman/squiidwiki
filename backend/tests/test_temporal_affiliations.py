"""Time dimension on member_set and set_relationships.

The point of the surrogate key + from_date/until_date is that a pair can hold
more than one spell: allies until they fell out, then enemies; a member who
left one set for another. These tests pin the invariants that make that work.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole, SetRelationshipType
from app.crud.gang_set import (
    add_set_relationship,
    create_gang_set,
    end_set_relationship,
    list_gang_sets,
    list_set_relationship_history,
    list_set_relationships,
    update_gang_set,
)
from app.crud.member import (
    create_member,
    end_member_affiliation,
    load_member_affiliations,
)
from app.crud.universe import create_universe
from app.models.gang_set import SetRelationship
from app.schemas.gang_set import SetCreate, SetUpdate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn
from app.schemas.universe import UniverseCreate

pytestmark = pytest.mark.asyncio(loop_scope="session")

Y2012 = {"year": 2012, "precision": "Y", "approx": False}
Y2007 = {"year": 2007, "precision": "Y", "approx": False}


async def _setup(session: AsyncSession):
    user = await create_user(session, f"u{uuid.uuid4().hex[:6]}@x.com", "pw", GlobalRole.ADMIN)
    universe = await create_universe(
        session, UniverseCreate(name="T", slug=f"t-{uuid.uuid4().hex[:6]}"), user.id
    )
    a = await create_gang_set(session, SetCreate(universe_id=universe.id, name="A"), user.id)
    b = await create_gang_set(session, SetCreate(universe_id=universe.id, name="B"), user.id)
    return user, universe, a, b


# ── set relationships ────────────────────────────────────────────────────────


async def test_ending_a_link_removes_it_from_current_but_keeps_it(db_session: AsyncSession):
    _, uni, a, b = await _setup(db_session)
    await add_set_relationship(db_session, a.id, b.id, SetRelationshipType.FRIEND, uni.id)

    history = await list_set_relationship_history(db_session, a.id)
    assert len(history) == 1
    assert await end_set_relationship(db_session, a.id, history[0]["id"], Y2012) is True

    friends, enemies = await list_set_relationships(db_session, a.id, uni.id)
    assert friends == [] and enemies == []

    history = await list_set_relationship_history(db_session, a.id)
    assert len(history) == 1
    assert history[0]["is_current"] is False
    assert history[0]["until_date"] == Y2012
    assert history[0]["other_id"] == b.id


async def test_pair_can_flip_from_ally_to_enemy(db_session: AsyncSession):
    """The motivating case: allies until 2012, enemies since."""
    _, uni, a, b = await _setup(db_session)
    await add_set_relationship(db_session, a.id, b.id, SetRelationshipType.FRIEND, uni.id)
    open_link = (await list_set_relationship_history(db_session, a.id))[0]
    await end_set_relationship(db_session, a.id, open_link["id"], Y2012)
    await add_set_relationship(db_session, a.id, b.id, SetRelationshipType.ENEMY, uni.id)

    friends, enemies = await list_set_relationships(db_session, a.id, uni.id)
    assert friends == []
    assert enemies == [b.id]

    history = await list_set_relationship_history(db_session, a.id)
    assert len(history) == 2
    current = [h for h in history if h["is_current"]]
    past = [h for h in history if not h["is_current"]]
    assert len(current) == 1 and current[0]["type"] == SetRelationshipType.ENEMY
    assert len(past) == 1 and past[0]["type"] == SetRelationshipType.FRIEND


async def test_two_open_links_for_one_pair_are_rejected(db_session: AsyncSession):
    _, uni, a, b = await _setup(db_session)
    await add_set_relationship(db_session, a.id, b.id, SetRelationshipType.FRIEND, uni.id)
    lo, hi = (a.id, b.id) if a.id < b.id else (b.id, a.id)
    db_session.add(
        SetRelationship(set_a_id=lo, set_b_id=hi, relationship_type=SetRelationshipType.ENEMY)
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_editing_current_links_leaves_closed_ones_alone(db_session: AsyncSession):
    """Clearing the ally list is not the same as erasing the set's past."""
    user, uni, a, b = await _setup(db_session)
    await add_set_relationship(db_session, a.id, b.id, SetRelationshipType.FRIEND, uni.id)
    open_link = (await list_set_relationship_history(db_session, a.id))[0]
    await end_set_relationship(db_session, a.id, open_link["id"], Y2012)

    await update_gang_set(db_session, a.id, uni.id, SetUpdate(friend_ids=[], enemy_ids=[]))

    history = await list_set_relationship_history(db_session, a.id)
    assert len(history) == 1
    assert history[0]["until_date"] == Y2012


async def test_none_until_date_is_sql_null_not_json_null(db_session: AsyncSession):
    """Regression: JSONB columns serialise Python None to JSON 'null' by default.

    A row stored that way is invisible to `until_date IS NULL`, so it escapes
    both the current-spell queries and the partial unique index, which silently
    permits two open links for one pair.
    """
    _, uni, a, b = await _setup(db_session)
    await add_set_relationship(db_session, a.id, b.id, SetRelationshipType.FRIEND, uni.id)
    lo, hi = (a.id, b.id) if a.id < b.id else (b.id, a.id)
    json_nulls = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM set_relationships "
                "WHERE set_a_id = :lo AND set_b_id = :hi AND until_date = 'null'::jsonb"
            ),
            {"lo": lo, "hi": hi},
        )
    ).scalar_one()
    assert json_nulls == 0


# ── member affiliations ──────────────────────────────────────────────────────


async def test_member_leaving_a_set_keeps_the_spell_and_drops_the_headcount(
    db_session: AsyncSession,
):
    user, uni, a, _ = await _setup(db_session)
    stayer = await create_member(
        db_session,
        MemberCreate(
            universe_id=uni.id,
            nickname="Stayer",
            affiliations=[MemberSetAffiliationIn(set_id=a.id)],
        ),
        user.id,
    )
    leaver = await create_member(
        db_session,
        MemberCreate(
            universe_id=uni.id,
            nickname="Leaver",
            affiliations=[MemberSetAffiliationIn(set_id=a.id)],
        ),
        user.id,
    )

    sets, _ = await list_gang_sets(db_session, uni.id)
    assert next(s._member_count for s in sets if s.id == a.id) == 2

    spell = (await load_member_affiliations(db_session, [leaver.id]))[leaver.id][0]
    assert await end_member_affiliation(db_session, leaver.id, spell.id, Y2007) is True

    sets, _ = await list_gang_sets(db_session, uni.id)
    assert next(s._member_count for s in sets if s.id == a.id) == 1

    # The spell survives as history, and is no longer the member's primary set.
    affs = (await load_member_affiliations(db_session, [leaver.id]))[leaver.id]
    assert len(affs) == 1
    assert affs[0].is_current is False
    assert affs[0].until_date == Y2007
    assert affs[0].is_primary is False

    still_there = (await load_member_affiliations(db_session, [stayer.id]))[stayer.id]
    assert still_there[0].is_current is True


async def test_member_can_rejoin_a_set_they_left(db_session: AsyncSession):
    user, uni, a, _ = await _setup(db_session)
    m = await create_member(
        db_session,
        MemberCreate(
            universe_id=uni.id,
            nickname="Returner",
            affiliations=[MemberSetAffiliationIn(set_id=a.id)],
        ),
        user.id,
    )
    spell = (await load_member_affiliations(db_session, [m.id]))[m.id][0]
    await end_member_affiliation(db_session, m.id, spell.id, Y2007)

    from app.crud.member import _sync_member_sets

    await _sync_member_sets(db_session, m.id, [MemberSetAffiliationIn(set_id=a.id)])
    await db_session.commit()

    affs = (await load_member_affiliations(db_session, [m.id]))[m.id]
    assert len(affs) == 2
    assert [x.is_current for x in affs] == [True, False]


async def test_a_closed_spell_cannot_be_closed_again(db_session: AsyncSession):
    user, uni, a, _ = await _setup(db_session)
    m = await create_member(
        db_session,
        MemberCreate(
            universe_id=uni.id, nickname="X", affiliations=[MemberSetAffiliationIn(set_id=a.id)]
        ),
        user.id,
    )
    spell = (await load_member_affiliations(db_session, [m.id]))[m.id][0]
    assert await end_member_affiliation(db_session, m.id, spell.id, Y2007) is True
    assert await end_member_affiliation(db_session, m.id, spell.id, Y2012) is False

    affs = (await load_member_affiliations(db_session, [m.id]))[m.id]
    assert affs[0].until_date == Y2007
