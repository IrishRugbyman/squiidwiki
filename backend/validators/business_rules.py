"""
Central business-rule validator for SquiidWiki.

Every rule is a ``@staticmethod`` so validators can be called without
instantiation from any service.  Each method raises a specific exception
subclass from ``backend.exceptions`` when the constraint is violated.
"""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    EventType,
    LocationType,
    MemberStatus,
    RelationshipType,
    SetRelationship,
)
from backend.exceptions import (
    LocationConstraintError,
    RelationshipCollisionWarning,
    TemporalIntegrityError,
    VitalStateError,
)

if TYPE_CHECKING:
    from backend.database.models import Event, Member, Set


class BusinessRuleValidator:
    """Stateless collection of domain integrity checks."""

    # ------------------------------------------------------------------
    # Rule 1 — Vital-state constraint
    # ------------------------------------------------------------------
    @staticmethod
    def validate_vital_state(member: Member, event_date: date | None) -> None:
        """A deceased member cannot participate in events after death."""
        if (
            member.status == MemberStatus.DECEASED
            and member.death_date is not None
            and event_date is not None
            and event_date > member.death_date
        ):
            raise VitalStateError(
                f"Member '{member.name}' died on {member.death_date}; "
                f"cannot participate in an event dated {event_date}",
            )

    # ------------------------------------------------------------------
    # Rule 2 — Location constraint
    # ------------------------------------------------------------------
    @staticmethod
    def validate_location_constraint(
        member: Member,
        location_type: LocationType | str,
    ) -> None:
        """An incarcerated member can only appear in facility events."""
        if isinstance(location_type, str):
            location_type = LocationType(location_type)

        if (
            member.status == MemberStatus.INCARCERATED
            and location_type == LocationType.STREET
        ):
            raise LocationConstraintError(
                f"Member '{member.name}' is incarcerated and cannot "
                f"participate in a street event",
            )

    # ------------------------------------------------------------------
    # Rule 3 — Temporal integrity
    # ------------------------------------------------------------------
    @staticmethod
    def validate_event_after_founding(
        set_: Set,
        event_date: date | None,
    ) -> None:
        """An event involving a gang cannot predate its founding."""
        if (
            set_.founded_date is not None
            and event_date is not None
            and event_date < set_.founded_date
        ):
            raise TemporalIntegrityError(
                f"Event date {event_date} predates the founding of "
                f"'{set_.name}' ({set_.founded_date})",
            )

    @staticmethod
    def validate_member_join_after_birth(
        birth_date: date | None,
        joined_date: date | None,
    ) -> None:
        """A member cannot join a set before their birth date."""
        if (
            birth_date is not None
            and joined_date is not None
            and joined_date < birth_date
        ):
            raise TemporalIntegrityError(
                f"Join date {joined_date} is before birth date {birth_date}",
            )

    @staticmethod
    def validate_death_after_birth(
        birth_date: date | None,
        death_date: date | None,
    ) -> None:
        """Death date must come after birth date."""
        if (
            birth_date is not None
            and death_date is not None
            and death_date < birth_date
        ):
            raise TemporalIntegrityError(
                f"Death date {death_date} is before birth date {birth_date}",
            )

    # ------------------------------------------------------------------
    # Rule 4 — Relationship collision detection
    # ------------------------------------------------------------------
    @staticmethod
    async def validate_no_relationship_collision(
        set_a_id: int,
        set_b_id: int,
        db: AsyncSession,
        *,
        force: bool = False,
    ) -> None:
        """
        When Gang A allies with Gang B, check that Gang B is not in an
        active rivalry with any of Gang A's current allies.

        If ``force`` is True the check still runs but silently passes
        (the caller already acknowledged the conflict).
        """
        result = await db.execute(
            select(SetRelationship).where(
                SetRelationship.relationship_type == RelationshipType.ALLY,
                SetRelationship.ended_at.is_(None),
                SetRelationship.deleted_at.is_(None),
                (SetRelationship.set_a_id == set_a_id)
                | (SetRelationship.set_b_id == set_a_id),
            )
        )
        allies_of_a = result.scalars().all()

        ally_ids: set[int] = set()
        for rel in allies_of_a:
            ally_ids.add(rel.set_a_id if rel.set_b_id == set_a_id else rel.set_b_id)

        if not ally_ids:
            return

        conflicts_result = await db.execute(
            select(SetRelationship).where(
                SetRelationship.relationship_type == RelationshipType.ENEMY,
                SetRelationship.ended_at.is_(None),
                SetRelationship.deleted_at.is_(None),
                (
                    (SetRelationship.set_a_id == set_b_id)
                    & (SetRelationship.set_b_id.in_(ally_ids))
                )
                | (
                    (SetRelationship.set_b_id == set_b_id)
                    & (SetRelationship.set_a_id.in_(ally_ids))
                ),
            )
        )
        conflicts = conflicts_result.scalars().all()

        if conflicts and not force:
            conflicting = set()
            for c in conflicts:
                conflicting.add(c.set_a_id if c.set_b_id == set_b_id else c.set_b_id)
            raise RelationshipCollisionWarning(
                f"Set {set_b_id} has active rivalries with your allies: "
                f"{sorted(conflicting)}",
                conflicting_sets=[str(s) for s in sorted(conflicting)],
            )

    # ------------------------------------------------------------------
    # Convenience: run all relevant checks for event participation
    # ------------------------------------------------------------------
    @classmethod
    def validate_event_participation(
        cls,
        member: Member,
        event_date: date | None,
        location_type: LocationType | str,
        sets: list[Set] | None = None,
    ) -> None:
        """Run rules 1-3 in one call for adding a participant to an event."""
        cls.validate_vital_state(member, event_date)
        cls.validate_location_constraint(member, location_type)

        if sets:
            for s in sets:
                cls.validate_event_after_founding(s, event_date)
