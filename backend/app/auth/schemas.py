import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.core.enums import GlobalRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    global_role: GlobalRole
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    global_role: GlobalRole = GlobalRole.USER
