"""add member.set_rank

Adds an optional rank within the member's set (CEO, CO_CEO for now).
Stored as VARCHAR (no Postgres ENUM) so adding new ranks later is just a
code change.

Revision ID: 9a3dc580f64a
Revises: 8ff5d700c6b5
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa


revision = '9a3dc580f64a'
down_revision = '8ff5d700c6b5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('member', sa.Column('set_rank', sa.String(), nullable=True))


def downgrade():
    op.drop_column('member', 'set_rank')
