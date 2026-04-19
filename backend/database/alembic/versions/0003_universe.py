"""universe multi-tenancy

Revision ID: 0003_universe
Revises: 0002_auth_upgrade
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_universe"
down_revision = "0002_auth_upgrade"
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
        "universes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_audit_cols,
    )
    op.create_index("idx_universes_deleted_at", "universes", ["deleted_at"])

    op.create_table(
        "user_universe_access",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("universe_id", sa.Integer(), sa.ForeignKey("universes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="viewer"),
        sa.UniqueConstraint("user_id", "universe_id", name="uq_user_universe"),
    )

    # Add nullable universe_id to domain tables
    for table in ("sets", "members", "alliances"):
        op.add_column(table, sa.Column(
            "universe_id",
            sa.Integer(),
            sa.ForeignKey("universes.id", ondelete="SET NULL"),
            nullable=True,
        ))
        op.create_index(f"idx_{table}_universe_id", table, ["universe_id"])


def downgrade() -> None:
    for table in ("sets", "members", "alliances"):
        op.drop_index(f"idx_{table}_universe_id", table_name=table)
        op.drop_column(table, "universe_id")

    op.drop_table("user_universe_access")
    op.drop_table("universes")
