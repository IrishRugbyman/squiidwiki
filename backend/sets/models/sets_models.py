from sqlalchemy import Column, Integer, Text, Enum, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional

from backend.database.base_class import Base
from backend.members.models.members_models import Members


class Sets(Base):
    """Model for sets (groups) of members"""
    __tablename__ = 'sets'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    type = Column(Enum('active', 'extinct', 'system', name='set_type_enum'), nullable=False, server_default="active")
    description = Column(Text)
    emoji = Column(Text)

    # Relationships
    alliance_sets_map: Mapped[List['AllianceSetsMap']] = relationship('AllianceSetsMap', uselist=True, back_populates='set')
    members: Mapped[List[Members]] = relationship('Members', uselist=True, back_populates='set')
    set_allies_map: Mapped[List['SetAlliesMap']] = relationship('SetAlliesMap', uselist=True, foreign_keys='[SetAlliesMap.ally_id]', back_populates='ally')
    set_allies_map_: Mapped[List['SetAlliesMap']] = relationship('SetAlliesMap', uselist=True, foreign_keys='[SetAlliesMap.set_id]', back_populates='set')
    set_enemies_map: Mapped[List['SetEnemiesMap']] = relationship('SetEnemiesMap', uselist=True, foreign_keys='[SetEnemiesMap.enemy_id]', back_populates='enemy')
    set_enemies_map_: Mapped[List['SetEnemiesMap']] = relationship('SetEnemiesMap', uselist=True, foreign_keys='[SetEnemiesMap.set_id]', back_populates='set')
    
    # Add relationship with alliances through AllianceSetsMap
    alliances = relationship(
        "Alliance",
        secondary="alliance_set",
        back_populates="sets",
        overlaps="alliance_sets_map,set"
    )


class SetAlliesMap(Base):
    """Model for mapping ally relationships between sets"""
    __tablename__ = 'set_allies_map'
    __table_args__ = (
        UniqueConstraint('set_id', 'ally_id'),
    )

    id = Column(Integer, primary_key=True)
    set_id = Column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    ally_id = Column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    ally: Mapped['Sets'] = relationship('Sets', foreign_keys=[ally_id], back_populates='set_allies_map')
    set: Mapped['Sets'] = relationship('Sets', foreign_keys=[set_id], back_populates='set_allies_map_')


class SetEnemiesMap(Base):
    """Model for mapping enemy relationships between sets"""
    __tablename__ = 'set_enemies_map'
    __table_args__ = (
        UniqueConstraint('set_id', 'enemy_id'),
    )

    id = Column(Integer, primary_key=True)
    set_id = Column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    enemy_id = Column(ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    enemy: Mapped['Sets'] = relationship('Sets', foreign_keys=[enemy_id], back_populates='set_enemies_map')
    set: Mapped['Sets'] = relationship('Sets', foreign_keys=[set_id], back_populates='set_enemies_map_') 