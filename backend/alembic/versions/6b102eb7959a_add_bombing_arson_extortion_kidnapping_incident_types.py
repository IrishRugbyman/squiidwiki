"""add BOMBING, ARSON, EXTORTION, KIDNAPPING to incidenttype enum

The original three values (SHOOTING, MURDER, FIGHT) were shaped by the Detroit
universe, where the street-gang record is overwhelmingly firearm violence.
Other universes need the acts that define their own milieu: bombings
(plastiquage), arson, extortion/racketeering and kidnapping all fell outside
the enum and had no representable type.

Revision ID: 6b102eb7959a
Revises: 1831260a1179
Create Date: 2026-08-20
"""

from alembic import op

revision = "6b102eb7959a"
down_revision = "1831260a1179"
branch_labels = None
depends_on = None

NEW_VALUES = ("BOMBING", "ARSON", "EXTORTION", "KIDNAPPING")


def upgrade() -> None:
    # Postgres 12+ allows ALTER TYPE ... ADD VALUE inside a transaction, as long
    # as the new value is not *used* in that same transaction. asyncpg rejects
    # multi-statement execute(), so issue one statement per value.
    for value in NEW_VALUES:
        op.execute(f"ALTER TYPE incidenttype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres cannot drop a value from an enum type, so reversing this means
    # rebuilding the type without the new labels. Any incident still carrying
    # one of them would violate the new type, so fail loudly rather than
    # silently rewriting real rows.
    labels = ", ".join(f"'{v}'" for v in NEW_VALUES)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM incident WHERE type::text IN ({labels})) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: incidents still use one of {labels}. '
                    'Retype or delete them first.';
            END IF;
        END $$;
        """
    )
    op.execute("ALTER TYPE incidenttype RENAME TO incidenttype_old")
    op.execute("CREATE TYPE incidenttype AS ENUM ('SHOOTING', 'MURDER', 'FIGHT')")
    op.execute(
        "ALTER TABLE incident ALTER COLUMN type TYPE incidenttype USING type::text::incidenttype"
    )
    op.execute("DROP TYPE incidenttype_old")
