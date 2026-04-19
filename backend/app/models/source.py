import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import SourceReliability


class Source(SQLModel, table=True):
    __tablename__ = "source"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    url: str
    title: str
    publication: Optional[str] = None
    published_at: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    accessed_at: Optional[date] = None
    reliability: SourceReliability = SourceReliability.UNVERIFIED
    notes: Optional[str] = None
    archive_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
