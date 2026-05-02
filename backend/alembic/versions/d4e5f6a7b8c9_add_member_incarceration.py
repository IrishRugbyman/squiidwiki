"""add member_incarceration table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'member_incarceration',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('member_id', UUID(as_uuid=True), sa.ForeignKey('member.id'), nullable=False, index=True),
        sa.Column('from_date', JSONB, nullable=True),
        sa.Column('to_date', JSONB, nullable=True),
        sa.Column('facility', sa.String, nullable=True),
        sa.Column('case_id', sa.String, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
    )


def downgrade():
    op.drop_table('member_incarceration')
