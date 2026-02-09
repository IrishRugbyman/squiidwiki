"""Member model."""
from sqlalchemy import Column, String, Integer, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.associations import member_sources
import uuid
import enum


class MemberStatus(str, enum.Enum):
    """Status of a member."""
    ALIVE_FREE = "ALIVE_FREE"
    ALIVE_LOCKED_UP = "ALIVE_LOCKED_UP"
    DEAD = "DEAD"
    UNKNOWN = "UNKNOWN"


class AffiliationType(str, enum.Enum):
    """Type of gang affiliation."""
    SET = "SET"
    ALLIANCE = "ALLIANCE"
    CIVILIAN = "CIVILIAN"
    UNKNOWN = "UNKNOWN"


class Member(Base):
    """Gang member or civilian."""
    __tablename__ = "members"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    nicknames = Column(JSON, nullable=False, default=list)  # List of nicknames
    status = Column(SQLEnum(MemberStatus), nullable=False, default=MemberStatus.UNKNOWN)
    bio = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    social_media = Column(JSON, nullable=True)  # Dict of social media links
    
    # Affiliation
    affiliation_type = Column(SQLEnum(AffiliationType), nullable=False, default=AffiliationType.UNKNOWN)
    set_id = Column(String, ForeignKey("sets.id"), nullable=True)
    alliance_id = Column(String, ForeignKey("alliances.id"), nullable=True)
    
    # FuzzyDate for date of birth
    dob_year = Column(Integer, nullable=True)
    dob_month = Column(Integer, nullable=True)
    dob_day = Column(Integer, nullable=True)
    
    # FuzzyDate for date of death
    dod_year = Column(Integer, nullable=True)
    dod_month = Column(Integer, nullable=True)
    dod_day = Column(Integer, nullable=True)
    
    # FuzzyDate for release from prison
    release_year = Column(Integer, nullable=True)
    release_month = Column(Integer, nullable=True)
    release_day = Column(Integer, nullable=True)
    
    # Relationships
    set = relationship("Set", back_populates="members", foreign_keys=[set_id], lazy="selectin")
    alliance_direct = relationship("Alliance", back_populates="direct_members", 
                                   foreign_keys=[alliance_id], lazy="selectin")
    incident_participations = relationship("IncidentParticipant", back_populates="member", lazy="selectin")
    sources = relationship("Source", secondary=member_sources, lazy="selectin")
    
    def __repr__(self):
        name = self.first_name or (self.nicknames[0] if self.nicknames else "Unknown")
        return f"<Member {name}>"
