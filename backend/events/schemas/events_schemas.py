from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date as datetype
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Enum for event types"""
    MURDER = "murder"
    SHOOTING = "shooting"
    ASSIST = "assist"


class DatePrecision(str, Enum):
    """Enum for date precision types"""
    EXACT = "exact"
    YEAR = "year"
    KEEP = "keep"  # Special case for murders to keep victim's death date


class EventBase(BaseModel):
    """Base schema for all events"""
    shooter_id: int
    victim_id: int
    date: Optional[datetype] = None
    date_approx: Optional[str] = "unknown"


class EventCreate(BaseModel):
    """Schema for creating an event"""
    shooter_id: int
    victim_id: int
    date_precision: DatePrecision
    date_exact: Optional[str] = None
    date_year: Optional[str] = None
    update_victim_death: Optional[bool] = False


class EventUpdate(BaseModel):
    """Schema for updating an event"""
    shooter_id: Optional[int] = None
    date_precision: Optional[DatePrecision] = None
    date_exact: Optional[str] = None
    date_year: Optional[str] = None
    update_victim_death: Optional[bool] = False


class EventMemberInfo(BaseModel):
    """Schema for member information within an event"""
    id: int
    name: str
    set_name: Optional[str] = None
    status: str
    
    class Config:
        orm_mode = True


class EventResponse(EventBase):
    """Schema for event responses"""
    id: int
    shooter: EventMemberInfo
    victim: EventMemberInfo
    
    class Config:
        orm_mode = True


class MurderResponse(EventResponse):
    """Schema specific to murder events"""
    # Murder-specific fields could be added here
    pass


class ShootingResponse(EventResponse):
    """Schema specific to shooting events"""
    # Shooting-specific fields could be added here
    pass


class AssistResponse(EventResponse):
    """Schema specific to assist events"""
    # Assist-specific fields could be added here
    pass 