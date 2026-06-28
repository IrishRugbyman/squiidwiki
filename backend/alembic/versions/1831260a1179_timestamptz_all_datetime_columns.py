"""migrate all datetime columns to TIMESTAMP WITH TIME ZONE

Revision ID: 1831260a1179
Revises: 07ea27d25af6
Create Date: 2026-06-28
"""

from alembic import op

revision = "1831260a1179"
down_revision = "07ea27d25af6"
branch_labels = None
depends_on = None

_COLUMNS: list[tuple[str, str]] = [
    ("users", "created_at"),
    ("users", "last_login_at"),
    ("refresh_tokens", "created_at"),
    ("refresh_tokens", "expires_at"),
    ("universe", "created_at"),
    ("member", "created_at"),
    ("member", "updated_at"),
    ("sets", "created_at"),
    ("sets", "updated_at"),
    ("alliance", "created_at"),
    ("alliance", "updated_at"),
    ("incident", "created_at"),
    ("incident", "updated_at"),
    ("source", "created_at"),
    ("source", "updated_at"),
    ("gang", "created_at"),
    ("gang", "updated_at"),
    ("research_note", "created_at"),
    ("research_note", "updated_at"),
    ("media", "created_at"),
    ("audit_log", "created_at"),
]


def upgrade() -> None:
    for table, col in _COLUMNS:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {col} "
            f"TYPE TIMESTAMPTZ USING {col} AT TIME ZONE 'UTC'"
        )


def downgrade() -> None:
    for table, col in reversed(_COLUMNS):
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {col} "
            f"TYPE TIMESTAMP WITHOUT TIME ZONE USING {col} AT TIME ZONE 'UTC'"
        )
