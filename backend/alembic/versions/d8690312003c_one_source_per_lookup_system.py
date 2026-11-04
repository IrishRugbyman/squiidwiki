"""One source per custody lookup system per universe.

Revision ID: d8690312003c
Revises: 4a89130f7a88
Create Date: 2026-10-04

Run after app/scripts/merge_lookup_sources.py has folded each universe's BOP,
OTIS and GDC rows into one; until then the index cannot be built, and this
migration fails loudly rather than leave duplicates in place.
"""

import sqlalchemy as sa

from alembic import op

revision = "d8690312003c"
down_revision = "4a89130f7a88"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_source_universe_lookup_system",
        "source",
        ["universe_id", "lookup_system"],
        unique=True,
        postgresql_where=sa.text("lookup_system IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_source_universe_lookup_system", table_name="source")
