import datetime

import pytest

from app.core.fuzzy_date import FuzzyDate
from app.core.enums import DatePrecision


def test_year_only_display():
    d = FuzzyDate.year_only(2019)
    assert d.display() == "2019"


def test_year_only_approx():
    d = FuzzyDate.year_only(2018, approx=True)
    assert d.display() == "circa 2018"


def test_ym_display():
    d = FuzzyDate(year=2019, month=3, precision=DatePrecision.YM)
    assert d.display() == "Mar 2019"


def test_ymd_display():
    d = FuzzyDate(year=2021, month=6, day=4, precision=DatePrecision.YMD)
    assert d.display() == "Jun 4, 2021"


def test_unknown_display():
    d = FuzzyDate.unknown()
    assert d.display() == "unknown"


def test_circa_text_override():
    d = FuzzyDate(year=2019, precision=DatePrecision.Y, approx=True, circa_text="early 2019")
    assert d.display() == "early 2019"


def test_sortable_date_year_only():
    d = FuzzyDate.year_only(2019)
    assert d.to_sortable_date() == datetime.date(2019, 1, 1)


def test_sortable_date_ym():
    d = FuzzyDate(year=2019, month=3, precision=DatePrecision.YM)
    assert d.to_sortable_date() == datetime.date(2019, 3, 1)


def test_sortable_date_unknown():
    assert FuzzyDate.unknown().to_sortable_date() is None


def test_invalid_ymd_missing_day():
    with pytest.raises(Exception):
        FuzzyDate(year=2021, month=6, precision=DatePrecision.YMD)


def test_roundtrip_json():
    d = FuzzyDate(year=2023, month=8, precision=DatePrecision.YM, approx=True)
    dumped = d.model_dump()
    restored = FuzzyDate(**dumped)
    assert restored == d
