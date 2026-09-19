"""Family ties: the JSONB column, and the inverse the backend writes for you.

The roles are gender-neutral (`parent`, `child`, `sibling`, `cousin`, `spouse`,
`uncle`, `nephew`). They were `father`, `son` and `brother` until a sister had
to be recorded and there was nowhere to put her, so these tests pin the two
things that change behaviour rather than wording: `parent` is a list, where
`father` was a single id, and every role still mirrors onto the relative.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole
from app.crud.member import INVERSE_REL, create_member, delete_member, update_member
from app.crud.universe import create_universe
from app.schemas.member import MemberCreate, MemberUpdate
from app.schemas.universe import UniverseCreate


async def _universe(session: AsyncSession):
    user = await create_user(session, f"u{uuid.uuid4().hex[:6]}@x.com", "pw", GlobalRole.ADMIN)
    universe = await create_universe(
        session, UniverseCreate(name="Test", slug=f"t-{uuid.uuid4().hex[:6]}"), user.id
    )
    return universe, user.id


async def _member(session: AsyncSession, universe_id, actor_id, name: str):
    return await create_member(
        session, MemberCreate(universe_id=universe_id, nickname=name), actor_id
    )


async def _refresh(session: AsyncSession, member):
    await session.refresh(member)
    return member


def test_every_role_has_an_inverse_and_the_vocabulary_is_neutral():
    # A role with no inverse is written on one row and rendered on neither, and
    # a gendered role is one half of a pair the other half of which cannot be
    # stored at all.
    assert set(INVERSE_REL) == {
        "parent",
        "child",
        "sibling",
        "cousin",
        "spouse",
        "uncle",
        "nephew",
    }
    for role, inverse in INVERSE_REL.items():
        assert INVERSE_REL[inverse] == role


@pytest.mark.asyncio(loop_scope="session")
async def test_a_parent_tie_writes_the_child_back(db_session: AsyncSession):
    universe, actor = await _universe(db_session)
    father = await _member(db_session, universe.id, actor, "Father")
    son = await _member(db_session, universe.id, actor, "Son")

    await update_member(
        db_session, son.id, universe.id, MemberUpdate(family={"parent": [str(father.id)]})
    )

    assert (await _refresh(db_session, son)).family == {"parent": [str(father.id)]}
    assert (await _refresh(db_session, father)).family == {"child": [str(son.id)]}


@pytest.mark.asyncio(loop_scope="session")
async def test_a_member_can_have_two_parents(db_session: AsyncSession):
    # The whole point of the rename. `father` was a single id, so a mother had
    # nowhere to go and a second parent overwrote the first.
    universe, actor = await _universe(db_session)
    child = await _member(db_session, universe.id, actor, "Child")
    mother = await _member(db_session, universe.id, actor, "Mother")
    father = await _member(db_session, universe.id, actor, "Father")

    await update_member(
        db_session,
        child.id,
        universe.id,
        MemberUpdate(family={"parent": [str(mother.id), str(father.id)]}),
    )

    stored = (await _refresh(db_session, child)).family["parent"]
    assert sorted(stored) == sorted([str(mother.id), str(father.id)])
    assert (await _refresh(db_session, mother)).family == {"child": [str(child.id)]}
    assert (await _refresh(db_session, father)).family == {"child": [str(child.id)]}


@pytest.mark.asyncio(loop_scope="session")
async def test_a_sibling_tie_is_its_own_inverse(db_session: AsyncSession):
    universe, actor = await _universe(db_session)
    brother = await _member(db_session, universe.id, actor, "Brother")
    sister = await _member(db_session, universe.id, actor, "Sister")

    await update_member(
        db_session, sister.id, universe.id, MemberUpdate(family={"sibling": [str(brother.id)]})
    )

    assert (await _refresh(db_session, brother)).family == {"sibling": [str(sister.id)]}


@pytest.mark.asyncio(loop_scope="session")
async def test_removing_a_tie_removes_it_on_both_rows(db_session: AsyncSession):
    universe, actor = await _universe(db_session)
    a = await _member(db_session, universe.id, actor, "A")
    b = await _member(db_session, universe.id, actor, "B")

    await update_member(db_session, a.id, universe.id, MemberUpdate(family={"cousin": [str(b.id)]}))
    await update_member(db_session, a.id, universe.id, MemberUpdate(family={}))

    assert (await _refresh(db_session, a)).family in (None, {})
    assert (await _refresh(db_session, b)).family is None


@pytest.mark.asyncio(loop_scope="session")
async def test_dropping_one_parent_keeps_the_other(db_session: AsyncSession):
    # The PATCH carries the whole dict, so this is the path where a client that
    # sends only its own new ties silently detaches everything else.
    universe, actor = await _universe(db_session)
    child = await _member(db_session, universe.id, actor, "Child")
    mother = await _member(db_session, universe.id, actor, "Mother")
    father = await _member(db_session, universe.id, actor, "Father")

    await update_member(
        db_session,
        child.id,
        universe.id,
        MemberUpdate(family={"parent": [str(mother.id), str(father.id)]}),
    )
    await update_member(
        db_session, child.id, universe.id, MemberUpdate(family={"parent": [str(mother.id)]})
    )

    assert (await _refresh(db_session, child)).family == {"parent": [str(mother.id)]}
    assert (await _refresh(db_session, mother)).family == {"child": [str(child.id)]}
    assert (await _refresh(db_session, father)).family is None


@pytest.mark.asyncio(loop_scope="session")
async def test_deleting_a_member_detaches_the_ties_pointing_at_him(db_session: AsyncSession):
    universe, actor = await _universe(db_session)
    parent = await _member(db_session, universe.id, actor, "Parent")
    child = await _member(db_session, universe.id, actor, "Child")

    await update_member(
        db_session, child.id, universe.id, MemberUpdate(family={"parent": [str(parent.id)]})
    )
    await delete_member(db_session, child.id, universe.id)

    assert (await _refresh(db_session, parent)).family is None
