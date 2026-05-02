"""multi-alias for sets and alliance

Migrate sets.alias (text) -> sets.aliases (jsonb array of text)
and add alliance.aliases (jsonb array of text). Member.aliases
already exists from the initial schema, so it is untouched.

Revision ID: f3a8c9d0e1b2
Revises: ea2e731fea3c
Create Date: 2026-04-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f3a8c9d0e1b2'
down_revision: Union[str, None] = 'ea2e731fea3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sets: add aliases JSONB, backfill from existing alias, drop alias
    op.add_column(
        'sets',
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        "UPDATE sets SET aliases = jsonb_build_array(alias) "
        "WHERE alias IS NOT NULL AND alias <> ''"
    )
    op.drop_column('sets', 'alias')

    # alliance: add aliases JSONB (no prior column to migrate)
    op.add_column(
        'alliance',
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('alliance', 'aliases')

    op.add_column(
        'sets',
        sa.Column('alias', sa.String(), nullable=True),
    )
    op.execute(
        "UPDATE sets SET alias = aliases->>0 "
        "WHERE aliases IS NOT NULL AND jsonb_array_length(aliases) >= 1"
    )
    op.drop_column('sets', 'aliases')
