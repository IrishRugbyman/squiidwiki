from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime
from typing import List

from backend.database.base_class import Base
from backend.sets.models.sets_models import Sets


# Association table for the many-to-many relationship between alliances and sets
alliance_set_association = Table(
    'alliance_set',
    Base.metadata,
    Column('alliance_id', Integer, ForeignKey('alliances.id', ondelete='CASCADE'), primary_key=True),
    Column('set_id', Integer, ForeignKey('sets.id', ondelete='CASCADE'), primary_key=True)
)


class Alliance(Base):
    """Alliance model representing an alliance between sets"""
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationship with sets (many-to-many)
    sets = relationship(
        "Sets",
        secondary=alliance_set_association,
        back_populates="alliances",
        lazy="joined"
    )
    
    # Relationship with AllianceSetsMap
    alliance_sets_map: Mapped[List['AllianceSetsMap']] = relationship('AllianceSetsMap', uselist=True, back_populates='alliance')


class AllianceSetsMap(Base):
    """Model for mapping the many-to-many relationship between alliances and sets"""
    __tablename__ = 'alliance_sets_map'
    __table_args__ = (
        UniqueConstraint('alliance_id', 'set_id'),
    )

    id = Column(Integer, primary_key=True)
    alliance_id = Column(ForeignKey('alliances.id', ondelete='CASCADE'), nullable=False)
    set_id = Column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    alliance: Mapped['Alliance'] = relationship('Alliance', back_populates='alliance_sets_map')
    set: Mapped[Sets] = relationship('Sets', back_populates='alliance_sets_map') 