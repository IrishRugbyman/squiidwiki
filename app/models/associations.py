"""Association tables for many-to-many relationships."""
from sqlalchemy import Table, Column, ForeignKey, Integer, String, CheckConstraint
from app.models.base import Base
import uuid


# Set allies (self-referential M2M)
set_allies = Table(
    "set_allies",
    Base.metadata,
    Column("set_a_id", String, ForeignKey("sets.id"), primary_key=True),
    Column("set_b_id", String, ForeignKey("sets.id"), primary_key=True),
    Column("since_year", Integer, nullable=True),
    Column("since_month", Integer, nullable=True),
    Column("since_day", Integer, nullable=True),
    CheckConstraint("set_a_id < set_b_id", name="set_allies_order_check")
)

# Set enemies (self-referential M2M)
set_enemies = Table(
    "set_enemies",
    Base.metadata,
    Column("set_a_id", String, ForeignKey("sets.id"), primary_key=True),
    Column("set_b_id", String, ForeignKey("sets.id"), primary_key=True),
    Column("since_year", Integer, nullable=True),
    Column("since_month", Integer, nullable=True),
    Column("since_day", Integer, nullable=True),
    CheckConstraint("set_a_id < set_b_id", name="set_enemies_order_check")
)

# Member-Source M2M
member_sources = Table(
    "member_sources",
    Base.metadata,
    Column("member_id", String, ForeignKey("members.id"), primary_key=True),
    Column("source_id", String, ForeignKey("sources.id"), primary_key=True)
)

# Set-Source M2M
set_sources = Table(
    "set_sources",
    Base.metadata,
    Column("set_id", String, ForeignKey("sets.id"), primary_key=True),
    Column("source_id", String, ForeignKey("sources.id"), primary_key=True)
)

# Alliance-Source M2M
alliance_sources = Table(
    "alliance_sources",
    Base.metadata,
    Column("alliance_id", String, ForeignKey("alliances.id"), primary_key=True),
    Column("source_id", String, ForeignKey("sources.id"), primary_key=True)
)

# Incident-Source M2M
incident_sources = Table(
    "incident_sources",
    Base.metadata,
    Column("incident_id", String, ForeignKey("incidents.id"), primary_key=True),
    Column("source_id", String, ForeignKey("sources.id"), primary_key=True)
)
