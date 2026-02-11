"""Incident and IncidentParticipant models."""
from sqlalchemy import Column, String, Integer, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.associations import incident_sources
import uuid
import enum


class IncidentType(str, enum.Enum):
    """Type of incident."""
    SHOOTING = "SHOOTING"
    MURDER = "MURDER"
    STABBING = "STABBING"
    BEATING = "BEATING"
    OTHER = "OTHER"


class ParticipantRole(str, enum.Enum):
    """Role in an incident."""
    PERPETRATOR = "PERPETRATOR"
    ACCOMPLICE = "ACCOMPLICE"
    VICTIM = "VICTIM"


class VictimOutcome(str, enum.Enum):
    """Outcome for a victim."""
    UNHARMED = "UNHARMED"
    WOUNDED = "WOUNDED"
    KILLED = "KILLED"


class Incident(Base):
    """Violent incident."""
    __tablename__ = "incidents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(SQLEnum(IncidentType), nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # FuzzyDate for incident date
    date_year = Column(Integer, nullable=True)
    date_month = Column(Integer, nullable=True)
    date_day = Column(Integer, nullable=True)
    
    # Relationships
    participants = relationship("IncidentParticipant", back_populates="incident", 
                               cascade="all, delete-orphan", lazy="selectin")
    sources = relationship("Source", secondary=incident_sources, lazy="selectin")
    
    def __repr__(self):
        return f"<Incident {self.type} on {self.date_year or 'unknown'}>"


class IncidentParticipant(Base):
    """Participant in an incident."""
    __tablename__ = "incident_participants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    role = Column(SQLEnum(ParticipantRole), nullable=False)
    outcome = Column(SQLEnum(VictimOutcome), nullable=True)  # Only for VICTIM role
    notes = Column(Text, nullable=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="participants")
    member = relationship("Member", back_populates="incident_participations")
    
    def __repr__(self):
        return f"<IncidentParticipant {self.member_id} as {self.role}>"
