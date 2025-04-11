from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Enum, Index
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional
from datetime import date

from backend.database.base_class import Base


class Members(Base):
    """Model for members (individuals)"""
    __tablename__ = 'members'
    __table_args__ = (
        Index('idx_members_set_id', 'set_id'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    status = Column(Enum('dead', 'alive', 'locked_up', 'unknown'), nullable=False)
    description = Column(Text)
    release_date = Column(Date)
    release_date_approx = Column(Text, server_default="unknown")
    death_date = Column(Date)
    death_date_approx = Column(Text, server_default="unknown")
    set_id = Column(ForeignKey('sets.id', ondelete='SET NULL'))
    alliance_id = Column(Integer, server_default='NULL')

    # Relationships
    set: Mapped[Optional['Sets']] = relationship('Sets', back_populates='members')
    
    # Event relationships
    assists: Mapped[List['Assists']] = relationship('Assists', uselist=True, foreign_keys='[Assists.shooter_id]', back_populates='shooter')
    assists_: Mapped[List['Assists']] = relationship('Assists', uselist=True, foreign_keys='[Assists.victim_id]', back_populates='victim')
    murders: Mapped[List['Murders']] = relationship('Murders', uselist=True, foreign_keys='[Murders.shooter_id]', back_populates='shooter')
    murders_: Mapped['Murders'] = relationship('Murders', uselist=False, foreign_keys='[Murders.victim_id]', back_populates='victim')
    shootings: Mapped[List['Shootings']] = relationship('Shootings', uselist=True, foreign_keys='[Shootings.shooter_id]', back_populates='shooter')
    shootings_: Mapped[List['Shootings']] = relationship('Shootings', uselist=True, foreign_keys='[Shootings.victim_id]', back_populates='victim') 