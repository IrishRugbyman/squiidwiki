"""set name_variants

Replace sets.aliases (jsonb list[str]) with sets.name_variants
(jsonb list[{name?, initials?, number?, is_primary}]). Backfills
each set's primary variant from the existing name column and
preserves prior aliases as additional non-primary variants
(with the alias string placed in the `name` field; users can
re-classify into initials/number via the UI).

Revision ID: 29e5618942bc
Revises: 33ac22d53ce8
Create Date: 2026-05-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '29e5618942bc'
down_revision: Union[str, None] = '33ac22d53ce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sets',
        sa.Column('name_variants', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        """
        UPDATE sets
        SET name_variants = (
            SELECT jsonb_build_array(
                jsonb_build_object(
                    'name', name,
                    'initials', NULL,
                    'number', NULL,
                    'is_primary', TRUE
                )
            )
            || CASE
                WHEN aliases IS NULL OR jsonb_typeof(aliases) <> 'array'
                    THEN '[]'::jsonb
                ELSE COALESCE(
                    (
                        SELECT jsonb_agg(
                            jsonb_build_object(
                                'name', a,
                                'initials', NULL,
                                'number', NULL,
                                'is_primary', FALSE
                            )
                        )
                        FROM jsonb_array_elements_text(aliases) AS a
                    ),
                    '[]'::jsonb
                )
            END
        )
        WHERE name IS NOT NULL
        """
    )
    op.drop_column('sets', 'aliases')


def downgrade() -> None:
    op.add_column(
        'sets',
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        """
        UPDATE sets
        SET aliases = (
            SELECT jsonb_agg(elem->>'name')
            FROM jsonb_array_elements(name_variants) AS elem
            WHERE COALESCE((elem->>'is_primary')::boolean, FALSE) = FALSE
              AND elem->>'name' IS NOT NULL
        )
        WHERE name_variants IS NOT NULL
        """
    )
    op.drop_column('sets', 'name_variants')
