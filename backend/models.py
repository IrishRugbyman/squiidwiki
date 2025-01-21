from pydantic import BaseModel
from typing import Optional

class Set(BaseModel):
    id: int
    name: str
    allies: Optional[str] = None
    enemies: Optional[str] = None

class Member(BaseModel):
    id: int
    name: str
    status: str  # "free", "locked up", or "deceased"
    release_date: Optional[str] = None  # Only if status is "locked up"
    date_of_death: Optional[str] = None  # Only if status is "deceased"
    set_id: int

class Alliance(BaseModel):
    id: int
    name: str
    description: Optional[str] = None