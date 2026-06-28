import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.core.enums import MediaKind


class Media(SQLModel, table=True):
    __tablename__ = "media"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)

    # Exactly one of these is non-null — enforced by a CHECK constraint at the
    # DB level (see migration) and by `_ensure_exactly_one` in app/crud/media.py.
    member_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("member.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    incident_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("incident.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    source_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("source.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    set_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("sets.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    alliance_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("alliance.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )

    kind: MediaKind = Field(
        default=MediaKind.R2, sa_column=Column(String, nullable=False, server_default="R2")
    )
    r2_key: str | None = None
    thumb_r2_key: str | None = None
    external_url: str | None = None

    original_filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    width: int | None = None
    height: int | None = None
    caption: str | None = None
    is_primary: bool = False

    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
