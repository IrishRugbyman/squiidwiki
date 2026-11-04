import calendar
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
        """The parts must make a date on the calendar, and match the precision.

        Raises ValueError (a 422 in a request), never `assert`, which
        `python -O` strips. The precision says which parts are known: Y is a
        year alone, YM a year and month, YMD all three, and none of them may
        carry a part finer than it claims, since display and the sortable
        date read the precision and would silently drop it. UNKNOWN claims
        nothing, so it may keep whatever parts are known (a year, or a day
        and month with no year), as long as they could be a real date.
        """
        year, month, day, precision = self.year, self.month, self.day, self.precision
        if year is not None and not 1 <= year <= 9999:
            raise ValueError(f"year {year} is out of range (1-9999)")
        if month is not None and not 1 <= month <= 12:
            raise ValueError(f"month {month} is not a month (1-12)")
        if day is not None:
            if month is None:
                raise ValueError("a day needs its month")
            # With no year, 29 February may be right: check against a leap year.
            last = calendar.monthrange(year if year is not None else 2000, month)[1]
            if not 1 <= day <= last:
                when = f"{year}-{month:02d}" if year is not None else f"month {month}"
                raise ValueError(f"day {day} does not exist in {when} (1-{last})")
        needs = {
            DatePrecision.YMD: ("year", "month", "day"),
            DatePrecision.YM: ("year", "month"),
            DatePrecision.Y: ("year",),
        }.get(precision)
        if needs is not None:
            missing = [f for f in needs if getattr(self, f) is None]
            if missing:
                raise ValueError(f"precision {precision.value} requires {', '.join(missing)}")
            extra = [f for f in ("month", "day") if f not in needs and getattr(self, f) is not None]
            if extra:
                raise ValueError(
                    f"precision {precision.value} cannot carry {' or '.join(extra)}; "
                    "use a finer precision or leave it out"
                )
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
