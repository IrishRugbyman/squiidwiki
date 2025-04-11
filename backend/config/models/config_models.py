from sqlalchemy import Column, Integer, Text, UniqueConstraint
from sqlalchemy.ext.declarative import DeclarativeMeta

from backend.database.base_class import Base


class Config(Base):
    """Configuration model for system settings"""
    __tablename__ = 'config'

    key = Column(Text, primary_key=True)
    value = Column(Integer, unique=True)


class Enums(Base):
    """Model for storing enumeration values"""
    __tablename__ = 'enums'
    __table_args__ = (
        UniqueConstraint('enum_type', 'enum_key'),
    )

    id = Column(Integer, primary_key=True)
    enum_type = Column(Text, nullable=False)
    enum_key = Column(Text, nullable=False)
    enum_value = Column(Text, nullable=False) 