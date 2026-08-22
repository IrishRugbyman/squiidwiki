"""re-clean JSONB 'null' on member, and stop it coming back

Migration 572768a81ef3 already did this once, but only the DATA: the model kept
plain `Column(JSONB)` on member.dob / date_of_death / family / social_media /
aliases, so the Chicago reseed of 2026-08-21 wrote 4,565 fresh rows with the JSON
scalar `null` again. `IS NULL` cannot see that value, so "which members have no
date of birth" answered zero on a table where none of them had one.

The model now carries none_as_null=True on all five columns, which is what keeps
this fixed; this revision cleans what the reseed left behind.

Revision ID: d5a2e08edf2c
Revises: 5eeb3fbbbd24
Create Date: 2026-08-22
"""

from alembic import op

revision = "d5a2e08edf2c"
down_revision = "5eeb3fbbbd24"
branch_labels = None
depends_on = None

_COLUMNS = ("dob", "date_of_death", "family", "social_media", "aliases")


def upgrade() -> None:
    for col in _COLUMNS:
        op.execute(f"UPDATE member SET {col} = NULL WHERE {col} = 'null'::jsonb")


def downgrade() -> None:
    # The corrupted state was a bug, not data; there is nothing to restore.
    pass
