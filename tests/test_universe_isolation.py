"""Tests that entities in universe A are invisible to universe B when queried with universe scope."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Alliance, AllianceStatus, Member, MemberStatus, Set, SetType, Universe


class TestUniverseIsolation:
    """Scoped queries must not cross universe boundaries."""

    async def _make_universes(self, db: AsyncSession) -> tuple[Universe, Universe]:
        u1 = Universe(name="Alpha City", slug="alpha-city")
        u2 = Universe(name="Beta Town", slug="beta-town")
        db.add_all([u1, u2])
        await db.flush()
        return u1, u2

    # ── Sets ──────────────────────────────────────────────────────────────

    async def test_sets_isolated(self, db: AsyncSession):
        u1, u2 = await self._make_universes(db)
        db.add_all([
            Set(name="SetAlpha", type=SetType.ACTIVE, universe_id=u1.id),
            Set(name="SetBeta", type=SetType.ACTIVE, universe_id=u2.id),
        ])
        await db.flush()

        result = await db.execute(
            select(Set).where(Set.universe_id == u1.id, Set.deleted_at.is_(None))
        )
        sets = result.scalars().all()
        assert len(sets) == 1
        assert sets[0].name == "SetAlpha"

    async def test_sets_in_other_universe_invisible(self, db: AsyncSession):
        u1, u2 = await self._make_universes(db)
        db.add(Set(name="OnlyInU2", type=SetType.ACTIVE, universe_id=u2.id))
        await db.flush()

        result = await db.execute(
            select(Set).where(Set.universe_id == u1.id, Set.deleted_at.is_(None))
        )
        assert result.scalars().all() == []

    # ── Members ───────────────────────────────────────────────────────────

    async def test_members_isolated(self, db: AsyncSession):
        u1, u2 = await self._make_universes(db)
        db.add_all([
            Member(name="AlphaMember", status=MemberStatus.ALIVE, universe_id=u1.id),
            Member(name="BetaMember", status=MemberStatus.ALIVE, universe_id=u2.id),
        ])
        await db.flush()

        result = await db.execute(
            select(Member).where(Member.universe_id == u1.id, Member.deleted_at.is_(None))
        )
        members = result.scalars().all()
        assert len(members) == 1
        assert members[0].name == "AlphaMember"

    # ── Alliances ─────────────────────────────────────────────────────────

    async def test_alliances_isolated(self, db: AsyncSession):
        u1, u2 = await self._make_universes(db)
        db.add_all([
            Alliance(name="AlphaAlliance", status=AllianceStatus.ACTIVE, universe_id=u1.id),
            Alliance(name="BetaAlliance", status=AllianceStatus.ACTIVE, universe_id=u2.id),
        ])
        await db.flush()

        result = await db.execute(
            select(Alliance).where(Alliance.universe_id == u1.id, Alliance.deleted_at.is_(None))
        )
        alliances = result.unique().scalars().all()
        assert len(alliances) == 1
        assert alliances[0].name == "AlphaAlliance"

    # ── Universe metadata ─────────────────────────────────────────────────

    async def test_universe_slug_unique(self, db: AsyncSession):
        db.add(Universe(name="First", slug="duplicate-slug"))
        await db.flush()
        db.add(Universe(name="Second", slug="duplicate-slug"))
        with pytest.raises(Exception):
            await db.flush()

    async def test_null_universe_id_not_returned_in_scoped_query(self, db: AsyncSession):
        u1, _ = await self._make_universes(db)
        # Set without universe_id (legacy / unscoped)
        db.add(Set(name="Unscoped", type=SetType.ACTIVE, universe_id=None))
        await db.flush()

        result = await db.execute(
            select(Set).where(Set.universe_id == u1.id, Set.deleted_at.is_(None))
        )
        assert result.scalars().all() == []
