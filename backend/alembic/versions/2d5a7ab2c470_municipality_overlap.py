"""municipality_overlap: which districts each neighborhood lies in

A neighborhood is a child of its city, not of a ZIP district, because some cross
district lines (Dexter-Linwood is 70% in 48206 and 29% in 48238). The link
between the two layers is geometric, so it is computed from the outlines by
`sync_overlaps` in app/crud/municipality.py whenever a sub-area is written, and
stored with both shares so either page can say how much.

Backfill: `$PY -m app.scripts.recompute_overlaps`.

Revision ID: 2d5a7ab2c470
Revises: 18ab21ff07f0
Create Date: 2026-09-29
"""

import sqlalchemy as sa

from alembic import op

revision = "2d5a7ab2c470"
down_revision = "18ab21ff07f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "municipality_overlap",
        sa.Column("neighborhood_id", sa.Uuid(), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        # Fraction of the neighborhood's area inside the district, and of the
        # district's area inside the neighborhood.
        sa.Column("share_of_neighborhood", sa.Float(), nullable=False),
        sa.Column("share_of_district", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["neighborhood_id"], ["municipality.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["district_id"], ["municipality.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("neighborhood_id", "district_id"),
        sa.CheckConstraint(
            "share_of_neighborhood > 0 AND share_of_neighborhood <= 1"
            " AND share_of_district > 0 AND share_of_district <= 1",
            name="ck_municipality_overlap_shares",
        ),
    )
    op.create_index("ix_municipality_overlap_district_id", "municipality_overlap", ["district_id"])


def downgrade() -> None:
    op.drop_index("ix_municipality_overlap_district_id", table_name="municipality_overlap")
    op.drop_table("municipality_overlap")
