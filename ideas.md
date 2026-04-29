# SquiidWiki — Ideas & Improvements

Ranked roughly by impact. None of these are committed to a timeline.

---

## Data & Visualization

- [x] **Alliance relationship graph** — reactflow force-directed graph of sets within an alliance with member-count node sizing and ally/enemy edges across alliances. The set-level graph exists; this is the macro view.
- [x] **Member family network graph** — reactflow canvas on the member detail Family tab showing family links across multiple hops (grandparents, cousins), not just direct relations. Currently only a flat list and timeline exist.
- [x] **Incident heatmap / calendar density view** — overlay incident count as a heatmap on the calendar month grid. Year-view mode (12-month grid showing event density at a glance).
- [x] **Cross-entity timeline** — universe-level chronological feed of incidents, member status changes, and set status changes on a single horizontal axis.
- [x] **Map click → filter incidents list** — clicking a municipality on the map currently navigates to its detail page; a "filter incidents in this zone" alternative would make the map a real exploration tool.

## Performance & Scale

- [x] **List virtualization** — `@tanstack/react-virtual` for members and incidents tables when result count > 50. Without it, loading 500 members renders all DOM nodes at once.
- [x] **Optimistic updates** — extend the pattern beyond `useDeleteSet` (the only mutation with `onMutate`/rollback today): member status change, set relationship add/remove, and source archive/unarchive should update the cache immediately and roll back on error.

## Mobile & UX

- [X] **Mobile card view for tables** — list pages currently hide columns at narrow widths (`hidden sm:table-cell`); a true `<sm:` card layout would read better than a 2-column stub table.
- [x] **Swipe-to-open sidebar** — vaul drawer with swipe gesture on mobile replacing hamburger-only open.

## Search & Filtering

- [x] **Saved filter presets** — name and save a filter combination (e.g., "Active shooters, 2023–2024") stored in localStorage per universe. Most useful on the incidents page.
- [x] **⌘K palette: extend to municipalities and sources** — palette already searches members/sets/alliances/incidents with section headers and result-type icons; municipalities and sources are missing.
- [x] **Filter incidents by participant name** — the participant search builder works on incident create; make it a filter on the list page too.

## Content & Editing

- [x] **Inline biography editing** — replace the sheet-based biography editor with a live markdown preview split-pane (like GitHub's issue editor). `react-markdown` is already in the tree for rendering. _(Plain-text inline edit + Save/Cancel shipped on member detail Bio tab; markdown split-pane preview deferred — `react-markdown` is not yet installed.)_
- [x] **Incident-driven member death workflow** — saving an incident with a participant `outcome=KILLED` auto-sets `member.status=DEAD`, copies `incident.date` to `member.date_of_death`, and stores a `member.death_incident_id` FK. Member detail page shows a prominent "Killed in incident" card linking back. First-death-wins (no override on the second incident); no auto-revert on un-kill (manual member edit handles undo). FK is `ON DELETE SET NULL` so deleting an incident gracefully unlinks. Replaces the old create-only `deathPrompts` flow.
- [ ] **Member merge** — when duplicate records exist, a merge dialog that picks the canonical record and migrates all incident participations, family links, and source citations.
- [x] **Member social profiles** — Facebook / Instagram / Twitter inputs in the member form (handle or URL), auto-linked on the detail page with brand glyphs.

## Media & Storage

- [ ] **Image hosting for members & incidents** — currently no first-class image storage; mugshots, incident photos, and source screenshots have nowhere to live. Proposed approach:
  - **Provider: Cloudflare R2** — 10 GB free, **zero egress fees**, S3-compatible (any S3 SDK works from FastAPI), no surprise bandwidth bills. Runner-up: Cloudinary (25 GB + 25 GB bandwidth + on-the-fly transforms, but credit system meters transforms+bandwidth together — a popular page can burn through it fast). Avoid imgur/ImgBB (TOS issues for this content, hotlink rot). Supabase Storage (1 GB) is too small.
  - **Backend model: `media` table** keyed by `(entity_type, entity_id)` so a single member/incident/source can hold multiple images. Columns: `id`, `universe_id`, `entity_type`, `entity_id`, `r2_key`, `original_filename`, `content_type`, `size_bytes`, `width`, `height`, `caption`, `uploaded_by_user_id`, `uploaded_at`. Indexed on `(entity_type, entity_id)`.
  - **Access control: signed URLs via JWT-gated endpoint** — frontend never gets raw R2 URLs. `GET /api/v1/media/{id}` checks auth + universe scoping, then returns a short-lived presigned URL (or proxies the bytes for small images). Upload via `POST /api/v1/media` returning a presigned PUT, or direct multipart through FastAPI for simplicity in v1.
  - **Frontend: image gallery component** on member detail (mugshot prominence + gallery), incident detail (scene/aftermath photos), source detail (screenshot of the article/post). Drag-and-drop upload, paste-from-clipboard, client-side resize before upload to cap storage.
  - **Audit:** every upload + delete writes to the existing audit log (entity_type=`media`).
  - **Open questions before implementing:** (1) image size cap & whether to generate thumbnails server-side or rely on CSS sizing; (2) whether mugshot is a first-class `member.primary_photo_id` FK or just "the first media row"; (3) prod vs test DB — R2 bucket per environment or shared bucket with `env/` prefix.

## Admin & Ops

- [x] **Universe statistics dashboard** — dedicated admin page showing per-universe entity counts, last-activity date, active users, and storage size. _(Per-universe entity counts shipped inline on the /universes page; last-activity / active-users / storage size still open — they'd need new backend fields.)_

## Cross-entity "Add X from related Y"

Pattern: a button on entity Y's detail page that opens a picker (existing) **or** a prefilled create form (new), so the relationship is wired up automatically.

- [x] **Set detail → Add Member** — picker of existing members + "Create new" that prefills `set_ids` with this set.
- [x] **Alliance detail → Add Set** — sets tab has no add. Picker of universe sets not yet in this alliance + create-new option.
- [x] **Alliance detail → Add Member** — same picker/create pattern on the members tab.
- [x] **Incident detail → Add Participant** — inline picker for member + role + outcome; create-new fallback prefills the sets seen in the incident.
- [x] **Incident detail → Add Source** — no sources tab on incident detail today; add the tab with attach-existing / create-new.
- [x] **Member detail → Add Incident** — incidents tab is read-only; new incident prefilled with this member as a participant.
- [x] **Member detail → Add Family relative** — family tab is view-only; mirror the set-relationship dialog.
- [x] **Source detail → Attach to incident/member** — reverse-direction linker (sources are only referenced from elsewhere today).
- [x] **Municipality detail → Create Set/Incident here** — location prefilled with this municipality.

## Forms & data-entry shortcuts

- [x] **Inline status toggle in list tables** — flip member/set/alliance status without opening the full edit sheet (today only the bulk-action bar can change member status).
- [x] **Auto-suggest participants on incident create** — once location + sets are chosen, suggest members from those sets. The current participant search only matches by name.
- [x] **Paste-a-URL → save as Source** — when a URL is pasted into a narrative/bio textarea, prompt "Save as source linked to this entity?".
- [x] **Duplicate entity action** (sets and members) — useful when a crew splits or you're tracking aliases.
- [x] **Keyboard `e` to edit current entity** — action shortcut to pair with the existing `g`-prefixed navigation.

## Research / notebook

- [x] **Research notebook** — sidebar tab + per-universe notes (title + freeform text, URLs auto-link). Plain-text MVP; markdown editor is a future upgrade.

## Smaller polish

- [x] **Bulk actions for sets / incidents / sources / alliances** — the floating bulk bar exists for members; extend it (multi-select to bulk-link a source, bulk-tag, or bulk-delete with one ConfirmDialog). _(Bulk-delete shipped on all four; bulk-link/bulk-tag still open as follow-ups.)_
- [x] **Recently viewed entities at the top of ⌘K** — fast bounce-back during research.
- [x] **Map markers → side-sheet preview** — quick-look without leaving the map page.
- [x] **Print/export single member profile** — PDF or markdown export for offline sharing.


# NOT YET (OR LATER)

- [ ] **Bulk CSV import** — drag-and-drop CSV → preview table → confirm workflow for mass-importing members or incidents.
- [ ] **Real-time audit feed** — SSE or WebSocket subscription so the audit log auto-appends new entries without a manual refresh.
