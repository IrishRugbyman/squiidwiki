import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ResearchNote(SQLModel, table=True):
    __tablename__ = "research_note"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    title: str
    content: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
