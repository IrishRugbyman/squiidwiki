"""add updated_at to sets, alliances, sources, incidents

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ('sets', 'alliance', 'source', 'incident'):
        op.add_column(
            table,
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        )


def downgrade() -> None:
    for table in ('sets', 'alliance', 'source', 'incident'):
        op.drop_column(table, 'updated_at')
