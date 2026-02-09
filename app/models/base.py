"""Base model and FuzzyDate composite type."""
from typing import Optional
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.hybrid import Comparator
import calendar


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class FuzzyDate:
    """
    A date with flexible precision: year-only, year-month, or full date.
    
    Rules:
    - year is required if any date info exists
    - month can only be set if year is set
    - day can only be set if month is set
    """
    
    def __init__(self, year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None):
        """Initialize FuzzyDate with validation."""
        if month is not None and year is None:
            raise ValueError("Cannot set month without year")
        if day is not None and month is None:
            raise ValueError("Cannot set day without month")
        
        if month is not None and not (1 <= month <= 12):
            raise ValueError(f"Month must be between 1 and 12, got {month}")
        
        if day is not None:
            if month is None:
                raise ValueError("Cannot validate day without month")
            max_day = calendar.monthrange(year or 2000, month)[1]
            if not (1 <= day <= max_day):
                raise ValueError(f"Day must be between 1 and {max_day} for month {month}, got {day}")
        
        self.year = year
        self.month = month
        self.day = day
    
    def __composite_values__(self):
        """Return values for SQLAlchemy composite."""
        return self.year, self.month, self.day
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.year is None:
            return "Unknown"
        if self.month is None:
            return str(self.year)
        
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_str = month_names[self.month - 1]
        
        if self.day is None:
            return f"{month_str} {self.year}"
        return f"{month_str} {self.day}, {self.year}"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"FuzzyDate(year={self.year}, month={self.month}, day={self.day})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, FuzzyDate):
            return False
        return (self.year, self.month, self.day) == (other.year, other.month, other.day)
    
    def __lt__(self, other) -> bool:
        """Less than comparison at lowest common precision."""
        if not isinstance(other, FuzzyDate):
            return NotImplemented
        
        if self.year is None or other.year is None:
            return False
        
        if self.year != other.year:
            return self.year < other.year
        
        # Years are equal, check month if both have it
        if self.month is None or other.month is None:
            return False  # Can't determine at year-only precision
        
        if self.month != other.month:
            return self.month < other.month
        
        # Months are equal, check day if both have it
        if self.day is None or other.day is None:
            return False  # Can't determine at month precision
        
        return self.day < other.day
    
    def __le__(self, other) -> bool:
        """Less than or equal."""
        return self == other or self < other
    
    def __gt__(self, other) -> bool:
        """Greater than."""
        if not isinstance(other, FuzzyDate):
            return NotImplemented
        return other < self
    
    def __ge__(self, other) -> bool:
        """Greater than or equal."""
        return self == other or self > other
    
    @property
    def is_empty(self) -> bool:
        """Check if date is completely empty."""
        return self.year is None
