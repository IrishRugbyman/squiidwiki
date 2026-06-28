import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import SourceReliability


class Source(SQLModel, table=True):
    __tablename__ = "source"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    url: str
    title: str
    publication: str | None = None
    published_at: dict | None = Field(default=None, sa_column=Column(JSONB))
    accessed_at: date | None = None
    reliability: SourceReliability = SourceReliability.UNVERIFIED
    notes: str | None = None
    archive_url: str | None = None
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
