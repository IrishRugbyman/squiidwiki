# SquiidWiki — Backlog

Open items only. Implemented ideas are in git history.

---

## Data model foundations

*Schema changes that unlock multiple downstream features.*

- [ ] **Street-level incident location** — `incidents.lat` / `incidents.lng` in addition to municipality FK. Municipality is too coarse for cluster analysis, heatmaps, or "all shootings within 200 m of X."
- [ ] **Set lineage / splinter relationships** — directional edge type on the existing set-relationship table (`SPLINTERED_FROM`, `MERGED_INTO`, `RENAMED_TO`). Sets are not static; the macro alliance graph misses this dimension.
- [ ] **Conflict / beef entity** — a `Conflict` row (set_a, set_b, started_on, ended_on?, summary) that incidents can link to. Lets you tell the story rather than scroll an incident list.
- [ ] **Court case entity** — links one or more incidents to charges, verdicts, sentence length. Many incidents map to one case (co-defendants); one incident can spawn many cases.
- [ ] **Funeral / memorial events** — sub-type of incident. Frequent retaliation triggers and often the only public photo of a network in one place at one time.
- [ ] **Set territory polygon** — optional GeoJSON polygon on `sets`, rendered on the map alongside the municipality choropleth. Hand-drawn or derived from K-means over incident lat/lng.
- [ ] **Member-to-member direct links (non-family)** — generic `MemberRelationship` (e.g., "co-defendants", "childhood friends", "direct rivals") that the reactflow graph can render independent of set boundaries.
- [ ] **Gang affiliation field** — new `Gang` entity (name + aliases) referenced by sets, alliances, and members. Alliances and sets can be `None` or any single gang; members cannot be `Mixed`. Needs a gang admin page and pickers on the set/alliance/member forms. Chicago-centric seed values to start (Black Disciples, Gangster Disciples, Bloods, etc.) but the model is generic.

---

## Analytics & intelligence

- [ ] **Set rivalry / beef intensity score** — dynamic score based on incident frequency and severity between two sets; displayed as a heat indicator on the set relationship graph. Extends the existing Redis computed-stats pattern.
- [ ] **Retaliation pattern view** — for each killing, show the set's response window: next incident by that set, time-to-retaliation distribution. The most "research-y" view the product can offer.
- [ ] **Network centrality dashboard** — degree, betweenness, and eigenvector centrality computed over the member-incident graph. Surfaces connectors that aren't obvious from raw kill counts. NetworkX in a nightly job; cache to Redis.
- [ ] **Co-offending analysis** — flag members who repeatedly appear together in incidents, with frequency heatmaps.
- [ ] **Survival curves by set** — Kaplan-Meier-style curves for time-to-incarceration and time-to-death per set. Visually striking with the stats infra already in place.
- [ ] **Source contradiction detector** — when two sources cite the same fact (e.g., shooter identity) with conflicting claims, flag it on the incident page. Requires per-fact citations (see Content section).
- [ ] **Animated incident heatmap over time** — scrub a year slider to redraw the choropleth. Map page already has the choropleth pieces; adding lat/lng to incidents (above) makes this trivial.
- [ ] **Temporal hotspot detection** — auto-identify time windows (e.g., "Fridays 2–4 AM") with abnormally high incident rates.
- [ ] **Location clustering** — group incidents by proximity (DBSCAN or grid-based) to reveal territorial boundaries; depends on lat/lng on incidents.
- [ ] **Member risk assessment** — composite score from incident participation, associations, and recent activity.
- [ ] **Community detection** — auto-group sets into larger coalitions using modularity optimization over the alliance/rivalry graph.
- [ ] **Incident correlation matrix** — heatmap table showing which sets/members co-occur in incidents most often.
- [ ] **Set lifecycle visualization** — chart set activity (incidents/month) over time with trend lines and key events overlaid.

---

## Content & editing

- [ ] **Per-fact citations** — let a sentence in a biography or incident narrative reference a specific source. Inline `[[source:123]]` markers rendered as superscript footnotes. Entity-scoped citations are fine for "this member exists" but useless for "this member fired the gun."
- [ ] **Member merge** — when duplicate records exist, a merge dialog picks the canonical record and migrates all incident participations, family links, and source citations.
- [ ] **Web Archive snapshot on source create** — when a `Source` URL is saved, fire a request to `web.archive.org/save/<url>` and store the resulting archived URL alongside. News links rot fast.
- [ ] **Auto-fetch source metadata** — when a URL is pasted into the source form, fetch title / byline / publish date / og-image and prefill the fields. Removes the most tedious part of citing.
- [ ] **Version history / diff view on biographies** — audit log on writes is already captured; expose it on the entity page as a "History" tab with red/green diffs.
- [ ] **"Stale data" indicators** — `last_verified_at` timestamp on Members and Sets with a subtle UI indicator if a profile hasn't been updated or involved in a new incident in over 18 months.
- [ ] **Data anomaly dashboard** — admin view flagging logical impossibilities: member linked to an incident before their birth year, member `outcome=KILLED` in 2021 but attached to a later incident in 2023, set `EXTINCT` but has recent incidents, etc.
- [ ] **Wiki-style internal links in bios** — `[[member:slug]]` / `[[set:slug]]` syntax expanded by the markdown renderer into typed links. Pairs with the inline bio editor.
- [ ] **AI-assisted bio draft from source URL** — paste a news article, get a structured proposal: name, DOB, sets, incidents to link, draft bio. User reviews before insert. Admin-only endpoint to control token spend.
- [ ] **Inline biography markdown split-pane** *(partial)* — plain-text inline edit shipped. Remaining: live markdown preview split-pane (GitHub issue-editor style); requires installing `react-markdown`.

---

## Search & discovery

- [ ] **Full-text search across biographies and source narratives** — Postgres `tsvector` + GIN index. ⌘K only matches names today; this lets you find "the kid mentioned in that 2022 article."
- [ ] **Fuzzy nickname matching (`pg_trgm`)** — trigram similarity search on `display_name` and aliases so ⌘K and participant search capture misspellings and phonetic variations ("Lil Tony" vs. "Lil Tone").
- [ ] **Radial geographic filtering** — "drop pin + radius" filter on the incidents list. Instead of hard municipality boundaries, filter by "everything within 2 miles of [coordinates/intersection]."
- [ ] **Saved search alerts** — saved filter presets already exist; add a "notify me when a new entity matches this filter" toggle, surfaced as a feed badge. SSE or polled.
- [ ] **Favorites / star entities** — quick access to frequently used entities via a sidebar section or ⌘K, separate from the recents list.

---

## Map & geo

- [ ] **Cluster markers** — when zoomed out, collapse nearby incident dots into cluster bubbles. Current "every incident as its own dot" doesn't scale past a few hundred points.
- [ ] **Geospatial incident playback** — time-slider on the map that animates incidents over a selected date range, showing how conflicts migrate geographically over months or years.
- [ ] **Territory mapping** — draw polygons on the map to define gang territories with overlap detection; complement or replace the set territory polygon derived from incident clustering.
- [ ] **Address autofill** — integrate geocoding API (Nominatim / Google) to auto-populate lat/lng from a street address when creating or editing an incident.
- [ ] **Pinned route between linked incidents** — when an incident links to a retaliation, draw the directional path between them on the map. Visual storytelling once lat/lng exists.
- [ ] **Geofenced alerts** — notify when new incidents or members are added within a custom geographic boundary.
- [ ] **Municipality boundary overlay** — shapefile import of official city/district borders displayed on the map.

# Bug

- adding a set on an alliance page should put this allaince by default in the creation form

---

## Admin & governance

- [ ] **Soft-delete with restore** — recycle bin for the last N days of deletes (admin-only). Prevents the "I just nuked the wrong member" situation.
- [ ] **Per-universe role assignment** — `UserUniverseRole` join table so a researcher can be admin in Detroit but viewer in Chicago. Today it's global `ADMIN`/`USER`.
- [ ] **Full universe export** — admin endpoint dumps a universe as JSON or SQL for backup, offline analysis, or cloning to test. Pairs with import.
- [ ] **Data completeness dashboard** — per-universe report showing % of entities missing key fields (e.g., "30% of members lack DOB").
- [ ] **Orphaned entity cleanup** — flag members with no incidents/sets, incidents with no participants, sources not linked to anything, etc.
- [ ] **Media orphan cleanup** — cross-reference the `media` table against the R2 bucket to find and purge files in R2 with no DB record and DB records pointing to deleted R2 objects.
- [ ] **Data freezing / entity lock** — lock an entity from further edits (e.g., for legal cases) with a note in the audit trail.
- [ ] **Read audit on flagged entities** — for sensitive members/sources, log read events too, not just writes.
- [ ] **Webhook on entity changes** — outbound POST on create/update/delete for downstream pipelines. Smaller scope than SSE and composable with external tools.
- [ ] **Universe statistics: last-activity / active-users / storage** *(partial)* — entity counts are shown on `/universes`. Remaining: last-activity date, active user count, storage size.

---

## Collaboration & workflow

- [ ] **Case / operation management** — group members, incidents, sets, and sources into named investigations with status (`OPEN` / `CLOSED` / `ARCHIVED`).
- [ ] **Draft / approval workflow** — non-admin users propose edits; admins approve or reject with comments. Like Wikipedia pending changes. Useful if the wiki expands to less-trusted roles.
- [ ] **Per-fact data confidence levels** — extend source reliability to entity fields: "Date of birth: VERIFIED | ALLEGED | RUMORED." Pairs with per-fact citations.
- [ ] **Threaded discussions** — per-entity comment threads (e.g., "Why was Member Y marked as DEAD?").
- [ ] **Task assignment** — create research tasks (e.g., "Verify Member X's alias") assignable to users with due dates.
- [ ] **Team activity feed** — real-time view of what other researchers are editing/viewing (opt-in).

---

## Security & access control

- [ ] **Per-entity visibility level** — `public | members | admin` flag on members, sources, and incidents. Some research is too sensitive for general accounts but should still live in the database.
- [ ] **Field-level permissions** — hide sensitive fields (e.g., addresses, phone numbers) from non-admin users.
- [ ] **Real-name redaction on export** — when exporting (PDF, CSV, universe dump), an option to replace legal names with nicknames-only.
- [ ] **Universe isolation** — restrict users to specific universes (currently all users see all universes); superseded by per-universe roles above but useful as a simpler toggle.
- [ ] **Custom validation rules** — admin-defined rules (e.g., "Members in Set A cannot have status=FREE") enforced on save.
- [ ] **Session timeout** — auto-logout after inactivity (configurable per user/role).
- [ ] **Brute-force protection** — rate-limiting on login endpoints.
- [ ] **IP allowlisting** — limit backend access to specific IPs/ranges for law enforcement deployments.

---

## Mobile & UX

- [ ] **Quick-capture mobile form** — strip the member create form to 3 essential fields (nickname, set, status) with a "more details" expand. Field research won't happen on the full sheet.
- [ ] **PWA / offline mode** — installable shell, cached universe data, queued mutations replayed on reconnect. The JSON API surface is clean enough for a service worker.
- [ ] **Keyboard shortcut help overlay** — `?` opens a modal listing every shortcut. Enough have accumulated (`g`-prefix nav, `e` to edit, ⌘K) that they need a discoverability surface.
- [ ] **Entity comparison view** — side-by-side diff of two members or incidents to spot discrepancies.
- [ ] **Column visibility presets** — save which columns are visible in tables (e.g., "Minimal" vs. "Detailed").
- [ ] **Customizable dashboards** — drag-and-drop widgets (recent incidents, member stats, map) per user.
- [ ] **Quick filter chips** — persistent filter pills at the top of list pages (e.g., "Status: DEAD") that survive navigation.
- [ ] **Bulk CSV import** — drag-and-drop CSV → preview table → confirm workflow for mass-importing members or incidents, with pre-configured templates and validation.

---

## Import / export & integration

- [ ] **Real-time audit feed** — SSE or WebSocket subscription so the audit log auto-appends new entries without a manual refresh.
- [ ] **PDF report generator** — customizable templates for printing entity profiles or incident summaries.
- [ ] **Scheduled reports** — auto-generate and email PDF/CSV reports (e.g., "Weekly Incident Summary").
- [ ] **Export to GIS formats** — Shapefiles/KML for use in external mapping tools.
- [ ] **External ID mapping** — link entities to records in other databases (e.g., "FBI ID: 12345").
- [ ] **Background job queue** — for long-running tasks (OCR, image processing, report generation) that currently block the request thread.
- [ ] **JSON-LD export** — semantic web-compatible exports for interoperability.
- [ ] **Health check endpoint** — `/health` verifying Postgres, Redis, and R2 connectivity for monitoring/uptime tools.

---

## AI-assisted

- [ ] **OCR for sources** — extract text from uploaded images/PDFs (e.g., news articles) into searchable fields.
- [ ] **Automated tagging** — NLP over biographies and incident descriptions to suggest keywords (e.g., "drive-by", "retaliation").
- [ ] **Entity linking suggestions** — "Member X was in an incident with Member Y; did you mean to add them to the same set?"
- [ ] **Face matching** — compare uploaded member photos against a gallery to detect duplicates (client-side ONNX or via external API).
- [ ] **Alias generation** — suggest possible aliases based on known nickname (e.g., "Robert" → "Bobby", "Rob").

---

## Quick wins *(low effort, high value)*

- [ ] **Entity references in text** — auto-link `@MemberName` or `#SetName` in biographies and notes to their pages.
- [ ] **Recent edits feed** — dashboard widget showing the latest changes across the universe.

---

## Partial — open tails

- [ ] **Bulk link / bulk tag** — bulk-delete shipped on all entity types. Remaining: bulk-link a source to multiple entities and bulk-tag (e.g., bulk-assign gang affiliation once that field exists).
- [ ] **Universe statistics: last-activity / active-users / storage** — listed above under Admin & governance.
