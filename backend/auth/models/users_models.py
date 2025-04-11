from sqlalchemy import Column, Integer, Text, Boolean, DateTime, text
from sqlalchemy.orm import Mapped
from datetime import datetime

from backend.database.base_class import Base


class Users(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    is_admin = Column(Boolean, nullable=False, server_default=text("0"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP")) 