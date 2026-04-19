import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import SetRelationshipType, SetStatus


# M2M join tables
class SetMunicipality(SQLModel, table=True):
    __tablename__ = "set_municipality"

    set_id: uuid.UUID = Field(foreign_key="sets.id", primary_key=True)
    municipality_id: uuid.UUID = Field(foreign_key="municipality.id", primary_key=True)


class SetRelationship(SQLModel, table=True):
    """
    Bilateral friend/enemy link between two sets.
    Stored once: set_a_id < set_b_id enforced by CHECK constraint + Postgres trigger.
    Application CRUD must normalize (min, max) before insert.
    """
    __tablename__ = "set_relationships"
    __table_args__ = (
        CheckConstraint("set_a_id < set_b_id", name="ck_set_relationship_ordering"),
        UniqueConstraint("set_a_id", "set_b_id", name="uq_set_relationship_pair"),
    )

    set_a_id: uuid.UUID = Field(foreign_key="sets.id", primary_key=True)
    set_b_id: uuid.UUID = Field(foreign_key="sets.id", primary_key=True)
    relationship_type: SetRelationshipType


class GangSet(SQLModel, table=True):
    __tablename__ = "sets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    alias: Optional[str] = None
    bio: Optional[str] = None
    status: SetStatus = SetStatus.ACTIVE
    alliance_id: Optional[uuid.UUID] = Field(default=None, foreign_key="alliance.id")
    founder_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            "founder_id",
            sa.Uuid(),
            sa.ForeignKey("member.id", use_alter=True, name="fk_sets_founder_id"),
            nullable=True,
        ),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
