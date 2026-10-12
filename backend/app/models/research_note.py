import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, DateTime, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.core.enums import NoteKind


class ResearchNote(SQLModel, table=True):
    __tablename__ = "research_note"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('INBOX', 'FOR_YOU', 'PARKED', 'REFERENCE')", name="ck_research_note_kind"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    title: str
    content: str = ""
    # VARCHAR plus a CHECK, not a Postgres ENUM, for the same reason as media.kind.
    kind: NoteKind = Field(
        default=NoteKind.INBOX,
        sa_column=Column(String(16), nullable=False, server_default="INBOX", index=True),
    )
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")


class ResearchNotePin(SQLModel, table=True):
    """A note pinned to one entity (member, set, incident or alliance).

    Exactly one target column is set. Every FK cascades: deleting the entity
    removes the pin and leaves the note, deleting the note removes its pins.
    """

    __tablename__ = "research_note_pin"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(member_id, set_id, incident_id, alliance_id) = 1",
            name="ck_research_note_pin_one_target",
        ),
        UniqueConstraint("note_id", "member_id", name="uq_research_note_pin_member"),
        UniqueConstraint("note_id", "set_id", name="uq_research_note_pin_set"),
        UniqueConstraint("note_id", "incident_id", name="uq_research_note_pin_incident"),
        UniqueConstraint("note_id", "alliance_id", name="uq_research_note_pin_alliance"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    note_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("research_note.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    member_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("member.id", ondelete="CASCADE"), nullable=True, index=True
        ),
    )
    set_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=True, index=True
        ),
    )
    incident_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("incident.id", ondelete="CASCADE"), nullable=True, index=True
        ),
    )
    alliance_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("alliance.id", ondelete="CASCADE"), nullable=True, index=True
        ),
    )
