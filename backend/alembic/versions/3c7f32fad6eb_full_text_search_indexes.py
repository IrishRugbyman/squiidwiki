"""full-text search: GIN indexes over biographies, bios, narratives and source notes

The command palette matched names only, so "the kid mentioned in that 2022
article" could not be found by what the article said. These are expression
indexes, not stored tsvector columns, so no model changes and nothing for writes
to keep in step. The query in app/crud/text_search.py must use exactly these
expressions (same regconfig, same coalesce) or Postgres will not use them.

'english' stems ("shot" / "shooting", "killed" / "killing"); nicknames are
mostly not dictionary words and pass through as they are.

Also adds the trigram index member_alias was missing: the fuzzy name search
scores member_alias.alias as well as the member columns 9065522d726a indexed.

Revision ID: 3c7f32fad6eb
Revises: 9ac442b3acc6
Create Date: 2026-11-03
"""

from alembic import op

revision = "3c7f32fad6eb"
down_revision = "9ac442b3acc6"
branch_labels = None
depends_on = None

# (index name, table, document expression). Keep in step with TEXT_TARGETS in
# app/crud/text_search.py.
INDEXES = [
    ("ix_member_biography_fts", "member", "coalesce(biography, '')"),
    ("ix_sets_bio_fts", "sets", "coalesce(bio, '')"),
    ("ix_alliance_description_fts", "alliance", "coalesce(description, '')"),
    ("ix_incident_narrative_fts", "incident", "coalesce(narrative, '')"),
    ("ix_source_text_fts", "source", "coalesce(title, '') || ' ' || coalesce(notes, '')"),
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for name, table, doc in INDEXES:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {name} ON {table} "
            f"USING gin (to_tsvector('english'::regconfig, {doc}))"
        )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_member_alias_alias_trgm ON member_alias USING gin (alias gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_member_alias_alias_trgm")
    for name, _, _ in INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
