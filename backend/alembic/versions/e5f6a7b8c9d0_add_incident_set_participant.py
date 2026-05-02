"""add incident_set_participant table

Revision ID: e5f6a7b8c9d0
Revises: d1e2f3a4b5c6
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'incident_set_participant',
        sa.Column('incident_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('outcome', sa.String(), nullable=False, server_default='UNKNOWN'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incident.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['set_id'], ['sets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('incident_id', 'set_id'),
    )
    op.create_index('ix_incident_set_participant_set_id', 'incident_set_participant', ['set_id'])


def downgrade() -> None:
    op.drop_index('ix_incident_set_participant_set_id', table_name='incident_set_participant')
    op.drop_table('incident_set_participant')
