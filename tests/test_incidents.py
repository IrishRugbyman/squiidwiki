"""Tests for Incident CRUD and IncidentParticipant join."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Incident,
    IncidentOutcome,
    IncidentParticipant,
    IncidentRole,
    IncidentType,
    LocationType,
    Member,
    MemberStatus,
    Set,
    SetType,
)


class TestIncidentCRUD:
    async def test_create_incident(self, db: AsyncSession):
        incident = Incident(
            incident_type=IncidentType.SHOOTING,
            location_type=LocationType.STREET,
            verified=False,
        )
        db.add(incident)
        await db.flush()

        result = await db.execute(select(Incident).where(Incident.id == incident.id))
        loaded = result.scalars().first()
        assert loaded is not None
        assert loaded.incident_type == IncidentType.SHOOTING
        assert loaded.location_type == LocationType.STREET
        assert loaded.verified is False

    async def test_create_murder_incident(self, db: AsyncSession):
        incident = Incident(
            incident_type=IncidentType.MURDER,
            location_type=LocationType.STREET,
            verified=True,
            narrative="A fatal incident occurred.",
        )
        db.add(incident)
        await db.flush()

        result = await db.execute(select(Incident).where(Incident.id == incident.id))
        loaded = result.scalars().first()
        assert loaded.incident_type == IncidentType.MURDER
        assert loaded.verified is True
        assert loaded.narrative == "A fatal incident occurred."

    async def test_soft_delete_incident(self, db: AsyncSession):
        incident = Incident(
            incident_type=IncidentType.SHOOTING,
            location_type=LocationType.STREET,
            verified=False,
        )
        db.add(incident)
        await db.flush()

        assert incident.deleted_at is None
        incident.soft_delete()
        assert incident.deleted_at is not None


class TestIncidentParticipant:
    async def _make_incident_and_member(self, db: AsyncSession):
        incident = Incident(
            incident_type=IncidentType.SHOOTING,
            location_type=LocationType.STREET,
            verified=False,
        )
        member = Member(name="TestMember", status=MemberStatus.ALIVE)
        db.add_all([incident, member])
        await db.flush()
        return incident, member

    async def test_add_participant(self, db: AsyncSession):
        incident, member = await self._make_incident_and_member(db)

        participant = IncidentParticipant(
            incident_id=incident.id,
            member_id=member.id,
            role=IncidentRole.SHOOTER,
            outcome=IncidentOutcome.UNHARMED,
        )
        db.add(participant)
        await db.flush()

        result = await db.execute(
            select(Incident)
            .options(selectinload(Incident.participants))
            .where(Incident.id == incident.id)
        )
        loaded = result.scalars().first()
        assert len(loaded.participants) == 1
        assert loaded.participants[0].role == IncidentRole.SHOOTER
        assert loaded.participants[0].outcome == IncidentOutcome.UNHARMED

    async def test_orthogonal_role_and_outcome(self, db: AsyncSession):
        incident, member = await self._make_incident_and_member(db)

        # Victim who survived
        participant = IncidentParticipant(
            incident_id=incident.id,
            member_id=member.id,
            role=IncidentRole.VICTIM,
            outcome=IncidentOutcome.INJURED,
        )
        db.add(participant)
        await db.flush()

        result = await db.execute(
            select(IncidentParticipant).where(IncidentParticipant.id == participant.id)
        )
        loaded = result.scalars().first()
        assert loaded.role == IncidentRole.VICTIM
        assert loaded.outcome == IncidentOutcome.INJURED

    async def test_default_outcome_is_unknown(self, db: AsyncSession):
        incident, member = await self._make_incident_and_member(db)

        participant = IncidentParticipant(
            incident_id=incident.id,
            member_id=member.id,
            role=IncidentRole.BYSTANDER,
        )
        db.add(participant)
        await db.flush()

        result = await db.execute(
            select(IncidentParticipant).where(IncidentParticipant.id == participant.id)
        )
        loaded = result.scalars().first()
        assert loaded.outcome == IncidentOutcome.UNKNOWN

    async def test_cascade_delete_participants(self, db: AsyncSession):
        incident, member = await self._make_incident_and_member(db)

        db.add(IncidentParticipant(
            incident_id=incident.id,
            member_id=member.id,
            role=IncidentRole.SHOOTER,
            outcome=IncidentOutcome.UNHARMED,
        ))
        await db.flush()

        await db.delete(incident)
        await db.flush()

        result = await db.execute(
            select(IncidentParticipant).where(IncidentParticipant.incident_id == incident.id)
        )
        assert result.scalars().first() is None

    async def test_multiple_participants_different_roles(self, db: AsyncSession):
        incident = Incident(
            incident_type=IncidentType.MURDER,
            location_type=LocationType.STREET,
            verified=False,
        )
        shooter = Member(name="Shooter", status=MemberStatus.ALIVE)
        victim = Member(name="Victim", status=MemberStatus.DECEASED)
        db.add_all([incident, shooter, victim])
        await db.flush()

        db.add(IncidentParticipant(
            incident_id=incident.id,
            member_id=shooter.id,
            role=IncidentRole.SHOOTER,
            outcome=IncidentOutcome.UNHARMED,
        ))
        db.add(IncidentParticipant(
            incident_id=incident.id,
            member_id=victim.id,
            role=IncidentRole.VICTIM,
            outcome=IncidentOutcome.KILLED,
        ))
        await db.flush()

        result = await db.execute(
            select(Incident)
            .options(selectinload(Incident.participants))
            .where(Incident.id == incident.id)
        )
        loaded = result.scalars().first()
        assert len(loaded.participants) == 2

        roles = {p.role for p in loaded.participants}
        assert IncidentRole.SHOOTER in roles
        assert IncidentRole.VICTIM in roles
