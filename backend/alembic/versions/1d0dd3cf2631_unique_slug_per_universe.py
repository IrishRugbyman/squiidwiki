"""unique (universe_id, slug) on member, sets, alliance

Slugs were only backed by a plain btree index, so nothing stopped two rows in
the same universe from sharing one. When that happened, get_*_by_slug's
scalar_one_or_none() raised MultipleResultsFound and the detail page rendered
"not found" (752's Tank and PBF's Tank both held `tank-2`).

Revision ID: 1d0dd3cf2631
Revises: 15c78137c9d2
Create Date: 2026-08-24
"""

from alembic import op

revision = "1d0dd3cf2631"
down_revision = "15c78137c9d2"
branch_labels = None
depends_on = None

# gang already carries uq_gang_universe_slug from an earlier revision.
TABLES = ("member", "sets", "alliance")


def upgrade() -> None:
    for table in TABLES:
        op.create_index(
            f"uq_{table}_universe_slug",
            table,
            ["universe_id", "slug"],
            unique=True,
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(f"uq_{table}_universe_slug", table_name=table)
