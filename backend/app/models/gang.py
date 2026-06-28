import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Gang(SQLModel, table=True):
    """Top-level gang nation (e.g. Black Disciples, Latin Kings).

    Sets, alliances, and members can each be linked to a single Gang. The
    underlying organizational unit (sets) groups crews; this is the broader
    affiliation that spans multiple sets/alliances.
    """

    __tablename__ = "gang"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    aliases: list | None = Field(default=None, sa_column=Column(JSONB))
    description: str | None = None
    slug: str | None = Field(default=None, index=True)
    color: str | None = Field(default=None, max_length=16)
    color_secondary: str | None = Field(default=None, max_length=16)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
