import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.enums import RapGroupKind, RapGroupRole, RapGroupStatus, SetRelationshipType


class RapGroup(SQLModel, table=True):
    """A rap group or a record label: artists who record together, or the
    company they sign to.

    Not a set: it has no map, no set stats and is never an affiliation. Its
    members keep their real set; the group is a separate link
    (`rap_group_member`). `kind` tells the two apart, and everything else about
    them is the same.
    """

    __tablename__ = "rap_group"
    __table_args__ = (sa.Index("uq_rap_group_universe_slug", "universe_id", "slug", unique=True),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    # Derived, never set on its own: the display of the primary entry in
    # name_variants, exactly as for sets and alliances (app/core/set_names.py).
    name: str = Field(index=True)
    name_variants: list | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    kind: RapGroupKind = RapGroupKind.GROUP
    status: RapGroupStatus = RapGroupStatus.ACTIVE
    # none_as_null is load-bearing: see the note on MemberSet.until_date.
    active_from: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    active_to: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    # The home area.
    municipality_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(sa.Uuid(), sa.ForeignKey("municipality.id"), nullable=True, index=True),
    )
    bio: str | None = None
    slug: str | None = Field(default=None, index=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")


class RapGroupMember(SQLModel, table=True):
    """A member's place in a rap group, in order: position 0 is listed first.

    A member can be in several groups. Both ends cascade. The member must be in
    the group's universe (checked in crud/rap_group.py).
    """

    __tablename__ = "rap_group_member"

    rap_group_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("rap_group.id", ondelete="CASCADE"), primary_key=True
        )
    )
    member_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("member.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        )
    )
    role: RapGroupRole = RapGroupRole.MEMBER
    since: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    until: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    position: int = Field(default=0)


class RapGroupRelationship(SQLModel, table=True):
    """Friend/enemy link between two rap groups, stored once in UUID order
    (`rap_group_a_id < rap_group_b_id`) and normalised by the CRUD, as for sets.
    One row per pair; both ends cascade."""

    __tablename__ = "rap_group_relationship"
    __table_args__ = (
        CheckConstraint("rap_group_a_id < rap_group_b_id", name="ck_rap_group_relationship_order"),
    )

    rap_group_a_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(), sa.ForeignKey("rap_group.id", ondelete="CASCADE"), primary_key=True
        )
    )
    rap_group_b_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("rap_group.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        )
    )
    relationship_type: SetRelationshipType
