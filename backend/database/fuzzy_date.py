"""FuzzyDate — a JSONB-backed date type with variable precision.

Schema:
  { "year": 2019, "month": 3, "day": 15, "precision": "YMD", "approx": false, "circa_text": null }

precision values: "Y" | "YM" | "YMD" | "UNKNOWN"

A companion plain-Date column (`*_sortable`) stores the earliest-possible date
for ORDER BY.  Set both together when persisting:

    obj.birth_date = FuzzyDate(year=1990, month=6, precision="YM")
    obj.birth_date_sortable = obj.birth_date.to_sortable_date()
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

Precision = Literal["Y", "YM", "YMD", "UNKNOWN"]


class FuzzyDate(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    precision: Precision = "UNKNOWN"
    approx: bool = False
    circa_text: Optional[str] = None

    @classmethod
    def from_date(cls, d: date) -> "FuzzyDate":
        return cls(year=d.year, month=d.month, day=d.day, precision="YMD")

    def to_sortable_date(self) -> Optional[date]:
        """Earliest-possible date for ordering.

        precision Y  → Jan 1 of the year
        precision YM → 1st of the month
        precision YMD → exact date
        UNKNOWN / missing year → None
        """
        if self.precision == "UNKNOWN" or self.year is None:
            return None
        month = (self.month or 1) if self.precision in ("YM", "YMD") else 1
        day = (self.day or 1) if self.precision == "YMD" else 1
        return date(self.year, month, day)

    def display(self) -> str:
        if self.precision == "UNKNOWN" or self.year is None:
            return self.circa_text or "unknown"
        prefix = "circa " if self.approx else ""
        if self.precision == "Y":
            return f"{prefix}{self.year}"
        if self.precision == "YM":
            month_name = date(self.year, self.month, 1).strftime("%b")
            return f"{prefix}{month_name} {self.year}"
        # YMD
        d = date(self.year, self.month, self.day)
        return f"{prefix}{d.strftime('%b')} {d.day}, {d.year}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FuzzyDate):
            return self.model_dump() == other.model_dump()
        return NotImplemented


class FuzzyDateJSON(TypeDecorator):
    """SQLAlchemy type that stores FuzzyDate as JSON.

    Uses JSONB on PostgreSQL, JSON/TEXT on SQLite (transparent to the ORM).
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, FuzzyDate):
            return value.model_dump()
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return FuzzyDate(**value)
