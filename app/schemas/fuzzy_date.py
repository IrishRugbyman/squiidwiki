"""FuzzyDate schema."""
from pydantic import BaseModel, field_validator
from typing import Optional
import calendar


class FuzzyDateSchema(BaseModel):
    """Schema for FuzzyDate with validation."""
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    
    @field_validator('month')
    @classmethod
    def validate_month(cls, v, info):
        """Validate month."""
        if v is not None:
            if info.data.get('year') is None:
                raise ValueError("Cannot set month without year")
            if not (1 <= v <= 12):
                raise ValueError("Month must be between 1 and 12")
        return v
    
    @field_validator('day')
    @classmethod
    def validate_day(cls, v, info):
        """Validate day."""
        if v is not None:
            month = info.data.get('month')
            if month is None:
                raise ValueError("Cannot set day without month")
            year = info.data.get('year', 2000)
            max_day = calendar.monthrange(year, month)[1]
            if not (1 <= v <= max_day):
                raise ValueError(f"Day must be between 1 and {max_day} for month {month}")
        return v
    
    def to_string(self) -> str:
        """Convert to human-readable string."""
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
    
    class Config:
        from_attributes = True
