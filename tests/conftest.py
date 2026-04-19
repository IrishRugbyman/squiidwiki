"""Shared fixtures for the SquiidWiki test suite."""
from __future__ import annotations

from datetime import date

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.base_class import Base
from backend.database.models import (
    Alliance,
    AllianceSetMap,
    DatePrecision,
    Event,
    EventParticipant,
    EventType,
    LocationType,
    Member,
    MemberStatus,
    ParticipantRole,
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
    s = Set(name="TestSet", type=SetType.ACTIVE, founded_date=date(2010, 1, 1))
    db.add(s)
    await db.flush()
    return s


@pytest_asyncio.fixture()
async def alive_member(db: AsyncSession, active_set: Set) -> Member:
    m = Member(
        name="AliveMember",
        status=MemberStatus.ALIVE,
        set_id=active_set.id,
        birth_date=date(1995, 6, 15),
    )
    db.add(m)
    await db.flush()
    return m


@pytest_asyncio.fixture()
async def deceased_member(db: AsyncSession, active_set: Set) -> Member:
    m = Member(
        name="DeceasedMember",
        status=MemberStatus.DECEASED,
        set_id=active_set.id,
        birth_date=date(1990, 1, 1),
        death_date=date(2020, 5, 10),
    )
    db.add(m)
    await db.flush()
    return m


@pytest_asyncio.fixture()
async def incarcerated_member(db: AsyncSession, active_set: Set) -> Member:
    m = Member(
        name="JailedMember",
        status=MemberStatus.INCARCERATED,
        set_id=active_set.id,
        birth_date=date(1992, 3, 20),
    )
    db.add(m)
    await db.flush()
    return m
