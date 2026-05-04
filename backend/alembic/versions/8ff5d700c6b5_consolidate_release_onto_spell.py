"""consolidate release fields onto incarceration spell

Adds member_incarceration.life_sentence; drops member.release_date and
member.life_sentence (they're redundant now that the spell carries
earliest_release_date / max_discharge_date / life_sentence).

Revision ID: 8ff5d700c6b5
Revises: 7b3e9a4c2d1f
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '8ff5d700c6b5'
down_revision = '7b3e9a4c2d1f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'member_incarceration',
        sa.Column('life_sentence', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Migrate any existing member.life_sentence=true into the latest spell, if one exists.
    op.execute("""
        UPDATE member_incarceration mi
        SET life_sentence = TRUE,
            earliest_release_date = NULL,
            max_discharge_date = NULL
        FROM (
            SELECT DISTINCT ON (member_id) id
            FROM member_incarceration
            ORDER BY member_id, created_at DESC
        ) latest
        JOIN member m ON m.id = (
            SELECT member_id FROM member_incarceration WHERE id = latest.id
        )
        WHERE mi.id = latest.id AND m.life_sentence = TRUE
    """)
    op.drop_column('member', 'release_date')
    op.drop_column('member', 'life_sentence')


def downgrade():
    op.add_column('member', sa.Column('release_date', JSONB, nullable=True))
    op.add_column(
        'member',
        sa.Column('life_sentence', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Best-effort: if any spell was a life sentence, mark its member as life_sentence too.
    op.execute("""
        UPDATE member m
        SET life_sentence = TRUE
        WHERE EXISTS (
            SELECT 1 FROM member_incarceration mi
            WHERE mi.member_id = m.id AND mi.life_sentence = TRUE
        )
    """)
    op.drop_column('member_incarceration', 'life_sentence')
