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
from backend.database.fuzzy_date import FuzzyDateJSON


def _enum_values(enum_cls):
    """Tell SQLAlchemy to store the enum's ``.value`` (lowercase) instead of ``.name``."""
    return [m.value for m in enum_cls]


# ───────────────────────────────────────────────────────────────────────────
# Python Enums (used as DB enum types)
# ───────────────────────────────────────────────────────────────────────────

class GlobalRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class UniverseRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class SetType(str, enum.Enum):
    ACTIVE = "active"
    EXTINCT = "extinct"
    SYSTEM = "system"


class MemberStatus(str, enum.Enum):
    ALIVE = "alive"
    DECEASED = "dead"
    INCARCERATED = "locked_up"
    UNKNOWN = "unknown"


class LocationType(str, enum.Enum):
    STREET = "street"
    FACILITY = "facility"


class DatePrecision(str, enum.Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class IncidentType(str, enum.Enum):
    SHOOTING = "shooting"
    MURDER = "murder"


class IncidentRole(str, enum.Enum):
    SHOOTER = "shooter"
    ASSISTED = "assisted"
    BYSTANDER = "bystander"
    VICTIM = "victim"


class IncidentOutcome(str, enum.Enum):
    KILLED = "killed"
    INJURED = "injured"
    UNHARMED = "unharmed"
    UNKNOWN = "unknown"


class RelationshipType(str, enum.Enum):
    ALLY = "ally"
    ENEMY = "enemy"


class AllianceStatus(str, enum.Enum):
    ACTIVE = "active"
    DISSOLVED = "dissolved"


class SourceReliability(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


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
# Universes
# ───────────────────────────────────────────────────────────────────────────

class Universe(AuditMixin, Base):
    __tablename__ = "universes"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True)
    created_by_id = Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])


class UserUniverseAccess(Base):
    __tablename__ = "user_universe_access"
    __table_args__ = (
        UniqueConstraint("user_id", "universe_id", name="uq_user_universe"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    universe_id = Column(ForeignKey("universes.id", ondelete="CASCADE"), nullable=False)
    role = Column(
        Enum(UniverseRole, name="universe_role_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=UniverseRole.VIEWER.value,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    universe: Mapped[Universe] = relationship("Universe", foreign_keys=[universe_id])


# ───────────────────────────────────────────────────────────────────────────
# Sets (gangs / groups)
# ───────────────────────────────────────────────────────────────────────────

class Set(AuditMixin, Base):
    __tablename__ = "sets"

    id = Column(Integer, primary_key=True)
    universe_id = Column(ForeignKey("universes.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(Text, nullable=False, unique=True)
    type = Column(
        Enum(SetType, name="set_type_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=SetType.ACTIVE.value,
    )
    description = Column(Text)
    emoji = Column(Text)
    founded_date = Column(FuzzyDateJSON, nullable=True)
    founded_date_sortable = Column(Date, nullable=True)

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
            "death_date_sortable IS NULL OR birth_date_sortable IS NULL OR death_date_sortable >= birth_date_sortable",
            name="ck_member_death_after_birth",
        ),
        CheckConstraint(
            "joined_date IS NULL OR birth_date_sortable IS NULL OR joined_date >= birth_date_sortable",
            name="ck_member_joined_after_birth",
        ),
        Index("idx_members_set_id", "set_id"),
        Index("idx_members_status", "status"),
    )

    id = Column(Integer, primary_key=True)
    universe_id = Column(ForeignKey("universes.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(Text, nullable=False)
    status = Column(
        Enum(MemberStatus, name="member_status_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=MemberStatus.ALIVE.value,
    )
    description = Column(Text)

    birth_date = Column(FuzzyDateJSON, nullable=True)
    birth_date_sortable = Column(Date, nullable=True)
    death_date = Column(FuzzyDateJSON, nullable=True)
    death_date_sortable = Column(Date, nullable=True)
    release_date = Column(FuzzyDateJSON, nullable=True)
    release_date_sortable = Column(Date, nullable=True)

    set_id = Column(ForeignKey("sets.id", ondelete="SET NULL"), nullable=True)
    joined_date = Column(Date, nullable=True)

    # --- relationships -------------------------------------------------------
    set: Mapped[Optional[Set]] = relationship("Set", back_populates="members")

    incident_participations: Mapped[List["IncidentParticipant"]] = relationship(
        "IncidentParticipant", back_populates="member", lazy="select",
    )


# ───────────────────────────────────────────────────────────────────────────
# Incidents  (SHOOTING / MURDER with orthogonal role + outcome per participant)
# ───────────────────────────────────────────────────────────────────────────

class Incident(AuditMixin, Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("idx_incidents_type", "incident_type"),
        Index("idx_incidents_date_sortable", "date_sortable"),
    )

    id = Column(Integer, primary_key=True)
    universe_id = Column(ForeignKey("universes.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_type = Column(
        Enum(IncidentType, name="incident_type_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
    )
    date = Column(FuzzyDateJSON, nullable=True)
    date_sortable = Column(Date, nullable=True)
    location_type = Column(
        Enum(LocationType, name="location_type_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=LocationType.STREET.value,
    )
    narrative = Column(Text, nullable=True)
    verified = Column(Boolean, nullable=False, server_default="false")

    # --- relationships -------------------------------------------------------
    participants: Mapped[List["IncidentParticipant"]] = relationship(
        "IncidentParticipant", back_populates="incident",
        cascade="all, delete-orphan", lazy="select",
    )


class IncidentParticipant(Base):
    """Join table: Incident ↔ Member with orthogonal role and outcome."""
    __tablename__ = "incident_participants"
    __table_args__ = (
        UniqueConstraint("incident_id", "member_id", "role", name="uq_incident_member_role"),
        Index("idx_ip_member", "member_id"),
        Index("idx_ip_incident", "incident_id"),
    )

    id = Column(Integer, primary_key=True)
    incident_id = Column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    role = Column(
        Enum(IncidentRole, name="incident_role_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
    )
    outcome = Column(
        Enum(IncidentOutcome, name="incident_outcome_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=IncidentOutcome.UNKNOWN.value,
    )

    # --- relationships -------------------------------------------------------
    incident: Mapped[Incident] = relationship("Incident", back_populates="participants")
    member: Mapped[Member] = relationship("Member", back_populates="incident_participations")


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
    universe_id = Column(ForeignKey("universes.id", ondelete="SET NULL"), nullable=True, index=True)
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


# ───────────────────────────────────────────────────────────────────────────
# Sources  (citations / references for Members and Incidents)
# ───────────────────────────────────────────────────────────────────────────

class Source(AuditMixin, Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    universe_id = Column(ForeignKey("universes.id", ondelete="SET NULL"), nullable=True, index=True)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    publication = Column(Text, nullable=True)
    published_at = Column(FuzzyDateJSON, nullable=True)
    published_at_sortable = Column(Date, nullable=True)
    accessed_at = Column(Date, nullable=True)
    reliability = Column(
        Enum(SourceReliability, name="source_reliability_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
        server_default=SourceReliability.UNVERIFIED.value,
    )
    archive_url = Column(Text, nullable=True)

    # --- relationships -------------------------------------------------------
    member_links: Mapped[List["MemberSource"]] = relationship(
        "MemberSource", back_populates="source", cascade="all, delete-orphan",
    )
    incident_links: Mapped[List["IncidentSource"]] = relationship(
        "IncidentSource", back_populates="source", cascade="all, delete-orphan",
    )


class MemberSource(Base):
    """M2M join: Member ↔ Source."""
    __tablename__ = "member_sources"
    __table_args__ = (
        UniqueConstraint("member_id", "source_id", name="uq_member_source"),
    )

    id = Column(Integer, primary_key=True)
    member_id = Column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)

    member: Mapped[Member] = relationship("Member")
    source: Mapped[Source] = relationship("Source", back_populates="member_links")


class IncidentSource(Base):
    """M2M join: Incident ↔ Source."""
    __tablename__ = "incident_sources"
    __table_args__ = (
        UniqueConstraint("incident_id", "source_id", name="uq_incident_source"),
    )

    id = Column(Integer, primary_key=True)
    incident_id = Column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)

    incident: Mapped[Incident] = relationship("Incident")
    source: Mapped[Source] = relationship("Source", back_populates="incident_links")


# ───────────────────────────────────────────────────────────────────────────
# AuditLog  (immutable append-only write log)
# ───────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """Immutable record of every create/update/delete on domain entities."""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(
        Enum(AuditAction, name="audit_action_enum", native_enum=False, values_callable=_enum_values),
        nullable=False,
    )
    diff_json = Column(Text, nullable=True)  # JSON stored as text for SQLite compat
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        default=func.now(),
    )

    user: Mapped[Optional["User"]] = relationship("User")
