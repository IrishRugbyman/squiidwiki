"""Tests for FuzzyDate type: round-trip, precision, sortable, display."""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.fuzzy_date import FuzzyDate
from backend.database.models import Member, MemberStatus, Set, SetType


# ─── FuzzyDate value object ───────────────────────────────────────────────────


class TestFuzzyDateSortable:
    def test_ymd_sortable(self):
        fd = FuzzyDate(year=2020, month=5, day=15, precision="YMD")
        assert fd.to_sortable_date() == date(2020, 5, 15)

    def test_ym_sortable_first_of_month(self):
        fd = FuzzyDate(year=2020, month=5, precision="YM")
        assert fd.to_sortable_date() == date(2020, 5, 1)

    def test_y_sortable_jan_first(self):
        fd = FuzzyDate(year=2020, precision="Y")
        assert fd.to_sortable_date() == date(2020, 1, 1)

    def test_unknown_sortable_is_none(self):
        fd = FuzzyDate(precision="UNKNOWN")
        assert fd.to_sortable_date() is None

    def test_missing_year_sortable_is_none(self):
        fd = FuzzyDate(year=None, precision="UNKNOWN")
        assert fd.to_sortable_date() is None

    def test_from_date_roundtrip(self):
        d = date(1998, 7, 4)
        fd = FuzzyDate.from_date(d)
        assert fd.precision == "YMD"
        assert fd.to_sortable_date() == d


class TestFuzzyDateDisplay:
    def test_ymd_display(self):
        fd = FuzzyDate(year=2019, month=3, day=15, precision="YMD")
        assert fd.display() == "Mar 15, 2019"

    def test_ym_display(self):
        fd = FuzzyDate(year=2019, month=3, precision="YM")
        assert fd.display() == "Mar 2019"

    def test_y_display(self):
        fd = FuzzyDate(year=2019, precision="Y")
        assert fd.display() == "2019"

    def test_unknown_display(self):
        fd = FuzzyDate(precision="UNKNOWN")
        assert fd.display() == "unknown"

    def test_approx_prefix(self):
        fd = FuzzyDate(year=2018, precision="Y", approx=True)
        assert fd.display() == "circa 2018"

    def test_circa_text_overrides_unknown(self):
        fd = FuzzyDate(precision="UNKNOWN", circa_text="late 90s")
        assert fd.display() == "late 90s"

    def test_approx_ymd(self):
        fd = FuzzyDate(year=2019, month=3, day=15, precision="YMD", approx=True)
        assert fd.display().startswith("circa ")


class TestFuzzyDateEquality:
    def test_equal_same_values(self):
        a = FuzzyDate(year=2020, month=1, day=1, precision="YMD")
        b = FuzzyDate(year=2020, month=1, day=1, precision="YMD")
        assert a == b

    def test_not_equal_different_precision(self):
        a = FuzzyDate(year=2020, month=1, precision="YM")
        b = FuzzyDate(year=2020, precision="Y")
        assert a != b


# ─── Round-trip through SQLite (ORM) ─────────────────────────────────────────


class TestFuzzyDatePersistence:
    """Verify FuzzyDate stores and retrieves correctly via the ORM."""

    async def test_set_founded_date_roundtrip(self, db: AsyncSession):
        fd = FuzzyDate(year=2005, month=6, precision="YM")
        s = Set(
            name="RoundTripSet",
            type=SetType.ACTIVE,
            founded_date=fd,
            founded_date_sortable=fd.to_sortable_date(),
        )
        db.add(s)
        await db.flush()

        result = await db.execute(select(Set).where(Set.id == s.id))
        loaded = result.scalars().first()
        assert loaded.founded_date == fd
        assert loaded.founded_date_sortable == date(2005, 6, 1)

    async def test_member_birth_death_roundtrip(self, db: AsyncSession):
        bd = FuzzyDate(year=1990, precision="Y")
        dd = FuzzyDate(year=2020, month=5, day=10, precision="YMD")
        m = Member(
            name="TestMember",
            status=MemberStatus.DECEASED,
            birth_date=bd,
            birth_date_sortable=bd.to_sortable_date(),
            death_date=dd,
            death_date_sortable=dd.to_sortable_date(),
        )
        db.add(m)
        await db.flush()

        result = await db.execute(select(Member).where(Member.id == m.id))
        loaded = result.scalars().first()
        assert loaded.birth_date == bd
        assert loaded.birth_date_sortable == date(1990, 1, 1)
        assert loaded.death_date == dd
        assert loaded.death_date_sortable == date(2020, 5, 10)

    async def test_null_fuzzy_date_roundtrip(self, db: AsyncSession):
        m = Member(name="NoDates", status=MemberStatus.ALIVE)
        db.add(m)
        await db.flush()

        result = await db.execute(select(Member).where(Member.id == m.id))
        loaded = result.scalars().first()
        assert loaded.birth_date is None
        assert loaded.birth_date_sortable is None

    async def test_unknown_precision_roundtrip(self, db: AsyncSession):
        fd = FuzzyDate(precision="UNKNOWN")
        m = Member(
            name="UnknownDOB",
            status=MemberStatus.ALIVE,
            birth_date=fd,
            birth_date_sortable=fd.to_sortable_date(),
        )
        db.add(m)
        await db.flush()

        result = await db.execute(select(Member).where(Member.id == m.id))
        loaded = result.scalars().first()
        assert loaded.birth_date.precision == "UNKNOWN"
        assert loaded.birth_date_sortable is None
