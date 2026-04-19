import uuid
from typing import Optional

from sqlmodel import Field, SQLModel


class Municipality(SQLModel, table=True):
    __tablename__ = "municipality"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="municipality.id")
