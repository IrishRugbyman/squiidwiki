"""add OVERDOSE to incidenttype

Not every death is a killing. An overdose (in a cell, in a stash house) has a
date, a place and often other people present, so it is an event the record can
hold, as a crash already is; without a type it could only be a date of death and
a line of biography, and anything reading the database (the Instagram memorials
first) had to guess how he died. Like CRASH it asserts no aggressor: the SHOOTER
role is whoever supplied the drugs, and is usually empty.

An illness is deliberately not a type: it has no place and no event, so it stays
a date of death with no incident.

ALTER TYPE ... ADD VALUE runs inside a transaction from PostgreSQL 12, so long as
the new value is not *used* in the same transaction; this migration writes no rows.

The downgrade refuses while any incident is typed OVERDOSE, as the CRASH
migration's does.

Revision ID: 9ac442b3acc6
Revises: 53921e33fe68
Create Date: 2026-11-03
"""

from alembic import op

revision = "9ac442b3acc6"
down_revision = "53921e33fe68"
branch_labels = None
depends_on = None

_WITHOUT_OVERDOSE = (
    "'SHOOTING', 'MURDER', 'FIGHT', 'BOMBING', 'ARSON', 'EXTORTION', 'KIDNAPPING', "
    "'ROBBERY', 'CRASH'"
)


def upgrade() -> None:
    op.execute("ALTER TYPE incidenttype ADD VALUE IF NOT EXISTS 'OVERDOSE'")


def downgrade() -> None:
    conn = op.get_bind()
    in_use = conn.exec_driver_sql("SELECT count(*) FROM incident WHERE type = 'OVERDOSE'").scalar()
    if in_use:
        raise RuntimeError(
            f"{in_use} incident(s) are typed OVERDOSE. Retype or delete them before "
            "downgrading; this migration will not rewrite them for you."
        )
    # Postgres cannot drop a value from an enum, so the type is rebuilt.
    op.execute(f"CREATE TYPE incidenttype_old AS ENUM ({_WITHOUT_OVERDOSE})")
    op.execute(
        "ALTER TABLE incident ALTER COLUMN type TYPE incidenttype_old "
        "USING type::text::incidenttype_old"
    )
    op.execute("DROP TYPE incidenttype")
    op.execute("ALTER TYPE incidenttype_old RENAME TO incidenttype")
