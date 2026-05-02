import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import AllianceStatus


# M2M join tables
class AllianceMunicipality(SQLModel, table=True):
    __tablename__ = "alliance_municipality"

    alliance_id: uuid.UUID = Field(foreign_key="alliance.id", primary_key=True)
    municipality_id: uuid.UUID = Field(foreign_key="municipality.id", primary_key=True)


class AllianceSet(SQLModel, table=True):
    __tablename__ = "alliance_set"

    alliance_id: uuid.UUID = Field(foreign_key="alliance.id", primary_key=True)
    set_id: uuid.UUID = Field(foreign_key="sets.id", primary_key=True)


class Alliance(SQLModel, table=True):
    __tablename__ = "alliance"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    aliases: Optional[list] = Field(default=None, sa_column=Column(JSONB))
    description: Optional[str] = None
    status: AllianceStatus = AllianceStatus.ACTIVE
    founded_at: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    slug: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
