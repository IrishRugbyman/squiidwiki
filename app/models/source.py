"""Source model."""
from sqlalchemy import Column, String, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid
import enum


class SourceType(str, enum.Enum):
    """Type of source."""
    NEWS_ARTICLE = "NEWS_ARTICLE"
    COURT_DOCUMENT = "COURT_DOCUMENT"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    VIDEO = "VIDEO"
    WITNESS = "WITNESS"
    OTHER = "OTHER"


class Source(Base):
    """Source of information."""
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(SQLEnum(SourceType), nullable=False)
    title = Column(String, nullable=True)
    url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # FuzzyDate for source date
    date_year = Column(Integer, nullable=True)
    date_month = Column(Integer, nullable=True)
    date_day = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Source {self.id}: {self.title or self.type}>"
