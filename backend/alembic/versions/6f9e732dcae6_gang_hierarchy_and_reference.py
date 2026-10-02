"""gang: parent card, nation, origin, founding date, symbols

A gang card gains the reference fields its page needs:

- `parent_id`: the card this one is a branch of (Rollin 60s -> Crips, Mafia
  Insane Vice Lords -> Vice Lords). Self-referencing FK, ON DELETE SET NULL, so
  removing a parent leaves its branches standing as top-level cards.
- `nation`: FOLK or PEOPLE for the Chicago lineages, as text rather than a
  Postgres enum (the media.kind precedent).
- `origin`, `founded_at` (FuzzyDate JSONB, as alliance.founded_at), `symbols`
  (JSONB list of strings).

All nullable, nothing backfilled: the values are research, written afterwards.

Revision ID: 6f9e732dcae6
Revises: b305c16cd347
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "6f9e732dcae6"
down_revision = "b305c16cd347"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("gang", sa.Column("parent_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "gang_parent_id_fkey", "gang", "gang", ["parent_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_gang_parent_id", "gang", ["parent_id"])
    op.add_column("gang", sa.Column("nation", sa.String(16), nullable=True))
    op.create_check_constraint(
        "ck_gang_nation", "gang", "nation IS NULL OR nation IN ('FOLK', 'PEOPLE')"
    )
    op.create_check_constraint(
        "ck_gang_parent_not_self", "gang", "parent_id IS NULL OR parent_id <> id"
    )
    op.add_column("gang", sa.Column("origin", sa.String(), nullable=True))
    op.add_column("gang", sa.Column("founded_at", postgresql.JSONB(), nullable=True))
    op.add_column("gang", sa.Column("symbols", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("gang", "symbols")
    op.drop_column("gang", "founded_at")
    op.drop_column("gang", "origin")
    op.drop_constraint("ck_gang_parent_not_self", "gang", type_="check")
    op.drop_constraint("ck_gang_nation", "gang", type_="check")
    op.drop_column("gang", "nation")
    op.drop_index("ix_gang_parent_id", table_name="gang")
    op.drop_constraint("gang_parent_id_fkey", "gang", type_="foreignkey")
    op.drop_column("gang", "parent_id")
