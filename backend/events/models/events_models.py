from sqlalchemy import Column, Integer, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship, Mapped
from datetime import date
from typing import Optional

from backend.database.base_class import Base
from backend.members.models.members_models import Members


class Assists(Base):
    """Model for assists between members"""
    __tablename__ = 'assists'

    id = Column(Integer, primary_key=True)
    shooter_id = Column(ForeignKey('members.id'), nullable=False)
    victim_id = Column(ForeignKey('members.id'), nullable=False)
    date = Column(Date)
    date_approx = Column(Text, server_default="unknown")

    # Relationships
    shooter: Mapped[Members] = relationship('Members', foreign_keys=[shooter_id], back_populates='assists')
    victim: Mapped[Members] = relationship('Members', foreign_keys=[victim_id], back_populates='assists_')


class Murders(Base):
    """Model for murders between members"""
    __tablename__ = 'murders'

    id = Column(Integer, primary_key=True)
    shooter_id = Column(ForeignKey('members.id'), nullable=False)
    victim_id = Column(ForeignKey('members.id'), nullable=False, unique=True)
    date = Column(Date)
    date_approx = Column(Text, server_default="unknown")

    # Relationships
    shooter: Mapped[Members] = relationship('Members', foreign_keys=[shooter_id], back_populates='murders')
    victim: Mapped[Members] = relationship('Members', foreign_keys=[victim_id], back_populates='murders_')


class Shootings(Base):
    """Model for shootings between members"""
    __tablename__ = 'shootings'

    id = Column(Integer, primary_key=True)
    shooter_id = Column(ForeignKey('members.id'), nullable=False)
    victim_id = Column(ForeignKey('members.id'), nullable=False)
    date = Column(Date)
    date_approx = Column(Text, server_default="unknown")

    # Relationships
    shooter: Mapped[Members] = relationship('Members', foreign_keys=[shooter_id], back_populates='shootings')
    victim: Mapped[Members] = relationship('Members', foreign_keys=[victim_id], back_populates='shootings_') 