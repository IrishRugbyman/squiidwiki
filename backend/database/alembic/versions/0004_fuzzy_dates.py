"""fuzzydate: replace plain Date columns with FuzzyDate JSONB + sortable

Revision ID: 0004_fuzzy_dates
Revises: 0003_universe
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_fuzzy_dates"
down_revision = "0003_universe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── sets: founded_date Date → JSONB + sortable ──────────────────────
    op.drop_column("sets", "founded_date")
    op.add_column("sets", sa.Column("founded_date", sa.JSON(), nullable=True))
    op.add_column("sets", sa.Column("founded_date_sortable", sa.Date(), nullable=True))

    # ── members: birth/death/release Date → JSONB + sortable ────────────
    for col in ("birth_date", "death_date", "release_date"):
        op.drop_column("members", col)
        op.add_column("members", sa.Column(col, sa.JSON(), nullable=True))
        op.add_column("members", sa.Column(f"{col}_sortable", sa.Date(), nullable=True))

    op.drop_column("members", "death_date_precision")
    op.drop_column("members", "release_date_precision")

    # Update check constraints to use sortable columns (IF EXISTS — baseline may not have created them)
    op.execute("ALTER TABLE members DROP CONSTRAINT IF EXISTS ck_member_death_after_birth")
    op.execute("ALTER TABLE members DROP CONSTRAINT IF EXISTS ck_member_joined_after_birth")
    op.create_check_constraint(
        "ck_member_death_after_birth",
        "members",
        "death_date_sortable IS NULL OR birth_date_sortable IS NULL OR death_date_sortable >= birth_date_sortable",
    )
    op.create_check_constraint(
        "ck_member_joined_after_birth",
        "members",
        "joined_date IS NULL OR birth_date_sortable IS NULL OR joined_date >= birth_date_sortable",
    )

    # ── events: date Date → JSONB + sortable ────────────────────────────
    op.drop_column("events", "date")
    op.add_column("events", sa.Column("date", sa.JSON(), nullable=True))
    op.add_column("events", sa.Column("date_sortable", sa.Date(), nullable=True))
    op.drop_column("events", "date_precision")


def downgrade() -> None:
    # Lossy: restore plain Date columns (data not backfilled)
    op.drop_column("events", "date")
    op.drop_column("events", "date_sortable")
    op.add_column("events", sa.Column("date", sa.Date(), nullable=True))
    op.add_column("events", sa.Column("date_precision", sa.Text(), nullable=True, server_default="unknown"))

    for col in ("birth_date", "death_date", "release_date"):
        op.drop_column("members", col)
        op.drop_column("members", f"{col}_sortable")
        op.add_column("members", sa.Column(col, sa.Date(), nullable=True))
    op.add_column("members", sa.Column("death_date_precision", sa.Text(), nullable=True, server_default="unknown"))
    op.add_column("members", sa.Column("release_date_precision", sa.Text(), nullable=True, server_default="unknown"))

    op.execute("ALTER TABLE members DROP CONSTRAINT IF EXISTS ck_member_death_after_birth")
    op.execute("ALTER TABLE members DROP CONSTRAINT IF EXISTS ck_member_joined_after_birth")
    op.create_check_constraint(
        "ck_member_death_after_birth",
        "members",
        "death_date IS NULL OR birth_date IS NULL OR death_date >= birth_date",
    )
    op.create_check_constraint(
        "ck_member_joined_after_birth",
        "members",
        "joined_date IS NULL OR birth_date IS NULL OR joined_date >= birth_date",
    )

    op.drop_column("sets", "founded_date")
    op.drop_column("sets", "founded_date_sortable")
    op.add_column("sets", sa.Column("founded_date", sa.Date(), nullable=True))
