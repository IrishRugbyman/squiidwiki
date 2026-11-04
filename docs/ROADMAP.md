# SquiidWiki - Roadmap

Forward-looking only: open items and future work. Nothing here is ticked.
When something ships, remove its line from this file; what was built and why
goes in `CHANGELOG.md`.

---

## Data model foundations

*Schema changes that unlock multiple downstream features.*

- [ ] **Conflict / beef entity**: a `Conflict` row (set_a, set_b, started_on, ended_on?, summary) that incidents can link to. Lets you tell the story rather than scroll an incident list.
- Court case entity [COMPLETE 2026-10-03]
- [ ] **Funeral / memorial events**: sub-type of incident. Frequent retaliation triggers and often the only public photo of a network in one place at one time.
- [ ] **Member-to-member direct links (non-family)**: generic `MemberRelationship` (e.g., "co-defendants", "childhood friends", "direct rivals") that the reactflow graph can render independent of set boundaries.

---

## Analytics & intelligence

- [ ] **Set rivalry / beef intensity score**: dynamic score based on incident frequency and severity between two sets; displayed as a heat indicator on the set relationship graph. Extends the existing Redis computed-stats pattern.
- [ ] **Retaliation pattern view**: for each killing, show the set's response window: next incident by that set, time-to-retaliation distribution. The most "research-y" view the product can offer.
- [ ] **Network centrality dashboard**: degree, betweenness, and eigenvector centrality computed over the member-incident graph. Surfaces connectors that aren't obvious from raw kill counts. NetworkX in a nightly job; cache to Redis.
- [ ] **Co-offending analysis**: flag members who repeatedly appear together in incidents, with frequency heatmaps.
- [ ] **Survival curves by set**: Kaplan-Meier-style curves for time-to-incarceration and time-to-death per set. Visually striking with the stats infra already in place.
- [ ] **Source contradiction detector**: when two sources cite the same fact (e.g., shooter identity) with conflicting claims, flag it on the incident page. Requires per-fact citations (see Content section).
- [ ] **Animated incident heatmap over time**: scrub a year slider to redraw the choropleth. Map page already has the choropleth pieces. Incidents carry `lat`/`lng`, but only 143 of 3,553 have them (2026-10-03).
- [ ] **Temporal hotspot detection**: auto-identify time windows (e.g., "Fridays 2–4 AM") with abnormally high incident rates.
- [ ] **Location clustering**: group incidents by proximity (DBSCAN or grid-based) to reveal territorial boundaries; limited by coordinate coverage (143 of 3,553 incidents).
- [ ] **Member risk assessment**: composite score from incident participation, associations, and recent activity.
- [ ] **Community detection**: auto-group sets into larger coalitions using modularity optimization over the alliance/rivalry graph.
- [ ] **Incident correlation matrix**: heatmap table showing which sets/members co-occur in incidents most often.
- [ ] **Set lifecycle visualization**: chart set activity (incidents/month) over time with trend lines and key events overlaid.

---

## Content & editing

- [ ] **Video links as first-class media**: a member's YouTube link currently survives only as a bare URL pasted into their biography, because `media` holds only images (`kind` is `R2` or `EXTERNAL_URL`, both rendered as pictures). Give members (and sets) a video section: store the URL on `media` with a `kind` for it, show a thumbnail grid that opens the video, and let a track carry a title and a channel. Once it exists, the bare URLs can come out of the biographies, where they break the rule that a biography says only what no column holds.

- [ ] **Sources a reader can follow** *(to refine)*: an entity's source list is unreadable today. Three parts, in order of value, with the inline markers below as the fourth:
  - [ ] **Show the evidence on private sources.** A research-file source (`research-file:` URL, kind INTERNAL) cannot be opened by a reader, so it shows as a bare title: of 124 such citations on prod (2026-10-12) one carries a quote. Each citation of a DM or a screenshot should carry the exact quoted line (`citation.quote`, already in the schema) and the cropped image (a `media` row on the source, `media.source_id` exists with no UI), rendered as the quote plus a clickable thumbnail. Backfill the existing citations from the research case files, which already hold the quoted lines, and have the research CLI fill the quote on every new citation.
  - [ ] **Short, readable source titles**: a source's display title should read like "DM, Dec 2021" or "Facebook post, 23 Nov 2019"; the long descriptive title and the technical detail move to the source's notes. Needs a short-title field or a rule for deriving one, and a pass over existing titles.
  - [ ] **Group repeating press**: when several articles report the same event, show the one that adds something (a name, a detail) and fold the rest under "+ N articles reporting the same". Needs a way to mark the lead citation per entity, or a heuristic (the article with the most specific quote).
- [ ] **Inline citation markers**: since 2026-10-04 a citation carries a locator, a quote and a note, so a record can say what each source supports. Remaining: `[[cite:<citation id>]]` markers in a biography or narrative rendered as numbered footnotes pointing at those citations.
- [ ] **Archive every source on create**: `source.archive_url` exists and is almost never filled, 15 of 976 sources on prod (2026-10-03), while 421 point at Instagram, Facebook, X, TikTok, YouTube or Reddit, where posts disappear fastest. Two paths, because the Wayback Machine cannot get past the Instagram and Facebook login walls: news, court and government URLs get a `web.archive.org/save/<url>` request and the snapshot URL in `archive_url`; social posts get a local capture (screenshot, caption text, every image) stored in R2 as `media` rows on the source (`media.source_id` already exists and has no UI), the way the research tree's Instagram fetcher already captures posts. Run it from the background job queue, never inline on the save, and backfill the 961 sources without a copy once it works.
- [ ] **Auto-fetch source metadata**: when a URL is pasted into the source form, fetch title / byline / publish date / og-image and prefill the fields. Removes the most tedious part of citing.
- [ ] **"Stale data" indicators**: `last_verified_at` timestamp on Members and Sets with a subtle UI indicator if a profile hasn't been updated or involved in a new incident in over 18 months.
- [ ] **Wiki-style internal links in bios**: `[[member:slug]]` / `[[set:slug]]` syntax expanded by the markdown renderer into typed links. Pairs with the inline bio editor.
- [ ] **AI-assisted bio draft from source URL**: paste a news article, get a structured proposal: name, DOB, sets, incidents to link, draft bio. User reviews before insert. Admin-only endpoint to control token spend.
- [ ] **Inline biography markdown split-pane** *(partial)*: plain-text inline edit shipped. Remaining: live markdown preview split-pane (GitHub issue-editor style); requires installing `react-markdown`.

---

## Search & discovery

- [ ] **Radial geographic filtering**: "drop pin + radius" filter on the incidents list. Instead of hard municipality boundaries, filter by "everything within 2 miles of [coordinates/intersection]."
- [ ] **Saved search alerts**: saved filter presets already exist; add a "notify me when a new entity matches this filter" toggle, surfaced as a feed badge. SSE or polled.
- [ ] **Favorites / star entities**: quick access to frequently used entities via a sidebar section or ⌘K, separate from the recents list.

---

## Map & geo

- [ ] **Geospatial incident playback**: time-slider on the map that animates incidents over a selected date range, showing how conflicts migrate geographically over months or years.
- [ ] **Pinned route between linked incidents**: when an incident links to a retaliation, draw the directional path between them on the map. Visual storytelling for incidents that carry coordinates.
- [ ] **Geofenced alerts**: notify when new incidents or members are added within a custom geographic boundary.

## Admin & governance

- [ ] **Soft-delete with restore**: recycle bin for the last N days of deletes (admin-only). Prevents the "I just nuked the wrong member" situation.
- [ ] **Per-universe role assignment**: `UserUniverseRole` join table so a researcher can be admin in Detroit but viewer in Chicago. Today it's global `ADMIN`/`USER`.
- [ ] **Full universe export**: admin endpoint dumps a universe as JSON or SQL for backup, offline analysis, or cloning to test. Pairs with import.
- [ ] **Data completeness dashboard**: per-universe report showing % of entities missing key fields (e.g., "30% of members lack DOB").
- [ ] **Orphaned entity cleanup**: flag members with no incidents/sets, incidents with no participants, sources not linked to anything, etc.
- [ ] **Media orphan cleanup**: cross-reference the `media` table against the R2 bucket to find and purge files in R2 with no DB record and DB records pointing to deleted R2 objects.
- [ ] **Data freezing / entity lock**: lock an entity from further edits (e.g., for legal cases) with a note in the audit trail.
- [ ] **Read audit on flagged entities**: for sensitive members/sources, log read events too, not just writes.
- [ ] **Webhook on entity changes**: outbound POST on create/update/delete for downstream pipelines. Smaller scope than SSE and composable with external tools.
- [ ] **Duplicate-name guard on set create**: the set form accepts a name that differs from an existing set's only by spaces or hyphens ("CashGang" and "Cash Gang"), and so mints a duplicate. Refuse, or warn, when a new name or variant equals an existing one with spaces and hyphens removed, and refuse outright when it matches two. The research CLI's resolver has done this since 2026-10-09; the API and the form do not.
- [ ] **Universe statistics: last-activity / active-users / storage** *(partial)*: entity counts are shown on `/universes`. Remaining: last-activity date, active user count, storage size.

---

## Collaboration & workflow

- [ ] **Case / operation management**: group members, incidents, sets, and sources into named investigations with status (`OPEN` / `CLOSED` / `ARCHIVED`).
- [ ] **Draft / approval workflow**: non-admin users propose edits; admins approve or reject with comments. Like Wikipedia pending changes. Useful if the wiki expands to less-trusted roles.
- [ ] **Per-fact data confidence levels**: extend source reliability to entity fields: "Date of birth: VERIFIED | ALLEGED | RUMORED." Pairs with per-fact citations.
- [ ] **Threaded discussions**: per-entity comment threads (e.g., "Why was Member Y marked as DEAD?").
- [ ] **Task assignment**: create research tasks (e.g., "Verify Member X's alias") assignable to users with due dates.
- [ ] **Team activity feed**: real-time view of what other researchers are editing/viewing (opt-in).

---

## Security & access control

- [ ] **Per-entity visibility level**: `public | members | admin` flag on members, sources, and incidents. Some research is too sensitive for general accounts but should still live in the database.
- [ ] **Field-level permissions**: hide sensitive fields (e.g., addresses, phone numbers) from non-admin users.
- [ ] **Real-name redaction on export**: when exporting (PDF, CSV, universe dump), an option to replace legal names with nicknames-only.
- [ ] **Universe isolation**: restrict users to specific universes (currently all users see all universes); superseded by per-universe roles above but useful as a simpler toggle.
- [ ] **Custom validation rules**: admin-defined rules (e.g., "Members in Set A cannot have status=FREE") enforced on save.
- [ ] **Session timeout**: auto-logout after inactivity (configurable per user/role).
- [ ] **Brute-force protection**: rate-limiting on login endpoints.
- [ ] **IP allowlisting**: limit backend access to specific IPs/ranges for law enforcement deployments.

---

## Mobile & UX

- [ ] **Quick-capture mobile form**: strip the member create form to 3 essential fields (nickname, set, status) with a "more details" expand. Field research won't happen on the full sheet.
- [ ] **PWA / offline mode**: installable shell, cached universe data, queued mutations replayed on reconnect. The JSON API surface is clean enough for a service worker.
- [ ] **Entity comparison view**: side-by-side diff of two members or incidents to spot discrepancies.
- [ ] **Column visibility presets**: save which columns are visible in tables (e.g., "Minimal" vs. "Detailed").
- [ ] **Customizable dashboards**: drag-and-drop widgets (recent incidents, member stats, map) per user.
- [ ] **Quick filter chips**: persistent filter pills at the top of list pages (e.g., "Status: DEAD") that survive navigation.
- [ ] **Bulk CSV import**: drag-and-drop CSV → preview table → confirm workflow for mass-importing members or incidents, with pre-configured templates and validation.

---

## Import / export & integration

- [ ] **Real-time audit feed**: SSE or WebSocket subscription so the audit log auto-appends new entries without a manual refresh.
- [ ] **PDF report generator**: customizable templates for printing entity profiles or incident summaries.
- [ ] **Scheduled reports**: auto-generate and email PDF/CSV reports (e.g., "Weekly Incident Summary").
- [ ] **Export to GIS formats**: Shapefiles/KML for use in external mapping tools.
- [ ] **External ID mapping**: link entities to records in other databases (e.g., "FBI ID: 12345").
- [ ] **Background job queue**: for long-running tasks (OCR, image processing, report generation) that currently block the request thread.
- [ ] **JSON-LD export**: semantic web-compatible exports for interoperability.

---

## AI-assisted

- [ ] **OCR for sources**: extract text from uploaded images/PDFs (e.g., news articles) into searchable fields.
- [ ] **Automated tagging**: NLP over biographies and incident descriptions to suggest keywords (e.g., "drive-by", "retaliation").
- [ ] **Entity linking suggestions**: "Member X was in an incident with Member Y; did you mean to add them to the same set?"
- [ ] **Face matching**: compare uploaded member photos against a gallery to detect duplicates (client-side ONNX or via external API).
- [ ] **Read a document into proposed entities, cheaply and checkably**: proven in the research tree's CLI (2026-10-08) and worth bringing into the app as an admin tool. Claude Haiku 5.5 reads a pasted article, filing or thread in ~12,000-character parts and returns one claim per named person or crew, each with an exact extract; code, not the model, then checks that every extract occurs in the text (compared on letters and digits, since PDF text breaks words) and matches names to existing rows by whole name only, so the result splits people already on file from new ones. Measured: about $0.002 per part, $0.11 for 67 press and court documents, 15 of 753 extracts failing the quote check. Nothing is written without a person reading each claim against its passage. In conversations the model still credits one speaker with the other's question, so a transcript needs the speaker marked and checked.
- [ ] **Alias generation**: suggest possible aliases based on known nickname (e.g., "Robert" → "Bobby", "Rob").

---

## Quick wins *(low effort, high value)*

- [ ] **Entity references in text**: auto-link `@MemberName` or `#SetName` in biographies and notes to their pages.
- [ ] **Recent edits feed (global)** *(partial)*: per-set activity feed shipped. Remaining: a universe-wide dashboard widget aggregating latest changes across all entities.
- [ ] **Migration dry-run against a throwaway DB**: always test an Alembic migration on a copy before it touches prod, and verify it does not alter existing data, not just that it applies.

---

## Performance

*Investigated 2026-05-05. Lists are the slowest pages; thumbnails already use pre-resized variants + `loading="lazy"`, so they're not the bottleneck. The two real culprits:*

- [ ] **Presign cache misses concurrently**: signed URLs are now cached in-process for nearly their lifetime (`app/core/storage.py`), so warm list renders skip signing. Cold ones still sign serially: `_attach_photos_generic` in `crud/media.py` awaits `signed_get_url()` per row, twice (full and thumb). `asyncio.gather()` the misses. Only worth it if first loads after a restart are noticeably slow.
- [ ] **Composite `(universe_id, created_at DESC)` indexes**: list queries (`crud/member.py:216`, `crud/gang_set.py:174`, `crud/incident.py:186`, alliance crud) order by `created_at DESC, id DESC` scoped to a universe, but only single-column indexes exist. Postgres scans the whole universe partition and sorts before paginating. Add `ix_<table>_universe_created_at` on member, sets, alliance, incident via Alembic. Painful once a universe has >5k rows; defer until data volume justifies it.

---

## Partial: open tails

- [ ] **Bulk link / bulk tag**: bulk-delete shipped on all entity types. Remaining: bulk-link a source to multiple entities and bulk-tag (e.g., bulk-assign a gang or a set to many members).
- [ ] **Universe statistics: last-activity / active-users / storage**: listed above under Admin & governance.
