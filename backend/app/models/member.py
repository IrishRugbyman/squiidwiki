import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.core.enums import MemberStatus


class MemberSource(SQLModel, table=True):
    __tablename__ = "member_source"

    member_id: uuid.UUID = Field(foreign_key="member.id", primary_key=True)
    source_id: uuid.UUID = Field(foreign_key="source.id", primary_key=True)


class MemberAlias(SQLModel, table=True):
    __tablename__ = "member_alias"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="member.id", index=True)
    alias: str
    from_date: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    until_date: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    source_id: Optional[uuid.UUID] = Field(default=None, foreign_key="source.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Member(SQLModel, table=True):
    __tablename__ = "member"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)

    # Identity — at least one of nickname / legal_name must be set (enforced in CRUD)
    nickname: Optional[str] = Field(default=None, index=True)
    legal_name: Optional[str] = Field(default=None, index=True)
    nickname_unknown: bool = False  # True → use legal_name as display_name
    aliases: Optional[list] = Field(default=None, sa_column=Column(JSONB))

    biography: str = ""

    set_id: Optional[uuid.UUID] = Field(default=None, foreign_key="sets.id", index=True)
    alliance_id: Optional[uuid.UUID] = Field(default=None, foreign_key="alliance.id", index=True)

    status: MemberStatus = MemberStatus.UNKNOWN

    dob: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    date_of_death: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    release_date: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    life_sentence: bool = False

    family: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    social_media: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    # Auto-populated by the incident CRUD when this member is a participant with
    # outcome=KILLED. ON DELETE SET NULL so deleting an incident gracefully unlinks.
    death_incident_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("incident.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    slug: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")

    @property
    def display_name(self) -> str:
        if self.nickname_unknown or not self.nickname:
            return self.legal_name or "Unknown"
        return self.nickname
