"""Municipalities gain a HOUSING_PROJECT kind.

Revision ID: 4f215263e2b3
Revises: d8690312003c
Create Date: 2026-10-04

A public housing estate (the Brewster Homes, the Jeffries) is drawn over the
districts like a neighborhood, but is not one. `kind` is VARCHAR(16) checked by
ck_municipality_kind, so only the CHECK changes.
"""

from alembic import op

revision = "4f215263e2b3"
down_revision = "d8690312003c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_municipality_kind", "municipality", type_="check")
    op.create_check_constraint(
        "ck_municipality_kind",
        "municipality",
        "kind IN ('CITY', 'DISTRICT', 'NEIGHBORHOOD', 'HOUSING_PROJECT')",
    )


def downgrade() -> None:
    # Fails loudly while any row still holds HOUSING_PROJECT: retype those first.
    op.drop_constraint("ck_municipality_kind", "municipality", type_="check")
    op.create_check_constraint(
        "ck_municipality_kind",
        "municipality",
        "kind IN ('CITY', 'DISTRICT', 'NEIGHBORHOOD')",
    )
