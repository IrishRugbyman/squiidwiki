from pydantic import BaseModel, Field
from typing import Optional, List, Union
from backend.database.enums import eSetType


class SetBase(BaseModel):
    """Base schema for Set data with common fields."""
    name: str
    description: Optional[str] = None
    emoji: Optional[str] = None


class SetCreate(SetBase):
    """Schema for creating a new Set."""
    allies: Optional[str] = None
    enemies: Optional[str] = None
    is_extinct: bool = False


class SetUpdate(SetBase):
    """Schema for updating an existing Set."""
    allies: Optional[str] = None
    enemies: Optional[str] = None
    is_extinct: bool = False


class SetResponse(SetBase):
    """Schema for Set responses."""
    id: int
    type: Union[int, str]  # To accommodate both int and enum string representation
    
    class Config:
        orm_mode = True


class SetOption(BaseModel):
    """Simple schema for set options (id and name only)."""
    id: int
    name: str
    
    class Config:
        orm_mode = True


class SetDetail(SetResponse):
    """Detailed Set response including related entities."""
    allies: List["SetResponse"] = []
    enemies: List["SetResponse"] = []
    members_count: int = 0
    
    class Config:
        orm_mode = True 