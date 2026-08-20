import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.core.enums import BusinessRole, BusinessStatus, BusinessType


def _fk_cascade(target: str) -> Column:
    return Column(PG_UUID(as_uuid=True), ForeignKey(target, ondelete="CASCADE"), primary_key=True)


class BusinessMember(SQLModel, table=True):
    """A member's link to a business: owner, front person, or beneficiary.

    Not dated (unlike member_set): control changes over decades of ownership
    history are real for this milieu but there is no matter to model yet. See
    member_set/set_relationships if that changes.

    Both FKs cascade: deleting the business or the member should not require
    business.py's own delete path to be duplicated inside crud/member.py.
    """

    __tablename__ = "business_member"

    business_id: uuid.UUID = Field(sa_column=_fk_cascade("business.id"))
    member_id: uuid.UUID = Field(sa_column=_fk_cascade("member.id"))
    role: BusinessRole


class BusinessSet(SQLModel, table=True):
    """The set(s) that protect or control this business."""

    __tablename__ = "business_set"

    business_id: uuid.UUID = Field(sa_column=_fk_cascade("business.id"))
    set_id: uuid.UUID = Field(sa_column=_fk_cascade("sets.id"))


class BusinessSource(SQLModel, table=True):
    __tablename__ = "business_source"

    business_id: uuid.UUID = Field(sa_column=_fk_cascade("business.id"))
    source_id: uuid.UUID = Field(sa_column=_fk_cascade("source.id"))


class Business(SQLModel, table=True):
    """A legitimate or front business: gaming, construction, ports, waste
    management, and the like. Economic capture is a first-class part of some
    milieus (Corsican organised crime especially) in a way territory alone
    does not represent."""

    __tablename__ = "business"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    aliases: list | None = Field(default=None, sa_column=Column(JSONB))
    business_type: BusinessType
    description: str | None = None
    status: BusinessStatus = BusinessStatus.ACTIVE
    municipality_id: uuid.UUID | None = Field(
        default=None, foreign_key="municipality.id", index=True
    )
    founded_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    ended_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    slug: str | None = Field(default=None, index=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
