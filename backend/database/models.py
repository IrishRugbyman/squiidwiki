from pydantic import BaseModel
from typing import Optional
from datetime import date
from backend.database.enums import eStatus, eSetType

class SetBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: eSetType = eSetType.ACTIVE  # Default to ACTIVE

class SetCreate(SetBase):
    pass

class Set(SetBase):
    id: int

    class Config:
        from_attributes = True

class SetAlliesMap(BaseModel):
    set_id: int
    ally_id: int

    class Config:
        from_attributes = True

class SetEnemiesMap(BaseModel):
    set_id: int
    enemy_id: int

    class Config:
        from_attributes = True

class AllianceBase(BaseModel):
    name: str
    description: Optional[str] = None

class AllianceCreate(AllianceBase):
    pass

class Alliance(AllianceBase):
    id: int

    class Config:
        from_attributes = True

class AllianceMemberMap(BaseModel):
    alliance_id: int
    set_id: int
    role: Optional[str] = None
    join_date: Optional[date] = None

    class Config:
        from_attributes = True

class MemberBase(BaseModel):
    name: str
    status: eStatus
    release_date: Optional[date] = None  # Only if status is "locked_up"
    date_of_death: Optional[date] = None  # Only if status is "dead"
    set_id: int

class MemberCreate(MemberBase):
    pass

class Member(MemberBase):
    id: int

    class Config:
        from_attributes = True

class ShootingBase(BaseModel):
    shooter_id: int
    victim_id: int
    date: date

class ShootingCreate(ShootingBase):
    pass

class Shooting(ShootingBase):
    id: int

    class Config:
        from_attributes = True

class MurderBase(BaseModel):
    shooter_id: int
    victim_id: int
    date: date

class MurderCreate(MurderBase):
    pass

class Murder(MurderBase):
    id: int

    class Config:
        from_attributes = True

class AssistBase(BaseModel):
    shooter_id: int
    victim_id: int
    date: date

class AssistCreate(AssistBase):
    pass

class Assist(AssistBase):
    id: int

    class Config:
        from_attributes = True