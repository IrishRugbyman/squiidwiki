"""add CRASH to incidenttype

A car crash kills people the wiki has to record, and none of the existing
types can hold one without lying: MURDER and SHOOTING assert an aggressor.
Without a type, the dead could only carry a date and a line of biography, and
the men who died in the same car had no page to share. A crash can matter to
the record beyond its deaths, too: sets have been named after men killed in one.

ALTER TYPE ... ADD VALUE is allowed inside a transaction from PostgreSQL 12, so
long as the new value is not *used* in the same transaction. This migration only
adds it, so it is safe here; the rows come later.

The downgrade is real rather than a pass, but it refuses to run while any
incident still uses the value, as the ROBBERY migration does.

Revision ID: af5914edd23e
Revises: dca974125ded
Create Date: 2026-09-25
"""

from alembic import op

revision = "af5914edd23e"
down_revision = "dca974125ded"
branch_labels = None
depends_on = None

_WITHOUT_CRASH = (
    "'SHOOTING', 'MURDER', 'FIGHT', 'BOMBING', 'ARSON', 'EXTORTION', 'KIDNAPPING', 'ROBBERY'"
)


def upgrade() -> None:
    op.execute("ALTER TYPE incidenttype ADD VALUE IF NOT EXISTS 'CRASH'")


def downgrade() -> None:
    conn = op.get_bind()
    in_use = conn.exec_driver_sql("SELECT count(*) FROM incident WHERE type = 'CRASH'").scalar()
    if in_use:
        raise RuntimeError(
            f"{in_use} incident(s) are typed CRASH. Retype or delete them before "
            "downgrading; this migration will not rewrite them for you."
        )
    # Postgres cannot drop a value from an enum, so the type is rebuilt.
    op.execute(f"CREATE TYPE incidenttype_old AS ENUM ({_WITHOUT_CRASH})")
    op.execute(
        "ALTER TABLE incident ALTER COLUMN type TYPE incidenttype_old "
        "USING type::text::incidenttype_old"
    )
    op.execute("DROP TYPE incidenttype")
    op.execute("ALTER TYPE incidenttype_old RENAME TO incidenttype")
