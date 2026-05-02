"""add_slug_to_gang_set

Revision ID: 10d0ba868d7f
Revises: 9065522d726a
Create Date: 2026-04-19 22:11:57.161607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '10d0ba868d7f'
down_revision: Union[str, None] = '9065522d726a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sets', sa.Column('slug', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_index(op.f('ix_sets_slug'), 'sets', ['slug'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sets_slug'), table_name='sets')
    op.drop_column('sets', 'slug')
