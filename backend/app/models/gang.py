import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Gang(SQLModel, table=True):
    """Top-level gang nation (e.g. Black Disciples, Latin Kings).

    Sets, alliances, and members can each be linked to a single Gang. The
    underlying organizational unit (sets) groups crews; this is the broader
    affiliation that spans multiple sets/alliances.
    """

    __tablename__ = "gang"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    aliases: Optional[list] = Field(default=None, sa_column=Column(JSONB))
    description: Optional[str] = None
    slug: Optional[str] = Field(default=None, index=True)
    color: Optional[str] = Field(default=None, max_length=16)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
