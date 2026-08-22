"""clean up JSONB 'null' on member and add spouse to the family relation set

Five nullable JSONB columns on `member` (dob, date_of_death, family,
social_media, aliases) lacked `none_as_null=True`, so SQLAlchemy was writing
Python None as the JSON scalar `null` rather than SQL NULL. That value is
invisible to `IS NOT NULL` / `IS NULL`, the only check every read path uses.
Same bug class as migration 6b102eb7959a (incident type) and the fix caught
in 57f8aaa46bdd (member_set/set_relationships), just not caught here yet.

No column type changes: none_as_null is a Python-side serialization flag on
JSONB, not a different Postgres type, so this is a data-only migration.

Revision ID: 572768a81ef3
Revises: aa14ae65b26f
Create Date: 2026-08-20
"""

from alembic import op

revision = "572768a81ef3"
down_revision = "58e15d368e68"
branch_labels = None
depends_on = None

_COLUMNS = ("dob", "date_of_death", "family", "social_media", "aliases")


def upgrade() -> None:
    for col in _COLUMNS:
        op.execute(f"UPDATE member SET {col} = NULL WHERE {col} = 'null'::jsonb")


def downgrade() -> None:
    # The corrupted state was a bug, not data; there is nothing to restore.
    pass
