# Frontend — CLAUDE.md

Frontend-specific guidance. The repo root `CLAUDE.md` covers cross-cutting rules, verification requirements, and the data model — read it first.

## Code Organization

```
frontend/src/
├── components/
│   ├── ui/        # shadcn/Radix primitives (button, dialog, dropdown-menu, command, …)
│   ├── icons/     # SocialIcons.tsx — inline brand SVGs (lucide dropped Facebook/Instagram/Twitter in v1.x)
│   ├── charts/    # recharts visualisations (lazy-loaded)
│   ├── graphs/    # reactflow + custom graphs (lazy-loaded)
│   ├── maps/      # maplibre municipality choropleth (lazy-loaded)
│   ├── skeletons/ # content-shape loading skeletons
│   └── *.tsx      # shared domain: Breadcrumbs, CopyButton, EmptyState, ErrorState,
│                  #   ConfirmDialog, FuzzyDate, MemberIdentity, StatusBadge, StatusToggle,
│                  #   GlobalCommandPalette, AddMemberToSetDialog, AddSetToAllianceDialog,
│                  #   AddMemberToAllianceDialog, …
├── hooks/         # useDebounce, useKeymap (useGoToNavigation, useEditShortcut), useCurrentUser
├── lib/           # api.ts (ApiError + refresh logic), queries.ts (~50 react-query hooks),
│                  # types.ts (mirrors backend enums/schemas), statusColors.ts,
│                  # incidentColors.ts, download.ts, utils.ts (cn helper)
├── routes/        # TanStack Router file-based — flat naming:
│                  # _app.tsx (layout), _app.{entity}.index.tsx (list), _app.{entity}.$id.tsx (detail)
├── stores/        # Zustand: auth.ts, universe.ts, recents.ts (all persisted to localStorage)
├── main.tsx       # QueryClient + Router root; global error-toast wiring
├── routeTree.gen.ts  # GENERATED — do not edit by hand
└── index.css      # Tailwind v4 theme tokens
```

## Shared UI primitives (reuse, don't reinvent)

- **Detail pages** must use `<Breadcrumbs>` + `<CopyButton value={window.location.href}>` in the header, and `<DetailHeaderSkeleton>` while loading.
- **List pages** use `<EmptyState>` for empty results (not inline divs), `TableRowSkeleton` / `MemberRowSkeleton` matching the real row height (prevents layout shift), `aria-sort` on sortable `th`, `aria-disabled` on pagination buttons.
- **Destructive actions** use `<ConfirmDialog impact={...}>` — always populate `impact` with the blast radius ("3 members, 12 incidents will be unlinked") so the user knows what's about to be destroyed.
- **Status colors** live in `lib/statusColors.ts` (member/set/alliance/reliability) and `lib/incidentColors.ts` (role/outcome chips). Don't duplicate Tailwind palettes per page — import from these.
- **Inline status editing** — `components/StatusToggle.tsx` exports `MemberStatusToggle`, `SetStatusToggle`, `AllianceStatusToggle`. Pair with `useUpdateMemberStatus` / `useUpdateSetStatus` / `useUpdateAllianceStatus` (single hook instance per page, takes `{id, status}` per row).
- **Forms / mutations** — the global `QueryClient` mutation `onError` already toasts the error via sonner. Only add `try/catch` around a mutation when you need custom UI state (e.g. closing a dialog, form-field errors) — don't wrap just to `toast.error()`.
- **Form sheets are exported** from their `*.index.tsx` route files (`MemberFormSheet`, `SetFormSheet`, `AllianceFormSheet`, `IncidentFormSheet`, `SourceFormSheet`, `MunicipalityFormSheet`) so detail pages and dialogs can reuse them. They accept:
  - `initial` — edit mode (calls update)
  - `copyFrom` — duplicate mode (calls create, seeded from existing entity)
  - `defaultSetId` / `defaultAllianceId` / `defaultParticipants` — prefill seeds for create mode
  - When opening dynamically, key the sheet by entity id (`key={`dup-${id}`}`) so re-opens re-seed.
- **Brand glyphs** — Facebook / Instagram / Twitter live in `components/icons/SocialIcons.tsx` (lucide v1.x removed brand icons).

## Keyboard

`hooks/useKeymap.ts` exports:
- `useGoToNavigation()` — wired in `_app.tsx`. `GO_TO_SHORTCUTS`: `g d`, `g s`, `g a`, `g m`, `g i`, `g r`, `g p`, `g x`, `g c`, `g n`. Add new routes to that list; the help dialog reads from it.
- `useEditShortcut(handler)` — call on detail pages with `() => entity && setEditing(true)`. Listens for plain `e`, ignores typing contexts and the 800ms `g`-prefix window.

## Recents (⌘K bounce-back)

`stores/recents.ts` — `useRecordRecent({type, id, slug, label})`. Detail pages call this once `entity` loads. Adding a new detail-page entity:
1. Extend `RecentEntityType` in `stores/recents.ts`.
2. Add the icon + base route in `RECENT_ICON` / `RECENT_ROUTE` maps in `GlobalCommandPalette.tsx`.
3. Call `useRecordRecent(...)` from the detail page when data is loaded.

## Performance

- Heavy viz components (`SetRelationshipGraph`, `MemberTimeline`, `IncidentsOverTime`, `ReliabilityDonut`, `MunicipalityMap`) are `React.lazy()`-imported with `<Suspense>` skeleton fallbacks. New recharts/reactflow/maplibre components **must** do the same — the main bundle is currently ~165kB gzipped; don't regress it.
- `ApiError` (`lib/api.ts`) surfaces `status` and `code` — use `err.code` to differentiate duplicate/not_found/forbidden in forms when a specific message is needed.

## Type checking

- `npx tsc --noEmit` ≠ `npm run build` — the latter runs `tsc -b` (build mode) which catches unused imports and project-reference errors the former misses. Run **both** before claiming done.

## Frontend pitfalls

- **`?.items.find(...)` is unsafe.** Optional chaining only protects the LHS — `.find` is then called on possibly-undefined `items` during refetch windows (e.g. after the optimistic-delete invalidation). Always: `(x?.items ?? []).find(...)`. Same shape for `.map`, `.filter`, `.some`, etc.
- **`react-markdown` is NOT installed** (despite anything older docs may say). Either install it before using, or use plain text + a small URL-detection regex (see `_app.research.$id.tsx` for the pattern).
- **`isPending && variables?.id === row.id`** — for per-row mutation pending state with a single hook instance, gate the spinner on the variables payload, not just `isPending` (which would spin on every row during a mutation).
