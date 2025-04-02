from pydantic import BaseModel
from typing import Optional
from datetime import date
from backend.database.enums import eStatus, eSetType

# --------------------------
# Set Models
# --------------------------

class SetBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: eSetType = eSetType.ACTIVE  # Default to ACTIVE
    emoji: Optional[str] = None  # Optional emoji representing the set

class SetCreate(SetBase):
    pass

class Set(SetBase):
    id: int

    class Config:
        from_attributes = True

# Relationships between Sets
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

# --------------------------
# Alliance Models
# --------------------------

class AllianceBase(BaseModel):
    name: str
    description: Optional[str] = None

class AllianceCreate(AllianceBase):
    status: Optional[str] = "active"
    pass

class Alliance(AllianceBase):
    id: int

    class Config:
        from_attributes = True

# Relationship between Alliances and Sets
class AllianceMemberMap(BaseModel):
    alliance_id: int
    set_id: int
    role: Optional[str] = None
    join_date: Optional[date] = None

    class Config:
        from_attributes = True

# Option model for dropdowns or simple list retrieval
class AllianceOption(BaseModel):
    id: int
    name: str

# --------------------------
# Member Models
# --------------------------

class MemberBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: eStatus
    release_date: Optional[date] = None  # Only if status is "locked_up"
    release_date_approx: Optional[str] = None  # Approximate release date (e.g., "2023" or "life")
    death_date: Optional[date] = None  # Only if status is "dead"
    death_date_approx: Optional[str] = None  # Approximate date of death (e.g., "2023")
    set_id: Optional[int] = None  # Optional set reference
    alliance_id: Optional[int] = None  # Optional alliance reference

class MemberCreate(MemberBase):
    pass

class Member(MemberBase):
    id: int

    class Config:
        from_attributes = True

# --------------------------
# Incident Models (Shootings, Murders, Assists)
# --------------------------

class ShootingBase(BaseModel):
    shooter_id: int
    victim_id: int
    date: Optional[date]
    date_approx: Optional[str]


class ShootingCreate(ShootingBase):
    pass

class Shooting(ShootingBase):
    id: int

    class Config:
        from_attributes = True

class MurderBase(BaseModel):
    shooter_id: int
    victim_id: int
    date: Optional[date]
    date_approx: Optional[str]


class MurderCreate(MurderBase):
    pass

class Murder(MurderBase):
    id: int

    class Config:
        from_attributes = True

class AssistBase(BaseModel):
    shooter_id: int
    victim_id: int
    date: Optional[date]
    date_approx: Optional[str]

class AssistCreate(AssistBase):
    pass

class Assist(AssistBase):
    id: int

    class Config:
        from_attributes = True
