"""Trigram (pg_trgm) fuzzy matching shared by the name searches.

The searches used to be plain ``ILIKE '%q%'``, so a misspelling found nothing:
"Lil Tone" missed "Lil Tony" (the ROADMAP's example), and a duplicate one letter away from an existing
member (one syllable off) never surfaced at the moment someone was about to
create it. Every name search now keeps its substring match and adds a trigram
match on top, then ranks substring hits first and the rest by score.

The score is ``word_similarity(q, field)``: how well the query matches the
best-matching run of words in the field, from 0 to 1. Plain ``similarity`` would
punish a short query against a long name ("tone" against "lil tony" scores 0.27),
which is exactly the case a search box sees. 0.5 was picked by trying pairs the
search should and should not join: "lil tone"/"lil tony" 0.78, "marowgate"/
"marrowgate boys" 0.75 and "riverbend"/"river bend" 0.62 match; two different
five-letter names sharing their first two letters score about 0.33 and do not.

pg_trgm is installed by migration ``9065522d726a``, which also put GIN trigram
indexes on the name columns. The function form below does not use those indexes
(only the ``%``/``<%`` operators can), which is fine at this wiki's size: a
universe holds thousands of rows, not millions. If that changes, switch to
``<%`` under ``SET LOCAL pg_trgm.word_similarity_threshold``.
"""

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

# Below this the word_similarity of two names is mostly shared letters, not a
# shared name. See the module docstring for the pairs it was calibrated on.
FUZZY_THRESHOLD = 0.5

# Trigrams need something to work with: two characters produce one or two
# trigrams and match half the table. Shorter queries stay substring-only.
FUZZY_MIN_QUERY_LEN = 3


def use_fuzzy(q: str) -> bool:
    return len(q.strip()) >= FUZZY_MIN_QUERY_LEN


def word_score(q: str, column: ColumnElement) -> ColumnElement:
    """word_similarity of ``q`` against one text column, 0 when it is NULL."""
    return sa.func.word_similarity(q, sa.func.coalesce(column, ""))


def best_score(q: str, *columns: ColumnElement) -> ColumnElement:
    """The highest word_similarity of ``q`` across several columns."""
    scores = [word_score(q, c) for c in columns]
    return scores[0] if len(scores) == 1 else sa.func.greatest(*scores)


def name_variant_values(table: str) -> ColumnElement:
    """The names and initials in a ``name_variants`` column, space-joined.

    Sets and alliances hold their names in slots (``name``, ``initials``,
    ``number``). Casting the JSON to text would score the key names too, so a
    query like "num" would match every row; score the slot values only.
    """

    def slot(key: str) -> str:
        return (
            "(SELECT coalesce(string_agg(v #>> '{}', ' '), '') FROM jsonb_path_query("
            f"{table}.name_variants, '$[*].{key} ? (@.type() == \"string\")') v)"
        )

    return sa.literal_column(f"({slot('name')} || ' ' || {slot('initials')})")


def ranked_select(
    model, where: ColumnElement, substring: ColumnElement, score: ColumnElement, *tiebreak
):
    """SELECT ``model`` rows matching ``substring`` or scoring >= the threshold.

    Substring hits come first, then near-misses by descending score, then
    ``tiebreak``. Callers keep the old substring-only query for queries too short
    to fuzz (``use_fuzzy``).
    """
    exact = sa.case((substring, 1), else_=0).label("exact")
    inner = sa.select(model.id, exact, score.label("score")).where(where).subquery()
    return (
        sa.select(model)
        .join(inner, inner.c.id == model.id)
        .where((inner.c.exact == 1) | (inner.c.score >= FUZZY_THRESHOLD))
        .order_by(inner.c.exact.desc(), inner.c.score.desc(), *tiebreak)
    )
