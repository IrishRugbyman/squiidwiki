import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import AuditAction, GlobalRole, UniverseRole


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    global_role: GlobalRole = GlobalRole.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None


class UserUniverseAccess(SQLModel, table=True):
    __tablename__ = "user_universe_access"

    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", primary_key=True)
    role: UniverseRole = UniverseRole.VIEWER


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    jti: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    entity_type: str = Field(index=True)
    entity_id: uuid.UUID = Field(index=True)
    action: AuditAction
    diff_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
