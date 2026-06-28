import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.core.enums import MemberStatus, SetRank


class MemberSource(SQLModel, table=True):
    __tablename__ = "member_source"

    member_id: uuid.UUID = Field(foreign_key="member.id", primary_key=True)
    source_id: uuid.UUID = Field(foreign_key="source.id", primary_key=True)


class MemberSet(SQLModel, table=True):
    __tablename__ = "member_set"

    member_id: uuid.UUID = Field(foreign_key="member.id", primary_key=True)
    set_id: uuid.UUID = Field(foreign_key="sets.id", primary_key=True)
    rank: SetRank | None = Field(default=None, sa_column=Column(String, nullable=True))
    is_primary: bool = Field(
        default=False,
        sa_column=Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
    )


class MemberAlias(SQLModel, table=True):
    __tablename__ = "member_alias"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="member.id", index=True)
    alias: str
    from_date: dict | None = Field(default=None, sa_column=Column(JSONB))
    until_date: dict | None = Field(default=None, sa_column=Column(JSONB))
    source_id: uuid.UUID | None = Field(default=None, foreign_key="source.id")
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )


class MemberIncarceration(SQLModel, table=True):
    __tablename__ = "member_incarceration"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="member.id", index=True)
    from_date: dict | None = Field(default=None, sa_column=Column(JSONB))
    earliest_release_date: dict | None = Field(default=None, sa_column=Column(JSONB))
    max_discharge_date: dict | None = Field(default=None, sa_column=Column(JSONB))
    life_sentence: bool = False
    facility: str | None = None
    case_id: str | None = None
    notes: str | None = None
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )


class Member(SQLModel, table=True):
    __tablename__ = "member"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)

    # Identity — at least one of nickname / legal_name must be set (enforced in CRUD)
    nickname: str | None = Field(default=None, index=True)
    legal_name: str | None = Field(default=None, index=True)
    nickname_unknown: bool = False  # True → use legal_name as display_name
    aliases: list | None = Field(default=None, sa_column=Column(JSONB))

    biography: str = ""

    alliance_id: uuid.UUID | None = Field(default=None, foreign_key="alliance.id", index=True)
    gang_id: uuid.UUID | None = Field(default=None, foreign_key="gang.id", index=True)

    status: MemberStatus = MemberStatus.UNKNOWN

    dob: dict | None = Field(default=None, sa_column=Column(JSONB))
    date_of_death: dict | None = Field(default=None, sa_column=Column(JSONB))

    family: dict | None = Field(default=None, sa_column=Column(JSONB))
    social_media: dict | None = Field(default=None, sa_column=Column(JSONB))

    # Auto-populated by the incident CRUD when this member is a participant with
    # outcome=KILLED. ON DELETE SET NULL so deleting an incident gracefully unlinks.
    death_incident_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("incident.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    slug: str | None = Field(default=None, index=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")

    @property
    def display_name(self) -> str:
        if self.nickname_unknown or not self.nickname:
            return self.legal_name or "Unknown"
        return self.nickname
