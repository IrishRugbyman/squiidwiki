"""Shared fixtures for the SquiidWiki test suite."""
from __future__ import annotations

from datetime import date

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.base_class import Base
from backend.database.fuzzy_date import FuzzyDate
from backend.database.models import (
    Alliance,
    AllianceSetMap,
    DatePrecision,
    Incident,
    IncidentParticipant,
    IncidentRole,
    IncidentType,
    LocationType,
    Member,
    MemberStatus,
    RelationshipType,
    Set,
    SetRelationship,
    SetType,
    Universe,
)


@pytest_asyncio.fixture()
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def db(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture()
async def universe(db: AsyncSession) -> Universe:
    u = Universe(name="Test Universe", slug="test-universe")
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture()
async def active_set(db: AsyncSession) -> Set:
    fd = FuzzyDate(year=2010, month=1, day=1, precision="YMD")
    s = Set(
        name="TestSet",
        type=SetType.ACTIVE,
        founded_date=fd,
        founded_date_sortable=fd.to_sortable_date(),
    )
    db.add(s)
    await db.flush()
    return s


@pytest_asyncio.fixture()
async def alive_member(db: AsyncSession, active_set: Set) -> Member:
    bd = FuzzyDate(year=1995, month=6, day=15, precision="YMD")
    m = Member(
        name="AliveMember",
        status=MemberStatus.ALIVE,
        set_id=active_set.id,
        birth_date=bd,
        birth_date_sortable=bd.to_sortable_date(),
    )
    db.add(m)
    await db.flush()
    return m


@pytest_asyncio.fixture()
async def deceased_member(db: AsyncSession, active_set: Set) -> Member:
    bd = FuzzyDate(year=1990, month=1, day=1, precision="YMD")
    dd = FuzzyDate(year=2020, month=5, day=10, precision="YMD")
    m = Member(
        name="DeceasedMember",
        status=MemberStatus.DECEASED,
        set_id=active_set.id,
        birth_date=bd,
        birth_date_sortable=bd.to_sortable_date(),
        death_date=dd,
        death_date_sortable=dd.to_sortable_date(),
    )
    db.add(m)
    await db.flush()
    return m


@pytest_asyncio.fixture()
async def incarcerated_member(db: AsyncSession, active_set: Set) -> Member:
    bd = FuzzyDate(year=1992, month=3, day=20, precision="YMD")
    m = Member(
        name="JailedMember",
        status=MemberStatus.INCARCERATED,
        set_id=active_set.id,
        birth_date=bd,
        birth_date_sortable=bd.to_sortable_date(),
    )
    db.add(m)
    await db.flush()
    return m
