import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
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
    notes: Optional[str] = None


class IncidentSetParticipant(SQLModel, table=True):
    """Set-level participant — used when the individual shooter is unknown."""
    __tablename__ = "incident_set_participant"

    incident_id: uuid.UUID = Field(foreign_key="incident.id", primary_key=True)
    set_id: uuid.UUID = Field(foreign_key="sets.id", primary_key=True)
    role: ParticipantRole
    outcome: ParticipantOutcome = ParticipantOutcome.UNKNOWN
    notes: Optional[str] = None


class Incident(SQLModel, table=True):
    __tablename__ = "incident"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    type: IncidentType
    date: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    sortable_date: Optional[datetime] = Field(default=None, index=True)
    municipality_id: Optional[uuid.UUID] = Field(default=None, foreign_key="municipality.id")
    location_text: Optional[str] = None
    narrative: Optional[str] = None
    verified: bool = False
    verified_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
