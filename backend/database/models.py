"""
Consolidated ORM models for SquiidWiki.

All domain tables live here.  Per-domain ``models/`` packages re-export the
classes they need so that existing import paths keep working.
"""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, relationship

from backend.database.base_class import AuditMixin, Base, TimestampMixin


def _enum_values(enum_cls):
    """Tell SQLAlchemy to store the enum's ``.value`` (lowercase) instead of ``.name``."""
    return [m.value for m in enum_cls]


# ───────────────────────────────────────────────────────────────────────────
# Python Enums (used as DB enum types)
# ───────────────────────────────────────────────────────────────────────────

class GlobalRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class SetType(str, enum.Enum):
    ACTIVE = "active"
    EXTINCT = "extinct"
    SYSTEM = "system"


class MemberStatus(str, enum.Enum):
    ALIVE = "alive"
    DECEASED = "dead"
    INCARCERATED = "locked_up"
    UNKNOWN = "unknown"


class EventType(str, enum.Enum):
    MURDER = "murder"
    SHOOTING = "shooting"
    ASSIST = "assist"
    PRISON_INCIDENT = "prison_incident"


class LocationType(str, enum.Enum):
    STREET = "street"
    FACILITY = "facility"


class DatePrecision(str, enum.Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class ParticipantRole(str, enum.Enum):
    SHOOTER = "shooter"
    VICTIM = "victim"
    ASSISTANT = "assistant"


class RelationshipType(str, enum.Enum):
    ALLY = "ally"
    ENEMY = "enemy"


class AllianceStatus(str, enum.Enum):
    ACTIVE = "active"
    DISSOLVED = "dissolved"


# ───────────────────────────────────────────────────────────────────────────
# System / Config tables  (no soft-delete, lightweight)
# ───────────────────────────────────────────────────────────────────────────

class Config(Base):
    __tablename__ = "config"

    key = Column(Text, primary_key=True)
    value = Column(Integer, unique=True)


class DbEnum(Base):
    """Stores dynamic enumeration values managed at runtime."""
    __tablename__ = "enums"
    __table_args__ = (UniqueConstraint("enum_type", "enum_key"),)

    id = Column(Integer, primary_key=True)
    enum_type = Column(Text, nullable=False)
    enum_key = Column(Text, nullable=False)
    enum_value = Column(Text, nullable=False)


# ───────────────────────────────────────────────────────────────────────────
# Users
# ───────────────────────────────────────────────────────────────────────────

class User(AuditMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    global_role = Column(
        Enum(GlobalRole, name="global_role_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=GlobalRole.USER.value,
    )

    @property
    def is_admin(self) -> bool:
        return self.global_role == GlobalRole.ADMIN

    @is_admin.setter
    def is_admin(self, value: bool) -> None:
        self.global_role = GlobalRole.ADMIN if value else GlobalRole.USER


# ───────────────────────────────────────────────────────────────────────────
# Sets (gangs / groups)
# ───────────────────────────────────────────────────────────────────────────

class Set(AuditMixin, Base):
    __tablename__ = "sets"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    type = Column(
        Enum(SetType, name="set_type_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=SetType.ACTIVE.value,
    )
    description = Column(Text)
    emoji = Column(Text)
    founded_date = Column(Date, nullable=True)

    # --- relationships -------------------------------------------------------
    members: Mapped[List[Member]] = relationship(
        "Member", back_populates="set", lazy="select",
    )

    relationships_as_a: Mapped[List[SetRelationship]] = relationship(
        "SetRelationship",
        foreign_keys="[SetRelationship.set_a_id]",
        back_populates="set_a",
        lazy="select",
    )
    relationships_as_b: Mapped[List[SetRelationship]] = relationship(
        "SetRelationship",
        foreign_keys="[SetRelationship.set_b_id]",
        back_populates="set_b",
        lazy="select",
    )

    alliance_memberships: Mapped[List[AllianceSetMap]] = relationship(
        "AllianceSetMap", back_populates="set", lazy="select",
    )


# ───────────────────────────────────────────────────────────────────────────
# Members
# ───────────────────────────────────────────────────────────────────────────

class Member(AuditMixin, Base):
    __tablename__ = "members"
    __table_args__ = (
        CheckConstraint(
            "death_date IS NULL OR birth_date IS NULL OR death_date >= birth_date",
            name="ck_member_death_after_birth",
        ),
        CheckConstraint(
            "joined_date IS NULL OR birth_date IS NULL OR joined_date >= birth_date",
            name="ck_member_joined_after_birth",
        ),
        Index("idx_members_set_id", "set_id"),
        Index("idx_members_status", "status"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    status = Column(
        Enum(MemberStatus, name="member_status_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=MemberStatus.ALIVE.value,
    )
    description = Column(Text)

    birth_date = Column(Date, nullable=True)
    death_date = Column(Date, nullable=True)
    death_date_precision = Column(
        Enum(DatePrecision, name="date_precision_enum", native_enum=False, values_callable=_enum_values),
        server_default=DatePrecision.UNKNOWN.value,
    )
    release_date = Column(Date, nullable=True)
    release_date_precision = Column(
        Enum(DatePrecision, name="date_precision_enum", native_enum=False, create_constraint=False, values_callable=_enum_values),
        server_default=DatePrecision.UNKNOWN.value,
    )

    set_id = Column(ForeignKey("sets.id", ondelete="SET NULL"), nullable=True)
    joined_date = Column(Date, nullable=True)

    # --- relationships -------------------------------------------------------
    set: Mapped[Optional[Set]] = relationship("Set", back_populates="members")

    event_participations: Mapped[List[EventParticipant]] = relationship(
        "EventParticipant", back_populates="member", lazy="select",
    )


# ───────────────────────────────────────────────────────────────────────────
# Events  (unified: murder, shooting, assist, prison_incident)
# ───────────────────────────────────────────────────────────────────────────

class Event(AuditMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("idx_events_type", "event_type"),
        Index("idx_events_date", "date"),
    )

    id = Column(Integer, primary_key=True)
    event_type = Column(
        Enum(EventType, name="event_type_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
    )
    date = Column(Date, nullable=True)
    date_precision = Column(
        Enum(DatePrecision, name="date_precision_enum", native_enum=False, create_constraint=False, values_callable=_enum_values),
        server_default=DatePrecision.UNKNOWN.value,
    )
    description = Column(Text)
    location_type = Column(
        Enum(LocationType, name="location_type_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=LocationType.STREET.value,
    )

    # --- relationships -------------------------------------------------------
    participants: Mapped[List[EventParticipant]] = relationship(
        "EventParticipant", back_populates="event", lazy="joined",
        cascade="all, delete-orphan",
    )


class EventParticipant(Base):
    """Association between an Event and a Member with a given role."""
    __tablename__ = "event_participants"
    __table_args__ = (
        UniqueConstraint("event_id", "member_id", "role", name="uq_event_member_role"),
        Index("idx_ep_member", "member_id"),
    )

    id = Column(Integer, primary_key=True)
    event_id = Column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    role = Column(
        Enum(ParticipantRole, name="participant_role_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
    )

    # --- relationships -------------------------------------------------------
    event: Mapped[Event] = relationship("Event", back_populates="participants")
    member: Mapped[Member] = relationship("Member", back_populates="event_participations")


# ───────────────────────────────────────────────────────────────────────────
# Set ↔ Set relationships  (ally / enemy with time-range)
# ───────────────────────────────────────────────────────────────────────────

class SetRelationship(AuditMixin, Base):
    __tablename__ = "set_relationships"
    __table_args__ = (
        CheckConstraint("set_a_id <> set_b_id", name="ck_no_self_relation"),
        UniqueConstraint(
            "set_a_id", "set_b_id", "relationship_type",
            name="uq_set_relationship",
        ),
        Index("idx_setrel_a", "set_a_id"),
        Index("idx_setrel_b", "set_b_id"),
    )

    id = Column(Integer, primary_key=True)
    set_a_id = Column(ForeignKey("sets.id", ondelete="CASCADE"), nullable=False)
    set_b_id = Column(ForeignKey("sets.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(
        Enum(RelationshipType, name="relationship_type_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
    )
    started_at = Column(Date, nullable=True)
    ended_at = Column(Date, nullable=True)

    # --- relationships -------------------------------------------------------
    set_a: Mapped[Set] = relationship(
        "Set", foreign_keys=[set_a_id], back_populates="relationships_as_a",
    )
    set_b: Mapped[Set] = relationship(
        "Set", foreign_keys=[set_b_id], back_populates="relationships_as_b",
    )

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


# ───────────────────────────────────────────────────────────────────────────
# Alliances  (named coalition of sets)
# ───────────────────────────────────────────────────────────────────────────

class Alliance(AuditMixin, Base):
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(AllianceStatus, name="alliance_status_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=AllianceStatus.ACTIVE.value,
    )
    formed_date = Column(Date, nullable=True)

    # --- relationships -------------------------------------------------------
    set_memberships: Mapped[List[AllianceSetMap]] = relationship(
        "AllianceSetMap", back_populates="alliance", lazy="joined",
        cascade="all, delete-orphan",
    )


class AllianceSetMap(AuditMixin, Base):
    """Tracks which sets belong to an alliance (with historical join/leave)."""
    __tablename__ = "alliance_set_map"
    __table_args__ = (
        UniqueConstraint("alliance_id", "set_id", name="uq_alliance_set"),
    )

    id = Column(Integer, primary_key=True)
    alliance_id = Column(ForeignKey("alliances.id", ondelete="CASCADE"), nullable=False)
    set_id = Column(ForeignKey("sets.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(Date, nullable=True)
    left_at = Column(Date, nullable=True)

    # --- relationships -------------------------------------------------------
    alliance: Mapped[Alliance] = relationship("Alliance", back_populates="set_memberships")
    set: Mapped[Set] = relationship("Set", back_populates="alliance_memberships")
