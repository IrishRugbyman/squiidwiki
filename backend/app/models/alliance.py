import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
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
    __table_args__ = (sa.Index("uq_alliance_universe_slug", "universe_id", "slug", unique=True),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    aliases: list | None = Field(default=None, sa_column=Column(JSONB))
    description: str | None = None
    status: AllianceStatus = AllianceStatus.ACTIVE
    gang_id: uuid.UUID | None = Field(default=None, foreign_key="gang.id", index=True)
    founded_at: dict | None = Field(default=None, sa_column=Column(JSONB))
    slug: str | None = Field(default=None, index=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
