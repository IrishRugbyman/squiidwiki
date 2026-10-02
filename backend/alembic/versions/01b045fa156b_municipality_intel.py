"""municipality intel: kind, aliases, region, description, sources, photos

A municipality held a name, a parent and a boundary, and nothing of what the
community maps say about a place: its street names ("The Hole", "Zone 6"), the
area it belongs to ("Downriver"), its history, the pictures that go with it.

- `kind` says what a row is. CITY is top level; DISTRICT is a sub-division that
  partitions its city (Detroit's ZIP codes, Corsican hamlets); NEIGHBORHOOD is
  a named area whose outline may overlap districts (Dexter-Linwood crosses
  several ZIPs), so a districts map never draws both at once.
- `aliases` (JSONB list of strings), `region`, `description`.
- `municipality_source`, the citations behind the description.
- `media.municipality_id`, so a place carries photos like a set does.

Backfill: every top-level row is a CITY and every child a DISTRICT, which is
what each of them was before this revision.

Revision ID: 01b045fa156b
Revises: ce9354d43875
Create Date: 2026-09-29
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "01b045fa156b"
down_revision = "ce9354d43875"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "municipality",
        sa.Column("kind", sa.String(16), nullable=False, server_default="CITY"),
    )
    op.execute("UPDATE municipality SET kind = 'DISTRICT' WHERE parent_id IS NOT NULL")
    op.create_check_constraint(
        "ck_municipality_kind",
        "municipality",
        "kind IN ('CITY', 'DISTRICT', 'NEIGHBORHOOD')",
    )
    op.create_check_constraint(
        "ck_municipality_kind_parent",
        "municipality",
        "(kind = 'CITY') = (parent_id IS NULL)",
    )
    op.add_column("municipality", sa.Column("aliases", postgresql.JSONB(), nullable=True))
    op.add_column("municipality", sa.Column("region", sa.String(), nullable=True))
    op.add_column("municipality", sa.Column("description", sa.String(), nullable=True))
    op.create_index("ix_municipality_parent_id", "municipality", ["parent_id"])

    op.create_table(
        "municipality_source",
        sa.Column("municipality_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["municipality_id"], ["municipality.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("municipality_id", "source_id"),
    )

    op.add_column("media", sa.Column("municipality_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "media_municipality_id_fkey",
        "media",
        "municipality",
        ["municipality_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_media_municipality_id", "media", ["municipality_id"])
    op.drop_constraint("media_attaches_to_exactly_one_entity", "media", type_="check")
    op.create_check_constraint(
        "media_attaches_to_exactly_one_entity",
        "media",
        "num_nonnulls(member_id, incident_id, source_id, set_id, alliance_id, municipality_id) = 1",
    )


def downgrade() -> None:
    op.execute("DELETE FROM media WHERE municipality_id IS NOT NULL")
    op.drop_constraint("media_attaches_to_exactly_one_entity", "media", type_="check")
    op.create_check_constraint(
        "media_attaches_to_exactly_one_entity",
        "media",
        "num_nonnulls(member_id, incident_id, source_id, set_id, alliance_id) = 1",
    )
    op.drop_index("ix_media_municipality_id", table_name="media")
    op.drop_constraint("media_municipality_id_fkey", "media", type_="foreignkey")
    op.drop_column("media", "municipality_id")

    op.drop_table("municipality_source")

    op.drop_index("ix_municipality_parent_id", table_name="municipality")
    op.drop_column("municipality", "description")
    op.drop_column("municipality", "region")
    op.drop_column("municipality", "aliases")
    op.drop_constraint("ck_municipality_kind_parent", "municipality", type_="check")
    op.drop_constraint("ck_municipality_kind", "municipality", type_="check")
    op.drop_column("municipality", "kind")
