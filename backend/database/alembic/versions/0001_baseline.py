"""baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

_audit_cols = [
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("is_archived", sa.Boolean(), server_default="false", nullable=False),
]


def upgrade() -> None:
    op.create_table(
        "config",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", sa.Integer(), unique=True),
    )

    op.create_table(
        "enums",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("enum_type", sa.Text(), nullable=False),
        sa.Column("enum_key", sa.Text(), nullable=False),
        sa.Column("enum_value", sa.Text(), nullable=False),
        sa.UniqueConstraint("enum_type", "enum_key"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
        *_audit_cols,
    )

    op.create_table(
        "alliances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("formed_date", sa.Date()),
        *_audit_cols,
    )

    op.create_table(
        "sets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("type", sa.String(50), server_default="active", nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("emoji", sa.Text()),
        sa.Column("founded_date", sa.Date()),
        *_audit_cols,
    )

    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), server_default="alive", nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("birth_date", sa.Date()),
        sa.Column("death_date", sa.Date()),
        sa.Column("death_date_precision", sa.String(50), server_default="unknown"),
        sa.Column("release_date", sa.Date()),
        sa.Column("release_date_precision", sa.String(50), server_default="unknown"),
        sa.Column("set_id", sa.Integer(), sa.ForeignKey("sets.id", ondelete="SET NULL")),
        sa.Column("joined_date", sa.Date()),
        sa.CheckConstraint(
            "death_date IS NULL OR birth_date IS NULL OR death_date >= birth_date",
            name="ck_member_death_after_birth",
        ),
        sa.CheckConstraint(
            "joined_date IS NULL OR birth_date IS NULL OR joined_date >= birth_date",
            name="ck_member_joined_after_birth",
        ),
        *_audit_cols,
    )
    op.create_index("idx_members_set_id", "members", ["set_id"])
    op.create_index("idx_members_status", "members", ["status"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("date", sa.Date()),
        sa.Column("date_precision", sa.String(50), server_default="unknown"),
        sa.Column("description", sa.Text()),
        sa.Column("location_type", sa.String(50), server_default="street", nullable=False),
        *_audit_cols,
    )
    op.create_index("idx_events_type", "events", ["event_type"])
    op.create_index("idx_events_date", "events", ["date"])

    op.create_table(
        "event_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.UniqueConstraint("event_id", "member_id", "role", name="uq_event_member_role"),
    )
    op.create_index("idx_ep_member", "event_participants", ["member_id"])

    op.create_table(
        "set_relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("set_a_id", sa.Integer(), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("set_b_id", sa.Integer(), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("started_at", sa.Date()),
        sa.Column("ended_at", sa.Date()),
        sa.CheckConstraint("set_a_id <> set_b_id", name="ck_no_self_relation"),
        sa.UniqueConstraint("set_a_id", "set_b_id", "relationship_type", name="uq_set_relationship"),
        *_audit_cols,
    )
    op.create_index("idx_setrel_a", "set_relationships", ["set_a_id"])
    op.create_index("idx_setrel_b", "set_relationships", ["set_b_id"])

    op.create_table(
        "alliance_set_map",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alliance_id", sa.Integer(), sa.ForeignKey("alliances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("set_id", sa.Integer(), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.Date()),
        sa.Column("left_at", sa.Date()),
        sa.UniqueConstraint("alliance_id", "set_id", name="uq_alliance_set"),
        *_audit_cols,
    )

    # Indexes for deleted_at (soft-delete filter performance)
    for table in ("users", "sets", "members", "events", "set_relationships", "alliances", "alliance_set_map"):
        op.create_index(f"idx_{table}_deleted_at", table, ["deleted_at"])


def downgrade() -> None:
    for table in ("alliance_set_map", "set_relationships", "event_participants",
                  "events", "members", "sets", "alliances", "users", "enums", "config"):
        op.drop_table(table)
