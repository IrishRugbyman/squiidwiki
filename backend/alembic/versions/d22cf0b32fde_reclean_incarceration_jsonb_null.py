"""re-clean JSONB 'null' on member_incarceration

Same bug as d5a2e08edf2c, one table over. member_incarceration.from_date,
earliest_release_date and max_discharge_date were plain Column(JSONB), so every
absent date was stored as the JSON scalar `null`, which IS NULL cannot see.

That distinction carries meaning here: a federal spell legitimately has no
earliest_release_date (no parole), and "no parole" must stay tellable from
"unknown". 21 Detroit rows were affected; the Chicago rows written after the
model fix were already clean.

The model now carries none_as_null=True on all three columns, which is what keeps
this from coming back.

Revision ID: d22cf0b32fde
Revises: d5a2e08edf2c
Create Date: 2026-08-22
"""

from alembic import op

revision = "d22cf0b32fde"
down_revision = "d5a2e08edf2c"
branch_labels = None
depends_on = None

_COLUMNS = ("from_date", "earliest_release_date", "max_discharge_date")


def upgrade() -> None:
    for col in _COLUMNS:
        op.execute(f"UPDATE member_incarceration SET {col} = NULL WHERE {col} = 'null'::jsonb")


def downgrade() -> None:
    # The corrupted state was a bug, not data; there is nothing to restore.
    pass
