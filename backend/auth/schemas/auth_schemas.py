from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.database.models import GlobalRole


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    global_role: GlobalRole = GlobalRole.USER
    is_admin: bool = False
    created_at: Optional[datetime] = None


class UserInDB(User):
    pass


class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False
