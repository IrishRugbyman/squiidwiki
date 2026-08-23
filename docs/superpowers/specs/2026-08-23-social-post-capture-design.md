# Social post capture - design

**Date:** 2026-08-23
**Status:** approved, not yet implemented

## Problem

Facebook posts and tweets are often the only evidence for a claim, and they rot.
The account goes private, the post is deleted, or (as with every Facebook URL
tried on 2026-08-23) the server simply cannot reach them: personal profiles and
`photo.php` return a login wall to any unauthenticated fetch.

The concrete case that motivated this: two RIP posts dated *17 janvier 2011*,
one of them by **"Tto Mez"**, a name on the TTO roster, were what tied the
nickname "Reggie Kush" to Reginald Pope, aged 19, killed 2011-01-16 at 18475
Prairie Street. Neither the Reddit mirror (224k comments) nor the 1105-page
WordPress mirror contained anything. That evidence existed only in a chat
transcript, and nothing in the database preserves it.

Nothing that exists today fits:

| store | why it doesn't fit |
|---|---|
| `source` (43 rows) | stores a **link, not content**. Built for published citations, and requires attaching to something, which is why it has 43 rows while the unstructured Reddit mirror has 224,146 |
| `research_note` (4 rows) | freeform, per-universe, attached to nobody, not searchable as a corpus |
| `media` | images only |

## Requirements

1. **Capture must be cheap and unattached.** Requiring a member to be chosen at
   paste time is the reason `source` is nearly empty. Posts land in an unlinked
   pool; linking happens later.
2. **Searchable as a corpus, and it must stay fast as it grows.**
3. **Joinable to members**, so evidence can be pulled per-entity.
4. **Author is a first-class column**, not buried in the text. The decisive
   signal in the motivating case was *who posted*, not what the post said.
5. **No rendering requirement.** The user explicitly does not need these on the
   public page. No UI, no visibility flags, no `npm run build`.

## Decisions

**Lives in `squiidwiki_prod`, as a SQLModel model with an Alembic migration.**

Two alternatives were rejected:

- *A separate SQLite corpus* (like `~/.cache/squiidwiki/reddit-mirror.db`) gives
  search but no joins to member rows, which is the difference between finding
  and connecting. It would also sit outside the nightly backup until explicitly
  added, defeating the purpose of preserving deletable evidence.
- *Extending `source`* overloads a table built around linked, published
  citations, and fights requirement 1.

Being in `squiidwiki_prod` means it is dumped nightly and mirrored offsite to
Falkenstein for free, via the existing `backup.sh` sweep of every database.

**It must be a real SQLModel model.** `backend/alembic/env.py` sets
`target_metadata = SQLModel.metadata` with no `include_object` filter, so any
table present in the database but absent from the models is proposed for **DROP**
by the next `alembic revision --autogenerate`. A hand-rolled table would be a
loaded gun.

## Schema

### `social_post`

| column | type | notes |
|---|---|---|
| `id` | uuid | PK |
| `universe_id` | uuid | FK, scoped like every other entity |
| `platform` | enum | `FACEBOOK` / `TWITTER` / `INSTAGRAM` / `OTHER` |
| `author_handle` | varchar, null | e.g. `linwood.mcgiver` |
| `author_display` | varchar, null | e.g. `Tto Mez` |
| `content` | text | **the only required field** |
| `posted_at` | jsonb, null | `FuzzyDate`, per project convention; often only a year is known |
| `url` | varchar, null | permalink if available |
| `captured_at` | timestamptz | defaults to now; the original may not survive |
| `notes` | varchar, null | annotations |
| `content_sha256` | char(64) | **unique per universe**, so re-pasting is a no-op rather than a duplicate |
| `created_by_id` | uuid, null | |

Plus a generated `search_tsv` tsvector over `content`, `author_display` and
`author_handle`, with a **GIN index**. This is the scaling answer: `LIKE` was
adequate for 224k Reddit rows, but a GIN index stays fast well beyond anything
pasted by hand.

`FuzzyDate` is a `TypeDecorator` already used across the schema; do not
substitute a plain `DATE`.

### `social_post_member`

Many-to-many: `(post_id, member_id)`, unique together, `ON DELETE CASCADE`.

Deliberately **not** modelled on `media`'s nullable-FK-per-entity-type pattern.
That works for media because one image belongs to one entity; a single post can
name several people. Member links only for now. Incident links can be added
later if they turn out to be wanted (YAGNI).

## Tooling

No UI. Both tools live in `research/privedatabase/tools/`, alongside the
existing seed and repair scripts, and follow their conventions (`wikiapi.py`
for API calls, `psql` for reads).

**Capture:** a CLI taking post text plus optional author, platform, date and
URL. Invoked when a post is pasted into a session. Idempotent via
`content_sha256`.

Capture writes **directly to the database**, not through an API route. Every
other write in this project goes through the API so the audit listeners record
it, but those listeners are registered per model and exist to track edits to
wiki content. No UI needs a `social_post` endpoint, and adding one to serve a
single CLI is unearned. The tradeoff, stated explicitly: captured posts produce
**no `audit_log` rows**. `captured_at` and `created_by_id` on the row itself
carry who and when, which is sufficient for research tooling. Add a route later
if a UI ever wants one.

**Sweep:** takes every member nickname and alias in a universe, runs them
against the corpus, and ranks candidate post-to-member links for review.

The sweep **proposes, never auto-links.** It will be noisy: the roster is full
of nicknames like Ace, Don, Mari, Juice, KB and G, and matching those against
free text produces garbage. Mitigations: word-boundary matching, a minimum
token length, and ranked output for human confirmation. "Free Pritch" is the
good case; "don" is not. Accepting a proposal is a separate, explicit step.

**Set-prefix normalisation happens in the matcher, never in the data.** Social
handles routinely carry the set name attached to the nickname: `Tto Ad`,
`Tto Mez`, `Tto Lante`, `JbTto Tall Tee`. Storing those as member aliases is
redundant, because the form is derivable from the set name plus the nickname
already on the row. The sweep must therefore strip any known set name for the
universe (and its variants) as a leading or trailing token from both sides
before comparing, so a post signed `Tto Ad` matches the member `Ad` with
nothing extra stored.

Aliases are reserved for what is *not* derivable: genuine spelling variants
such as `Tall Tae` for `Tall Tee`.

## Privacy

These are posts by named private individuals, and storing content is a
different act from storing a link. This lands inside an authenticated,
per-universe access-controlled database (see `docs/PRIVACY.md`) and renders
nowhere. `docs/PRIVACY.md` should gain a line covering captured social content
when this is implemented.

## Out of scope

- Screenshots and images. Text first; a post could carry an optional `media`
  link later if wanted.
- Automated scraping of any platform. Capture is manual paste only: the server
  cannot reach Facebook, and this design does not try to.
- Rendering on entity pages.
- Incident and set links.
