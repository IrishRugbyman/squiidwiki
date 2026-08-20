import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import IncidentType, ParticipantOutcome, ParticipantRole


class IncidentSource(SQLModel, table=True):
    __tablename__ = "incident_source"

    incident_id: uuid.UUID = Field(foreign_key="incident.id", primary_key=True)
    source_id: uuid.UUID = Field(foreign_key="source.id", primary_key=True)


class IncidentParticipant(SQLModel, table=True):
    """
    Orthogonal role + outcome per participant.
    role = what they did; outcome = what happened to them.
    """

    __tablename__ = "incident_participant"

    incident_id: uuid.UUID = Field(foreign_key="incident.id", primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="member.id", primary_key=True)
    role: ParticipantRole
    outcome: ParticipantOutcome = ParticipantOutcome.UNKNOWN
    # A court affirmatively cleared this person of this role in this incident.
    # The default, False, means "attributed by research" and NOT "convicted":
    # almost every participant row in this database is a researcher attribution,
    # never tested in court. So this flags the narrow exceptional case, and
    # `member_stats` excludes these rows from the offender counts so an acquitted
    # man's profile does not show a red "Kills" tile. Detail goes in `notes`.
    acquitted: bool = Field(
        default=False,
        sa_column=Column("acquitted", Boolean, nullable=False, server_default="false"),
    )
    notes: str | None = None


class IncidentSetParticipant(SQLModel, table=True):
    """Set-level participant — used when the individual shooter is unknown."""

    __tablename__ = "incident_set_participant"

    incident_id: uuid.UUID = Field(foreign_key="incident.id", primary_key=True)
    set_id: uuid.UUID = Field(foreign_key="sets.id", primary_key=True)
    role: ParticipantRole
    outcome: ParticipantOutcome = ParticipantOutcome.UNKNOWN
    notes: str | None = None


class Incident(SQLModel, table=True):
    __tablename__ = "incident"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    type: IncidentType
    date: dict | None = Field(default=None, sa_column=Column(JSONB))
    sortable_date: datetime | None = Field(default=None, index=True)
    municipality_id: uuid.UUID | None = Field(default=None, foreign_key="municipality.id")
    location_text: str | None = None
    lat: float | None = None
    lng: float | None = None
    narrative: str | None = None
    verified: bool = False
    verified_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
