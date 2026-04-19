import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.core.enums import DatePrecision


class FuzzyDate(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    precision: DatePrecision = DatePrecision.UNKNOWN
    approx: bool = False
    circa_text: Optional[str] = None

    @model_validator(mode="after")
    def validate_fields(self) -> "FuzzyDate":
        if self.precision == DatePrecision.YMD:
            assert self.year and self.month and self.day, "YMD requires year, month, day"
        elif self.precision == DatePrecision.YM:
            assert self.year and self.month, "YM requires year and month"
        elif self.precision == DatePrecision.Y:
            assert self.year, "Y requires year"
        return self

    def to_sortable_date(self) -> Optional[datetime.date]:
        """Earliest-possible date for ordering; None when precision is UNKNOWN."""
        if self.precision == DatePrecision.UNKNOWN or self.year is None:
            return None
        return datetime.date(self.year, self.month or 1, self.day or 1)

    def display(self) -> str:
        if self.circa_text:
            return self.circa_text
        prefix = "circa " if self.approx else ""
        if self.precision == DatePrecision.UNKNOWN or self.year is None:
            return "unknown"
        if self.precision == DatePrecision.Y:
            return f"{prefix}{self.year}"
        if self.precision == DatePrecision.YM:
            dt = datetime.date(self.year, self.month, 1)
            return f"{prefix}{dt.strftime('%b')} {self.year}"
        dt = datetime.date(self.year, self.month, self.day)
        return f"{prefix}{dt.strftime('%b')} {dt.day}, {self.year}"

    @classmethod
    def unknown(cls) -> "FuzzyDate":
        return cls(precision=DatePrecision.UNKNOWN)

    @classmethod
    def year_only(cls, year: int, approx: bool = False) -> "FuzzyDate":
        return cls(year=year, precision=DatePrecision.Y, approx=approx)
