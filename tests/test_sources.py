"""Tests for Source CRUD and M2M links."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Incident,
    IncidentSource,
    IncidentType,
    LocationType,
    Member,
    MemberSource,
    MemberStatus,
    Source,
    SourceReliability,
)


class TestSourceCRUD:
    async def test_create_source(self, db: AsyncSession):
        source = Source(url="https://example.com/article", reliability=SourceReliability.HIGH)
        db.add(source)
        await db.flush()

        result = await db.execute(select(Source).where(Source.id == source.id))
        loaded = result.scalars().first()
        assert loaded is not None
        assert loaded.url == "https://example.com/article"
        assert loaded.reliability == SourceReliability.HIGH

    async def test_default_reliability_is_unverified(self, db: AsyncSession):
        source = Source(url="https://example.com/unknown")
        db.add(source)
        await db.flush()

        result = await db.execute(select(Source).where(Source.id == source.id))
        loaded = result.scalars().first()
        assert loaded.reliability == SourceReliability.UNVERIFIED

    async def test_soft_delete_source(self, db: AsyncSession):
        source = Source(url="https://example.com/to-delete", reliability=SourceReliability.LOW)
        db.add(source)
        await db.flush()

        assert source.deleted_at is None
        source.soft_delete()
        assert source.deleted_at is not None

    async def test_source_with_all_fields(self, db: AsyncSession):
        from datetime import date
        source = Source(
            url="https://news.example.com/article",
            title="Gang War Erupts",
            publication="City Times",
            accessed_at=date(2024, 6, 1),
            reliability=SourceReliability.MEDIUM,
            archive_url="https://web.archive.org/web/abc",
        )
        db.add(source)
        await db.flush()

        result = await db.execute(select(Source).where(Source.id == source.id))
        loaded = result.scalars().first()
        assert loaded.title == "Gang War Erupts"
        assert loaded.publication == "City Times"
        assert loaded.archive_url == "https://web.archive.org/web/abc"


class TestSourceMemberLink:
    async def test_link_member_to_source(self, db: AsyncSession):
        source = Source(url="https://example.com", reliability=SourceReliability.MEDIUM)
        member = Member(name="TestMember", status=MemberStatus.ALIVE)
        db.add_all([source, member])
        await db.flush()

        db.add(MemberSource(member_id=member.id, source_id=source.id))
        await db.flush()

        result = await db.execute(
            select(MemberSource).where(
                MemberSource.member_id == member.id,
                MemberSource.source_id == source.id,
            )
        )
        assert result.scalars().first() is not None

    async def test_member_source_unique_constraint(self, db: AsyncSession):
        source = Source(url="https://example.com/dupe", reliability=SourceReliability.LOW)
        member = Member(name="DupeMember", status=MemberStatus.ALIVE)
        db.add_all([source, member])
        await db.flush()

        db.add(MemberSource(member_id=member.id, source_id=source.id))
        await db.flush()

        from sqlalchemy.exc import IntegrityError
        db.add(MemberSource(member_id=member.id, source_id=source.id))
        with pytest.raises(IntegrityError):
            await db.flush()


class TestSourceIncidentLink:
    async def test_link_incident_to_source(self, db: AsyncSession):
        source = Source(url="https://example.com/incident", reliability=SourceReliability.HIGH)
        incident = Incident(
            incident_type=IncidentType.SHOOTING,
            location_type=LocationType.STREET,
            verified=False,
        )
        db.add_all([source, incident])
        await db.flush()

        db.add(IncidentSource(incident_id=incident.id, source_id=source.id))
        await db.flush()

        result = await db.execute(
            select(IncidentSource).where(
                IncidentSource.incident_id == incident.id,
                IncidentSource.source_id == source.id,
            )
        )
        assert result.scalars().first() is not None

    async def test_source_can_link_multiple_incidents(self, db: AsyncSession):
        source = Source(url="https://example.com/multi", reliability=SourceReliability.MEDIUM)
        i1 = Incident(incident_type=IncidentType.MURDER, location_type=LocationType.STREET, verified=False)
        i2 = Incident(incident_type=IncidentType.SHOOTING, location_type=LocationType.STREET, verified=False)
        db.add_all([source, i1, i2])
        await db.flush()

        db.add(IncidentSource(incident_id=i1.id, source_id=source.id))
        db.add(IncidentSource(incident_id=i2.id, source_id=source.id))
        await db.flush()

        result = await db.execute(
            select(IncidentSource).where(IncidentSource.source_id == source.id)
        )
        assert len(result.scalars().all()) == 2
