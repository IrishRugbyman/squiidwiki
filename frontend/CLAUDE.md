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

`/` and Ctrl+K open the command palette. Its open flag lives in `stores/commandPalette.ts` (`useCommandPalette`), so any page can open it; the dashboard's search field and the mobile top bar's search button do.

`hooks/useKeymap.ts` exports:
- `useGoToNavigation()` — wired in `_app.tsx`. `GO_TO_SHORTCUTS`: `g d`, `g s`, `g a`, `g m`, `g i`, `g r`, `g p`, `g x`, `g c`, `g n`. Add new routes to that list; the help dialog reads from it.
- `useEditShortcut(handler)` — call on detail pages with `() => entity && setEditing(true)`. Listens for plain `e`, ignores typing contexts and the 800ms `g`-prefix window.

## Recents (⌘K bounce-back)

`stores/recents.ts` — `useRecordRecent({type, id, slug, label})`. Detail pages call this once `entity` loads; the hook adds the active universe, and `useUniverseRecents()` lists only the current universe's entries. Adding a new detail-page entity:
1. Extend `RecentEntityType` in `stores/recents.ts`.
2. Add the icon + base route in `RECENT_ICON` / `RECENT_ROUTE` in `lib/recentRoutes.ts` (shared by the palette and the dashboard's "Jump back in" row).
3. Call `useRecordRecent(...)` from the detail page when data is loaded.

## Performance

- Heavy viz components (`SetRelationshipGraph`, `MemberTimeline`, `IncidentHeatmap`, `MunicipalityMap`) are `React.lazy()`-imported with `<Suspense>` skeleton fallbacks. New recharts/reactflow/maplibre components **must** do the same — the main chunk measured 55.6 kB gzipped on 2026-09-24; don't regress it.
- **A list page whose route file exports a shared form sheet lives in the main bundle**, because always-loaded screens import the sheet from it. The Sets and Alliances lists are split out for that reason: `_app.$universe.sets.index.tsx` keeps `validateSearch`, the form and the shared set components, and the page component is in `_app.$universe.sets.index.lazy.tsx` (`createLazyFileRoute`), its own chunk (the same for `_app.$universe.alliances.index.lazy.tsx`, `_app.$universe.sources.index.lazy.tsx`, `_app.$universe.municipalities.index.lazy.tsx`, the map (`_app.$universe.map.lazy.tsx`, which carries turf), the incident and alliance pages (`_app.$universe.incidents.$id.lazy.tsx`, `_app.$universe.alliances.$id.lazy.tsx`) and the set page, `_app.$universe.sets.$id.lazy.tsx`). Every route not split this way ships in the main bundle: there is no automatic route splitting here. Do the same before growing another such page. Set naming and color helpers are in `lib/setDisplay.ts`.
- **Detail pages share `components/detail/DetailParts.tsx`** (`PanelHeading`, `DetailRow`, `StatStrip`, `IncidentRow`, `RankBadge`) and `components/LinkifiedText.tsx` for free text with URLs. Use them on a new detail page rather than another copy.
- **Mount form sheets only while open** on detail pages (`{editing && <XFormSheet open … />}`): each sheet loads the universe's members, sets, alliances and gangs for its pickers, so a closed one still cost the page ten requests.
- **Free-text URL params go through `textParam()`** (`lib/searchParams.ts`): the router parses `?q=4822` as a number, and a string-only validator silently dropped it.
- `ApiError` (`lib/api.ts`) surfaces `status` and `code` — use `err.code` to differentiate duplicate/not_found/forbidden in forms when a specific message is needed.

## Type checking

- Always run `npm run build` before claiming done — it runs `tsc -b` (build mode) which catches unused imports and project-reference errors that `tsc --noEmit` misses. The user serves the production build, so this also produces the bundle they'll actually load.

## Frontend pitfalls

- **`?.items.find(...)` is unsafe.** Optional chaining only protects the LHS — `.find` is then called on possibly-undefined `items` during refetch windows (e.g. after the optimistic-delete invalidation). Always: `(x?.items ?? []).find(...)`. Same shape for `.map`, `.filter`, `.some`, etc.
- **Mutation hooks need UUIDs, not slugs.** The route param `$id` on detail pages can be a slug (e.g. `/members/jason`). GET endpoints accept slug-or-UUID, but PATCH/DELETE require UUID. Pass the loaded `entity.id` (or a `memberUuid` derived from it) into hooks like `useUpdateMember(id, universeId)`, never the route param. Symptom: `Input should be a valid UUID, invalid character ... at 1`.
- **`react-markdown` is NOT installed** (despite anything older docs may say). Either install it before using, or use plain text + a small URL-detection regex (see `_app.research.$id.tsx` for the pattern).
- **`isPending && variables?.id === row.id`** — for per-row mutation pending state with a single hook instance, gate the spinner on the variables payload, not just `isPending` (which would spin on every row during a mutation).
