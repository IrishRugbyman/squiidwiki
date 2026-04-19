"""Tests for the 5 core business-rule validators."""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    LocationType,
    Member,
    MemberStatus,
    RelationshipType,
    Set,
    SetRelationship,
    SetType,
)
from backend.exceptions import (
    LocationConstraintError,
    RelationshipCollisionWarning,
    TemporalIntegrityError,
    VitalStateError,
)
from backend.validators.business_rules import BusinessRuleValidator


# ─── Rule 1: Vital State Constraint ──────────────────────────────────────────


class TestVitalStateConstraint:
    """Deceased members cannot participate in events after their death date."""

    async def test_deceased_member_event_after_death_raises(self, deceased_member: Member):
        with pytest.raises(VitalStateError):
            BusinessRuleValidator.validate_vital_state(
                deceased_member, date(2021, 1, 1),
            )

    async def test_deceased_member_event_on_death_date_passes(self, deceased_member: Member):
        BusinessRuleValidator.validate_vital_state(
            deceased_member, deceased_member.death_date,
        )

    async def test_deceased_member_event_before_death_passes(self, deceased_member: Member):
        BusinessRuleValidator.validate_vital_state(
            deceased_member, date(2019, 12, 31),
        )

    async def test_alive_member_any_date_passes(self, alive_member: Member):
        BusinessRuleValidator.validate_vital_state(
            alive_member, date(2099, 12, 31),
        )

    async def test_none_event_date_passes(self, deceased_member: Member):
        BusinessRuleValidator.validate_vital_state(deceased_member, None)

    async def test_deceased_no_death_date_passes(self, db: AsyncSession, active_set: Set):
        m = Member(
            name="NoDeathDate",
            status=MemberStatus.DECEASED,
            set_id=active_set.id,
        )
        db.add(m)
        await db.flush()
        BusinessRuleValidator.validate_vital_state(m, date(2025, 1, 1))


# ─── Rule 2: Location Constraint ─────────────────────────────────────────────


class TestLocationConstraint:
    """Incarcerated members cannot participate in street events."""

    async def test_incarcerated_street_event_raises(self, incarcerated_member: Member):
        with pytest.raises(LocationConstraintError):
            BusinessRuleValidator.validate_location_constraint(
                incarcerated_member, LocationType.STREET,
            )

    async def test_incarcerated_facility_event_passes(self, incarcerated_member: Member):
        BusinessRuleValidator.validate_location_constraint(
            incarcerated_member, LocationType.FACILITY,
        )

    async def test_alive_street_event_passes(self, alive_member: Member):
        BusinessRuleValidator.validate_location_constraint(
            alive_member, LocationType.STREET,
        )

    async def test_alive_facility_event_passes(self, alive_member: Member):
        BusinessRuleValidator.validate_location_constraint(
            alive_member, LocationType.FACILITY,
        )

    async def test_string_location_type_works(self, incarcerated_member: Member):
        with pytest.raises(LocationConstraintError):
            BusinessRuleValidator.validate_location_constraint(
                incarcerated_member, "street",
            )

    async def test_deceased_street_passes(self, deceased_member: Member):
        BusinessRuleValidator.validate_location_constraint(
            deceased_member, LocationType.STREET,
        )


# ─── Rule 3: Temporal Integrity ──────────────────────────────────────────────


class TestTemporalIntegrity:
    """Events cannot predate gang founding; members cannot join before birth."""

    async def test_event_before_founding_raises(self, active_set: Set):
        with pytest.raises(TemporalIntegrityError):
            BusinessRuleValidator.validate_event_after_founding(
                active_set, date(2009, 12, 31),
            )

    async def test_event_on_founding_date_passes(self, active_set: Set):
        BusinessRuleValidator.validate_event_after_founding(
            active_set, active_set.founded_date,
        )

    async def test_event_after_founding_passes(self, active_set: Set):
        BusinessRuleValidator.validate_event_after_founding(
            active_set, date(2015, 6, 1),
        )

    async def test_event_none_date_passes(self, active_set: Set):
        BusinessRuleValidator.validate_event_after_founding(active_set, None)

    async def test_set_no_founded_date_passes(self, db: AsyncSession):
        s = Set(name="NoFoundDate", type=SetType.ACTIVE)
        db.add(s)
        await db.flush()
        BusinessRuleValidator.validate_event_after_founding(s, date(1900, 1, 1))

    async def test_join_before_birth_raises(self):
        with pytest.raises(TemporalIntegrityError):
            BusinessRuleValidator.validate_member_join_after_birth(
                birth_date=date(2000, 1, 1),
                joined_date=date(1999, 12, 31),
            )

    async def test_join_on_birth_passes(self):
        BusinessRuleValidator.validate_member_join_after_birth(
            birth_date=date(2000, 1, 1),
            joined_date=date(2000, 1, 1),
        )

    async def test_join_after_birth_passes(self):
        BusinessRuleValidator.validate_member_join_after_birth(
            birth_date=date(2000, 1, 1),
            joined_date=date(2015, 9, 1),
        )

    async def test_join_none_dates_pass(self):
        BusinessRuleValidator.validate_member_join_after_birth(None, None)
        BusinessRuleValidator.validate_member_join_after_birth(date(2000, 1, 1), None)
        BusinessRuleValidator.validate_member_join_after_birth(None, date(2015, 1, 1))

    async def test_death_before_birth_raises(self):
        with pytest.raises(TemporalIntegrityError):
            BusinessRuleValidator.validate_death_after_birth(
                birth_date=date(2000, 1, 1),
                death_date=date(1999, 6, 1),
            )

    async def test_death_after_birth_passes(self):
        BusinessRuleValidator.validate_death_after_birth(
            birth_date=date(1990, 1, 1),
            death_date=date(2020, 5, 10),
        )


# ─── Rule 4: Relationship Collision ──────────────────────────────────────────


class TestRelationshipCollision:
    """Allying with a rival of an existing ally should warn/block."""

    async def _make_sets(self, db: AsyncSession) -> tuple[Set, Set, Set]:
        a = Set(name="GangA", type=SetType.ACTIVE)
        b = Set(name="GangB", type=SetType.ACTIVE)
        c = Set(name="GangC", type=SetType.ACTIVE)
        db.add_all([a, b, c])
        await db.flush()
        return a, b, c

    async def test_collision_detected(self, db: AsyncSession):
        a, b, c = await self._make_sets(db)

        # A allies with C
        db.add(SetRelationship(
            set_a_id=a.id, set_b_id=c.id,
            relationship_type=RelationshipType.ALLY,
        ))
        # B is enemy of C
        db.add(SetRelationship(
            set_a_id=b.id, set_b_id=c.id,
            relationship_type=RelationshipType.ENEMY,
        ))
        await db.flush()

        # A tries to ally with B — B is rival of C who is A's ally
        with pytest.raises(RelationshipCollisionWarning):
            await BusinessRuleValidator.validate_no_relationship_collision(
                a.id, b.id, db,
            )

    async def test_collision_with_force_passes(self, db: AsyncSession):
        a, b, c = await self._make_sets(db)

        db.add(SetRelationship(
            set_a_id=a.id, set_b_id=c.id,
            relationship_type=RelationshipType.ALLY,
        ))
        db.add(SetRelationship(
            set_a_id=b.id, set_b_id=c.id,
            relationship_type=RelationshipType.ENEMY,
        ))
        await db.flush()

        await BusinessRuleValidator.validate_no_relationship_collision(
            a.id, b.id, db, force=True,
        )

    async def test_no_collision_passes(self, db: AsyncSession):
        a, b, c = await self._make_sets(db)

        db.add(SetRelationship(
            set_a_id=a.id, set_b_id=c.id,
            relationship_type=RelationshipType.ALLY,
        ))
        await db.flush()

        # B has no rivalry with C -> no collision
        await BusinessRuleValidator.validate_no_relationship_collision(a.id, b.id, db)

    async def test_no_allies_passes(self, db: AsyncSession):
        a, b, _c = await self._make_sets(db)
        await BusinessRuleValidator.validate_no_relationship_collision(a.id, b.id, db)

    async def test_ended_rivalry_ignored(self, db: AsyncSession):
        a, b, c = await self._make_sets(db)

        db.add(SetRelationship(
            set_a_id=a.id, set_b_id=c.id,
            relationship_type=RelationshipType.ALLY,
        ))
        db.add(SetRelationship(
            set_a_id=b.id, set_b_id=c.id,
            relationship_type=RelationshipType.ENEMY,
            ended_at=date(2020, 1, 1),
        ))
        await db.flush()

        await BusinessRuleValidator.validate_no_relationship_collision(a.id, b.id, db)


# ─── Rule 5: Soft Delete Behavior ────────────────────────────────────────────


class TestSoftDelete:
    """Soft-delete mixin behaviour on domain models."""

    async def test_soft_delete_sets_deleted_at(self, alive_member: Member):
        assert alive_member.deleted_at is None
        assert not alive_member.is_deleted
        alive_member.soft_delete()
        assert alive_member.deleted_at is not None
        assert alive_member.is_deleted

    async def test_restore_clears_deleted_at(self, alive_member: Member):
        alive_member.soft_delete()
        assert alive_member.is_deleted
        alive_member.restore()
        assert alive_member.deleted_at is None
        assert not alive_member.is_deleted

    async def test_set_soft_delete(self, active_set: Set):
        assert not active_set.is_deleted
        active_set.soft_delete()
        assert active_set.is_deleted
        active_set.restore()
        assert not active_set.is_deleted


# ─── Convenience: validate_event_participation ───────────────────────────────


class TestEventParticipationConvenience:
    """The combined validator runs rules 1-3 in one call."""

    async def test_deceased_after_death_raises(self, deceased_member: Member, active_set: Set):
        with pytest.raises(VitalStateError):
            BusinessRuleValidator.validate_event_participation(
                deceased_member,
                date(2021, 1, 1),
                LocationType.STREET,
                sets=[active_set],
            )

    async def test_incarcerated_street_raises(self, incarcerated_member: Member, active_set: Set):
        with pytest.raises(LocationConstraintError):
            BusinessRuleValidator.validate_event_participation(
                incarcerated_member,
                date(2023, 1, 1),
                LocationType.STREET,
                sets=[active_set],
            )

    async def test_event_before_founding_raises(self, alive_member: Member, active_set: Set):
        with pytest.raises(TemporalIntegrityError):
            BusinessRuleValidator.validate_event_participation(
                alive_member,
                date(2005, 1, 1),
                LocationType.STREET,
                sets=[active_set],
            )

    async def test_valid_participation_passes(self, alive_member: Member, active_set: Set):
        BusinessRuleValidator.validate_event_participation(
            alive_member,
            date(2023, 6, 15),
            LocationType.STREET,
            sets=[active_set],
        )
