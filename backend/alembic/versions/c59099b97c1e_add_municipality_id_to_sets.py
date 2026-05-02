"""add municipality_id to sets

Adds a single primary municipality FK on `sets`. Sets pick one top-level
municipality (Detroit, Warren, Hamtramck, …); their multi-territory sub-district
claims continue to live in the existing `set_municipality` M2M.

Revision ID: c59099b97c1e
Revises: f3a8c9d0e1b2
Create Date: 2026-04-26 20:42:27.749633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c59099b97c1e'
down_revision: Union[str, None] = 'f3a8c9d0e1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sets', sa.Column('municipality_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_sets_municipality_id'), 'sets', ['municipality_id'], unique=False)
    op.create_foreign_key(
        'fk_sets_municipality_id', 'sets', 'municipality',
        ['municipality_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_sets_municipality_id', 'sets', type_='foreignkey')
    op.drop_index(op.f('ix_sets_municipality_id'), table_name='sets')
    op.drop_column('sets', 'municipality_id')
