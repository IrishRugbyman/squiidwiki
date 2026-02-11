"""Set (gang) model."""
from sqlalchemy import Column, String, Integer, Text, Enum as SQLEnum, ForeignKey, JSON, or_, and_, select
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.associations import set_allies, set_enemies, set_sources
import uuid
import enum


class SetStatus(str, enum.Enum):
    """Status of a set."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXTINCT = "EXTINCT"


class Set(Base):
    """Gang set."""
    __tablename__ = "sets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    primary_name = Column(String, nullable=False)
    names = Column(JSON, nullable=False, default=list)  # List of alternate names
    status = Column(SQLEnum(SetStatus), nullable=False, default=SetStatus.ACTIVE)
    territory = Column(String, nullable=True)
    colors = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Foreign key to alliance
    alliance_id = Column(String, ForeignKey("alliances.id"), nullable=True)
    
    # FuzzyDate for founded date
    founded_year = Column(Integer, nullable=True)
    founded_month = Column(Integer, nullable=True)
    founded_day = Column(Integer, nullable=True)
    
    # Relationships
    alliance = relationship("Alliance", back_populates="sets", lazy="selectin")
    members = relationship("Member", back_populates="set", foreign_keys="Member.set_id", lazy="selectin")
    sources = relationship("Source", secondary=set_sources, lazy="selectin")
    
    @property
    def allies(self):
        """Get all allied sets (bidirectional)."""
        from sqlalchemy.orm import object_session
        session = object_session(self)
        if not session:
            return []
        
        # Query both directions: where this set is set_a OR set_b
        result = session.execute(
            select(Set).join(
                set_allies,
                or_(
                    and_(set_allies.c.set_a_id == self.id, Set.id == set_allies.c.set_b_id),
                    and_(set_allies.c.set_b_id == self.id, Set.id == set_allies.c.set_a_id)
                )
            )
        ).scalars().all()
        return result
    
    @property
    def enemies(self):
        """Get all enemy sets (bidirectional)."""
        from sqlalchemy.orm import object_session
        session = object_session(self)
        if not session:
            return []
        
        # Query both directions: where this set is set_a OR set_b
        result = session.execute(
            select(Set).join(
                set_enemies,
                or_(
                    and_(set_enemies.c.set_a_id == self.id, Set.id == set_enemies.c.set_b_id),
                    and_(set_enemies.c.set_b_id == self.id, Set.id == set_enemies.c.set_a_id)
                )
            )
        ).scalars().all()
        return result
    
    def __repr__(self):
        return f"<Set {self.primary_name}>"
