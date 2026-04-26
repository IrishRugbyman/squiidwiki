"""add life_sentence to member

Adds a boolean column distinguishing life-sentence prisoners from those with
an unknown release date. UI shows "Life" when set; release_date is null.

Revision ID: d8a1b2c3e4f5
Revises: c59099b97c1e
Create Date: 2026-04-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd8a1b2c3e4f5'
down_revision: Union[str, None] = 'c59099b97c1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'member',
        sa.Column('life_sentence', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('member', 'life_sentence')
