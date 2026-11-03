# Handoff: fuzzy name search + full-text search (branch `claude/fuzzy-fulltext-search`)

Built in a cloud session on 2026-11-03. See the CHANGELOG entry of the same date
for what and why; this file is how to try it.

## Apply locally

```bash
cd backend
.venv/bin/python -m alembic upgrade head      # prod: 3c7f32fad6eb, indexes only
DATABASE_URL_PROD='<test url>' .venv/bin/python -m alembic upgrade head
.venv/bin/python -m pytest tests/test_search.py
# restart uvicorn on :8001
cd ../frontend && npm run build
```

The migration only creates indexes (`CREATE INDEX IF NOT EXISTS`); it does not
touch rows. Downgrade drops them.

## Try it

1. ⌘K, type a name with one letter wrong: the member still comes up, after any exact
   substring matches.
2. ⌘K, type a few words from a biography or a source's notes (3+ characters):
   a "Mentioned in" group lists the hits with the matched words highlighted.
   `"exact phrase"` and `-word` work.
3. Members → Add Member, type a name close to someone already on file: an amber
   "Possible duplicate" box lists them with a score; links open in a new tab.

## For the wiki CLI

`GET /api/v1/members/similar?universe_id=&name=` returns
`[{member: MemberListItem, score}]`, best first. A `member new` pre-check could warn
on any score >= 0.5 and refuse without `--force` on 1.0.

## Test notes

The backend suite needs the test DB migrated with Alembic, not just conftest's
`create_all` (matviews and triggers come from migrations): 315 passed.
