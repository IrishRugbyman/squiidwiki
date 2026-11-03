"""Full-text search over the prose columns: biographies, set bios, alliance
descriptions, incident narratives, and source titles + notes.

Each target's document expression must match its GIN index in migration
3c7f32fad6eb character for character, or Postgres falls back to a sequential
scan. The query is parsed with ``websearch_to_tsquery``, so users get the
syntax they already know: ``"exact phrase"``, ``-excluded``, ``a or b``.

Snippets come back as segments (``[{"text", "hit"}]``) rather than HTML, so no
client ever has to inject markup built from stored text.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CONFIG = "english"

# Private-use code points as ts_headline markers: they cannot occur in the text
# being searched, so splitting on them is unambiguous.
_START = ""
_STOP = ""
_HEADLINE_OPTS = (
    f'StartSel={_START}, StopSel={_STOP}, MaxWords=30, MinWords=12, MaxFragments=2, FragmentDelimiter=" … "'
)


@dataclass(frozen=True)
class Target:
    entity_type: str
    table: str
    document: str  # SQL; must equal the index expression
    # Columns selected for the label, slug and date of a hit.
    label_sql: str
    slug_sql: str
    date_sql: str


TEXT_TARGETS: dict[str, Target] = {
    t.entity_type: t
    for t in [
        Target(
            "member",
            "member",
            "coalesce(biography, '')",
            "CASE WHEN nickname_unknown OR nickname IS NULL "
            "THEN coalesce(legal_name, 'Unknown') ELSE nickname END",
            "slug",
            "NULL::jsonb",
        ),
        Target("set", "sets", "coalesce(bio, '')", "name", "slug", "NULL::jsonb"),
        Target("alliance", "alliance", "coalesce(description, '')", "name", "slug", "NULL::jsonb"),
        Target("incident", "incident", "coalesce(narrative, '')", "type::text", "NULL", "date"),
        Target(
            "source",
            "source",
            "coalesce(title, '') || ' ' || coalesce(notes, '')",
            "title",
            "NULL",
            "published_at",
        ),
    ]
}


def _segments(headline: str) -> list[dict]:
    """Split a ts_headline result on the markers into [{text, hit}] runs."""
    out: list[dict] = []
    rest = headline
    while rest:
        i = rest.find(_START)
        if i < 0:
            out.append({"text": rest, "hit": False})
            break
        if i:
            out.append({"text": rest[:i], "hit": False})
        j = rest.find(_STOP, i + 1)
        if j < 0:  # unterminated; treat the remainder as a hit
            out.append({"text": rest[i + 1 :], "hit": True})
            break
        out.append({"text": rest[i + 1 : j], "hit": True})
        rest = rest[j + 1 :]
    return [s for s in out if s["text"]]


async def search_text(
    session: AsyncSession,
    universe_id: uuid.UUID,
    q: str,
    types: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    targets = [TEXT_TARGETS[t] for t in (types or TEXT_TARGETS) if t in TEXT_TARGETS]
    if not targets:
        return []
    parts = []
    for t in targets:
        doc = f"to_tsvector('{CONFIG}'::regconfig, {t.document})"
        parts.append(
            f"SELECT '{t.entity_type}' AS entity_type, id, {t.label_sql} AS label, "
            f"{t.slug_sql} AS slug, {t.date_sql} AS date, "
            f"ts_rank_cd({doc}, query) AS rank, "
            f"ts_headline('{CONFIG}'::regconfig, {t.document}, query, :opts) AS headline "
            f"FROM {t.table}, q WHERE universe_id = :universe_id AND {doc} @@ query"
        )
    sql = (
        f"WITH q AS (SELECT websearch_to_tsquery('{CONFIG}'::regconfig, :q) AS query) "
        + " UNION ALL ".join(f"({p})" for p in parts)
        + " ORDER BY rank DESC, label LIMIT :limit"
    )
    result = await session.execute(
        text(sql), {"q": q, "universe_id": universe_id, "opts": _HEADLINE_OPTS, "limit": limit}
    )
    return [
        {
            "entity_type": r.entity_type,
            "id": r.id,
            "label": r.label,
            "slug": r.slug,
            "date": r.date,
            "rank": float(r.rank),
            "snippet": _segments(r.headline),
        }
        for r in result.all()
    ]
