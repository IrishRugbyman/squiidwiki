# SquiidWiki — Ideas & Improvements

Ranked roughly by impact. None of these are committed to a timeline.

---

## Data & Visualization

1. **Interactive municipality map** — Leaflet choropleth showing incident density per municipality; click a zone to filter the incidents list.
2. **Alliance relationship graph** — reactflow force-directed graph of sets within an alliance with member-count node sizing and ally/enemy edges across alliances. The set-level graph exists; this is the macro view.
3. **Member family network graph** — reactflow canvas on the member detail Family tab showing family links across multiple hops (grandparents, cousins), not just direct relations. Currently only a flat list and timeline exist.
4. **Incident heatmap / calendar density view** — overlay incident count as a heatmap on the calendar month grid. Year-view mode (12-month grid showing event density at a glance).
5. **Cross-entity timeline** — universe-level chronological feed of incidents, member status changes, and set status changes on a single horizontal axis.

## Performance & Scale

6. **List virtualization** — `@tanstack/react-virtual` for members and incidents tables when result count > 50. Without it, loading 500 members renders all DOM nodes at once.
7. **Optimistic updates** — member status change, set relationship add/remove, and source archive/unarchive should update the cache immediately and roll back on error.
8. **Prefetch on hover** — wire `router.preload()` on `mouseenter` for list rows so detail pages feel instant (`defaultPreload: 'intent'` is set globally but not wired to table rows).

## Mobile & UX

9. **Mobile card view for tables** — members, incidents, sets, and alliances list pages need a `<sm:` card layout; the current table requires horizontal scroll on mobile.
10. **Swipe-to-open sidebar** — vaul drawer with swipe gesture on mobile replacing hamburger-only open.
11. **Floating bulk-action safe area** — bulk-edit bar overlaps content on iOS Safari due to the home indicator; add `pb-[env(safe-area-inset-bottom)]`.

## Search & Filtering

12. **Saved filter presets** — name and save a filter combination (e.g., "Active shooters, 2023–2024") stored in localStorage per universe. Most useful on the incidents page.
13. **Global search expansion** — `⌘K` currently searches members and sets. Extend to incidents (by date/type), municipalities, and sources with result-type icons and section headers.
14. **Cross-member incident search** — on the incidents index, filter by participant name (the participant search builder works on create; make it a filter on the list).

## Content & Editing

15. **Inline biography editing** — replace the sheet-based biography editor with a live markdown preview split-pane (like GitHub's issue editor). `react-markdown` is already in the tree for rendering.
16. **Bulk CSV import** — drag-and-drop CSV → preview table → confirm workflow for mass-importing members or incidents.
17. **Member merge** — when duplicate records exist, a merge dialog that picks the canonical record and migrates all incident participations, family links, and source citations.

## Admin & Ops

18. **Audit log field-level diff** — `DiffBlock` shows before/after JSON blobs; a true diff render (red removed, green added per field) would be far more scannable.
19. **Real-time audit feed** — SSE or WebSocket subscription so the audit log auto-appends new entries without a manual refresh.
20. **Universe statistics dashboard** — dedicated admin page showing per-universe entity counts, last-activity date, active users, and storage size.
