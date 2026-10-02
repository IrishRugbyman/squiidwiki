"""municipality population: the latest official count, its year and who counted

Three columns rather than one: a bare number reads as current forever, and the
counts come from different bodies on different cycles (US Census annual estimates
for cities, ACS 5-year for ZIP areas and CDPs, INSEE populations légales for
French communes), so the page has to say which year and whose figure it shows.
Filled by `app/scripts/import_populations.py`.

Revision ID: 18ab21ff07f0
Revises: 01b045fa156b
Create Date: 2026-09-29
"""

import sqlalchemy as sa

from alembic import op

revision = "18ab21ff07f0"
down_revision = "01b045fa156b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("municipality", sa.Column("population", sa.Integer(), nullable=True))
    op.add_column("municipality", sa.Column("population_year", sa.SmallInteger(), nullable=True))
    op.add_column("municipality", sa.Column("population_source", sa.String(), nullable=True))
    op.create_check_constraint(
        "ck_municipality_population_nonneg", "municipality", "population IS NULL OR population >= 0"
    )


def downgrade() -> None:
    op.drop_constraint("ck_municipality_population_nonneg", "municipality", type_="check")
    op.drop_column("municipality", "population_source")
    op.drop_column("municipality", "population_year")
    op.drop_column("municipality", "population")
