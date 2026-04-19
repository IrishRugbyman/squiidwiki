"""incidents: replace events/event_participants with incidents/incident_participants

Revision ID: 0005_incidents
Revises: 0004_fuzzy_dates
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_incidents"
down_revision = "0004_fuzzy_dates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old events tables
    op.drop_table("event_participants")
    op.drop_table("events")

    # Create incidents table
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("universe_id", sa.Integer(), sa.ForeignKey("universes.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("incident_type", sa.Text(), nullable=False),
        sa.Column("date", sa.JSON(), nullable=True),
        sa.Column("date_sortable", sa.Date(), nullable=True),
        sa.Column("location_type", sa.Text(), nullable=False, server_default="street"),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_incidents_type", "incidents", ["incident_type"])
    op.create_index("idx_incidents_date_sortable", "incidents", ["date_sortable"])

    # Create incident_participants table
    op.create_table(
        "incident_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False, server_default="unknown"),
    )
    op.create_unique_constraint(
        "uq_incident_member_role", "incident_participants",
        ["incident_id", "member_id", "role"],
    )
    op.create_index("idx_ip_member", "incident_participants", ["member_id"])
    op.create_index("idx_ip_incident", "incident_participants", ["incident_id"])


def downgrade() -> None:
    op.drop_table("incident_participants")
    op.drop_table("incidents")

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("universe_id", sa.Integer(), sa.ForeignKey("universes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("date", sa.JSON(), nullable=True),
        sa.Column("date_sortable", sa.Date(), nullable=True),
        sa.Column("location_type", sa.Text(), nullable=False, server_default="street"),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "event_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False, server_default="unknown"),
    )
