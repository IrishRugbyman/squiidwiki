"""Alliance model."""
from sqlalchemy import Column, String, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.associations import alliance_sources
import uuid
import enum


class AllianceStatus(str, enum.Enum):
    """Status of an alliance."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXTINCT = "EXTINCT"


class Alliance(Base):
    """Gang alliance."""
    __tablename__ = "alliances"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    status = Column(SQLEnum(AllianceStatus), nullable=False, default=AllianceStatus.ACTIVE)
    bio = Column(Text, nullable=True)
    
    # FuzzyDate for founded date
    founded_year = Column(Integer, nullable=True)
    founded_month = Column(Integer, nullable=True)
    founded_day = Column(Integer, nullable=True)
    
    # Relationships
    sets = relationship("Set", back_populates="alliance", lazy="selectin")
    direct_members = relationship("Member", back_populates="alliance_direct", 
                                  foreign_keys="Member.alliance_id", lazy="selectin")
    sources = relationship("Source", secondary=alliance_sources, lazy="selectin")
    
    def __repr__(self):
        return f"<Alliance {self.name}>"
