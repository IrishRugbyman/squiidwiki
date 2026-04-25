"""add research_note table

Revision ID: ea2e731fea3c
Revises: b5e3f1a2d4c6
Create Date: 2026-04-25 21:35:51.028806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'ea2e731fea3c'
down_revision: Union[str, None] = 'b5e3f1a2d4c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'research_note',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('universe_id', sa.Uuid(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['universe_id'], ['universe.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_research_note_universe_id'),
        'research_note',
        ['universe_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_research_note_universe_id'), table_name='research_note')
    op.drop_table('research_note')
