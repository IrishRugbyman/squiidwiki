"""add media table and drop member.photo_url

Adds the media table for image storage (Cloudflare R2 originals + external
URL fallback). Three nullable FKs (member_id / incident_id / source_id) with
ON DELETE CASCADE plus a CHECK constraint that exactly one is set — matches
the codebase 'no polymorphism' rule.

Backfills existing member.photo_url values into media rows of kind=EXTERNAL_URL
with is_primary=true, then drops the photo_url column.

Revision ID: c8a2b3d4e5f6
Revises: a7c1f3d2e4b5
Create Date: 2026-04-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c8a2b3d4e5f6'
down_revision: Union[str, None] = 'a7c1f3d2e4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'media',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('member_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('kind', sa.String(), nullable=False, server_default='R2'),
        sa.Column('r2_key', sa.String(), nullable=True),
        sa.Column('thumb_r2_key', sa.String(), nullable=True),
        sa.Column('external_url', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('caption', sa.String(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['universe_id'], ['universe.id']),
        sa.ForeignKeyConstraint(['member_id'], ['member.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['incident_id'], ['incident.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            'num_nonnulls(member_id, incident_id, source_id) = 1',
            name='media_attaches_to_exactly_one_entity',
        ),
    )
    op.create_index('ix_media_universe_id', 'media', ['universe_id'])
    op.create_index('ix_media_member_id', 'media', ['member_id'])
    op.create_index('ix_media_incident_id', 'media', ['incident_id'])
    op.create_index('ix_media_source_id', 'media', ['source_id'])
    # Partial index for the "primary photo per member" lookup hot path.
    op.create_index(
        'ix_media_member_primary',
        'media',
        ['member_id'],
        unique=False,
        postgresql_where=sa.text('is_primary AND member_id IS NOT NULL'),
    )

    # Backfill existing photo_url values into media rows.
    op.execute("""
        INSERT INTO media (id, universe_id, member_id, kind, external_url, is_primary, created_at)
        SELECT gen_random_uuid(), universe_id, id, 'EXTERNAL_URL', photo_url, true, NOW()
        FROM member
        WHERE photo_url IS NOT NULL AND photo_url != ''
    """)

    op.drop_column('member', 'photo_url')


def downgrade() -> None:
    op.add_column('member', sa.Column('photo_url', sa.String(), nullable=True))

    # Restore primary external_url values back into member.photo_url.
    op.execute("""
        UPDATE member m
        SET photo_url = md.external_url
        FROM media md
        WHERE md.member_id = m.id
          AND md.kind = 'EXTERNAL_URL'
          AND md.is_primary = true
    """)

    op.drop_index('ix_media_member_primary', table_name='media')
    op.drop_index('ix_media_source_id', table_name='media')
    op.drop_index('ix_media_incident_id', table_name='media')
    op.drop_index('ix_media_member_id', table_name='media')
    op.drop_index('ix_media_universe_id', table_name='media')
    op.drop_table('media')
