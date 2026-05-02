import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Universe(SQLModel, table=True):
    __tablename__ = "universe"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
