"""
Authentication schema models.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema for JWT payload."""
    username: Optional[str] = None


class User(BaseModel):
    """User schema for responses."""
    id: int
    username: str
    is_admin: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User schema with database fields."""
    pass


class UserCreate(BaseModel):
    """User schema for creation."""
    username: str
    password: str
    is_admin: Optional[bool] = False 