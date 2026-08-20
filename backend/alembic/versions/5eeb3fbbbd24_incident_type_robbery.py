"""add ROBBERY to incidenttype

Armed robbery is what the Brise de Mer was actually built on, and the enum had
no way to say so. Its three signature jobs (the UBS heist in Geneva in 1990,
125 million francs; the Paris-Bastia flight in 1991; the plane on the tarmac at
Bastia-Poretta in 1992, robbed by four men who arrived by helicopter) could not
be recorded at all, which left Richard Casanova, the presumed mastermind of the
UBS job, with no trace of the thing he is best known for.

ALTER TYPE ... ADD VALUE is allowed inside a transaction from PostgreSQL 12, so
long as the new value is not *used* in the same transaction. This migration only
adds it, so it is safe here; the rows come later.

The downgrade is real rather than a pass, but it refuses to run while any
incident still uses the value. Silently rewriting those rows to some other type
would corrupt the record to make a schema change tidy.

Revision ID: 5eeb3fbbbd24
Revises: 56eddc26ba9b
Create Date: 2026-08-20
"""

from alembic import op

revision = "5eeb3fbbbd24"
down_revision = "56eddc26ba9b"
branch_labels = None
depends_on = None

_WITHOUT_ROBBERY = "'SHOOTING', 'MURDER', 'FIGHT', 'BOMBING', 'ARSON', 'EXTORTION', 'KIDNAPPING'"


def upgrade() -> None:
    op.execute("ALTER TYPE incidenttype ADD VALUE IF NOT EXISTS 'ROBBERY'")


def downgrade() -> None:
    conn = op.get_bind()
    in_use = conn.exec_driver_sql("SELECT count(*) FROM incident WHERE type = 'ROBBERY'").scalar()
    if in_use:
        raise RuntimeError(
            f"{in_use} incident(s) are typed ROBBERY. Retype or delete them before "
            "downgrading; this migration will not rewrite them for you."
        )
    # Postgres cannot drop a value from an enum, so the type is rebuilt.
    op.execute(f"CREATE TYPE incidenttype_old AS ENUM ({_WITHOUT_ROBBERY})")
    op.execute(
        "ALTER TABLE incident ALTER COLUMN type TYPE incidenttype_old "
        "USING type::text::incidenttype_old"
    )
    op.execute("DROP TYPE incidenttype")
    op.execute("ALTER TYPE incidenttype_old RENAME TO incidenttype")
