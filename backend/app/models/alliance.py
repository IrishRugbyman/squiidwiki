import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import AllianceStatus, SetRelationshipType


# M2M join tables
class AllianceMunicipality(SQLModel, table=True):
    __tablename__ = "alliance_municipality"

    alliance_id: uuid.UUID = Field(foreign_key="alliance.id", primary_key=True)
    municipality_id: uuid.UUID = Field(foreign_key="municipality.id", primary_key=True)


class AllianceSet(SQLModel, table=True):
    """Every alliance a set is in, in order: position 0 is the primary.

    A set can sit in more than one bloc - TMC is in TMCNE and helped form RHN -
    so membership is this table, as gangs are `set_gang`. `sets.alliance_id` is
    the mirror of the position-0 row, written by `_sync_set_alliances` in
    crud/gang_set.py and nothing else, because the list labels, the auto-allies
    and every older reader key off it. Both ends cascade.
    """

    __tablename__ = "alliance_set"

    alliance_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid, sa.ForeignKey("alliance.id", ondelete="CASCADE"), primary_key=True
        )
    )
    set_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid, sa.ForeignKey("sets.id", ondelete="CASCADE"), primary_key=True, index=True
        )
    )
    position: int = Field(default=0)


class Alliance(SQLModel, table=True):
    __tablename__ = "alliance"
    __table_args__ = (sa.Index("uq_alliance_universe_slug", "universe_id", "slug", unique=True),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    aliases: list | None = Field(default=None, sa_column=Column(JSONB))
    description: str | None = None
    status: AllianceStatus = AllianceStatus.ACTIVE
    gang_id: uuid.UUID | None = Field(default=None, foreign_key="gang.id", index=True)
    founded_at: dict | None = Field(default=None, sa_column=Column(JSONB))
    slug: str | None = Field(default=None, index=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")


class AllianceRelationship(SQLModel, table=True):
    """Friend/enemy link held by a whole alliance, over one period of time.

    The far side is either another alliance or a single set, never both. A
    bloc's wars are rarely clique-by-clique: one bloc against another is one fact
    about two alliances, and recording it as an edge between every pair of their
    sets would claim far more than any source says. `set_relationships` cannot
    hold it, since both its ends are sets.

    Alliance-to-alliance rows are stored once, `alliance_id < other_alliance_id`,
    as `set_relationships` does for sets; an alliance-to-set row always has the
    alliance in `alliance_id`. Like a set link, the *current* row is the one with
    `until_date IS NULL`, one per pair, and ending a link sets `until_date`
    rather than deleting the row. Unlike `set_relationships`, both ends cascade:
    a link to a deleted entity has nothing left to say.
    """

    __tablename__ = "alliance_relationship"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(other_alliance_id, other_set_id) = 1",
            name="ck_alliance_relationship_one_target",
        ),
        CheckConstraint(
            "other_alliance_id IS NULL OR alliance_id < other_alliance_id",
            name="ck_alliance_relationship_ordering",
        ),
        sa.Index(
            "uq_alliance_relationship_current_alliance",
            "alliance_id",
            "other_alliance_id",
            unique=True,
            postgresql_where=sa.text("until_date IS NULL AND other_alliance_id IS NOT NULL"),
        ),
        sa.Index(
            "uq_alliance_relationship_current_set",
            "alliance_id",
            "other_set_id",
            unique=True,
            postgresql_where=sa.text("until_date IS NULL AND other_set_id IS NOT NULL"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    alliance_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("alliance.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    other_alliance_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("alliance.id", ondelete="CASCADE"), nullable=True, index=True
        ),
    )
    other_set_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=True, index=True
        ),
    )
    relationship_type: SetRelationshipType
    # none_as_null is load-bearing: see the note on MemberSet.until_date.
    from_date: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    until_date: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
