import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Download, Mic, Pencil, Plus, Rat, Search, Users, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AffiliationCombobox } from '@/components/members/MemberFormSheet/pickers/AffiliationCombobox'
import { Skeleton } from '@/components/ui/skeleton'
import { useAllMembers, useMemberSearch, useAllSets, useBulkMemberStatus } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import { currentAffiliations, primaryAffiliation } from '@/lib/utils'
import { useDebounce } from '@/hooks/useDebounce'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { MEMBER_STATUS_CHIP_ACTIVE, MEMBER_STATUS_DOT, MEMBER_STATUS_ORDER } from '@/lib/statusColors'
import {
  MemberAvatar,
  MemberFormSheet,
  EditMemberSheet,
} from '@/components/members/MemberFormSheet'
import type { MemberListItem, MemberStatus } from '@/lib/types'
import { textParam } from '@/lib/searchParams'

// Re-export so existing import paths keep working.
export {
  MemberFormSheet,
  familyDictToEntries,
  familyEntriesToDict,
  FAMILY_ROLES,
  ROLE_LABEL,
  ROLE_LABEL_PLURAL,
  MAX_PARENTS,
} from '@/components/members/MemberFormSheet'
export type { FamilyRole, FamilyEntry } from '@/components/members/MemberFormSheet'

/* ────────────────────────────────────────────────────────────────────────────
   The list works on the whole universe, not on a page of it.

   It used to hold one cursor page of 50 and filter, sort and count inside that
   page: "LOCKED 110" on the chip, then a handful of rows, because only the
   locked members among the first 50 were there to show. "Load more" replaced
   the page instead of extending it, so "Showing 50 of …" never moved, and the
   total never printed at all because the endpoint returns `total: null`.

   Now every member is fetched once (useAllMembers follows the cursor to the
   end, and the dashboard and calendar share its cache), and filter, sort and
   counts are exact and instant. The table is virtualised; the phone list grows
   in steps. Filters live in the URL, so Back from a member lands on the same
   filtered, sorted list, and other pages can link to one.
   ──────────────────────────────────────────────────────────────────────── */

type SortKey = 'name' | 'status' | 'set'

interface MembersSearch {
  q?: string
  status?: MemberStatus
  set?: string
  sort?: SortKey
  order?: 'asc' | 'desc'
}

const ALL_STATUSES: MemberStatus[] = MEMBER_STATUS_ORDER
const SORT_KEYS: SortKey[] = ['name', 'status', 'set']
const MOBILE_STEP = 100

export const Route = createFileRoute('/_app/members/')({
  validateSearch: (s: Record<string, unknown>): MembersSearch => ({
    q: textParam(s.q),
    status: typeof s.status === 'string' && (ALL_STATUSES as string[]).includes(s.status) ? (s.status as MemberStatus) : undefined,
    set: typeof s.set === 'string' && s.set ? s.set : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as SortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
  }),
  component: MembersPage,
})

// ─── Status styling ───────────────────────────────────────────────────────────

const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

function primarySetName(m: MemberListItem): string {
  return primaryAffiliation(m.affiliations)?.set_name ?? ''
}

// ─── Row pieces shared by table and cards ─────────────────────────────────────

function MemberName({ member }: { member: MemberListItem }) {
  const isDead = member.status === 'DEAD'
  return (
    <>
      <span className={`font-medium ${isDead ? 'text-zinc-400' : 'text-white'}`}>{member.display_name}</span>
      {member.is_rapper && <Mic aria-label="Rapper" className="ml-1.5 inline h-3 w-3 align-baseline text-fuchsia-400" />}
      {member.is_snitch && <Rat aria-label="Snitch" className="ml-1.5 inline h-3 w-3 align-baseline text-amber-400" />}
      {member.aliases && member.aliases.length > 0 && (
        <span className="mt-0.5 block truncate text-[11px] text-zinc-400">
          {member.aliases.slice(0, 3).join(' · ')}
        </span>
      )}
    </>
  )
}

function SetChips({ member }: { member: MemberListItem }) {
  const current = currentAffiliations(member.affiliations)
  const primary = primaryAffiliation(member.affiliations)
  if (!primary) return <span className="text-xs text-zinc-500">-</span>
  const others = current.filter((a) => a.set_id !== primary.set_id)
  return (
    <span className="inline-flex min-w-0 flex-wrap items-center gap-1">
      <Link
        to="/sets/$id"
        params={{ id: primary.set_slug ?? primary.set_id }}
        className="inline-flex max-w-full items-center truncate rounded-full bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-violet-400"
      >
        {primary.set_name}
      </Link>
      {others.length > 0 && (
        <span
          className="inline-flex items-center rounded-full bg-zinc-800/40 px-1.5 py-0.5 text-[10px] text-zinc-400"
          title={others.map((a) => a.set_name).join(', ')}
        >
          +{others.length}
        </span>
      )}
    </span>
  )
}

/** Placeholder row laid out on the table's own five columns, at the real row height. */
function RowSkeleton() {
  return (
    <tr aria-hidden className="h-[57px]">
      <td className="px-3"><Skeleton className="h-3.5 w-3.5 rounded-sm" /></td>
      <td className="px-3">
        <span className="flex items-center gap-3">
          <Skeleton className="h-7 w-7 shrink-0 rounded-full" />
          <Skeleton className="h-3.5 w-32" />
        </span>
      </td>
      <td className="px-3"><Skeleton className="h-5 w-24 rounded-full" /></td>
      <td className="px-3"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td />
    </tr>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

function MembersPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const search = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })
  const statusFilter = search.status ?? null
  const setFilter = search.set ?? ''
  const sortKey: SortKey = search.sort ?? 'name'
  const sortDir = search.order ?? 'asc'

  // The field stays local for instant typing; the URL follows, debounced, with
  // `replace` so every keystroke is not a history entry.
  const [q, setQ] = useState(search.q ?? '')
  const debouncedQ = useDebounce(q.trim(), 200)
  useEffect(() => {
    if ((search.q ?? '') === debouncedQ) return
    navigate({ search: (prev) => ({ ...prev, q: debouncedQ || undefined }), replace: true })
  }, [debouncedQ, search.q, navigate])

  const [creating, setCreating] = useState(false)
  const [editingMemberId, setEditingMemberId] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkStatus, setBulkStatus] = useState<MemberStatus>('FREE')
  const [mobileLimit, setMobileLimit] = useState(MOBILE_STEP)
  const bulkUpdate = useBulkMemberStatus(universe?.id ?? '')

  const { data, isLoading } = useAllMembers(universe?.id ?? null)
  const { data: searchResults, isFetching: searchFetching } = useMemberSearch(universe?.id ?? null, debouncedQ)
  const { data: setsData } = useAllSets(universe?.id ?? null)

  const allMembers = useMemo(() => data?.items ?? [], [data])
  const isSearching = debouncedQ.length >= 2

  // Search runs server-side (nickname, legal name and every alias), then its
  // hits are read back from the full list so rows carry photos and the same
  // shape either way.
  const searched = useMemo(() => {
    if (!isSearching) return allMembers
    const hits = new Set((searchResults ?? []).map((m) => m.id))
    return allMembers.filter((m) => hits.has(m.id))
  }, [allMembers, isSearching, searchResults])

  const setScoped = useMemo(
    () => setFilter
      ? searched.filter((m) => currentAffiliations(m.affiliations).some((a) => a.set_id === setFilter))
      : searched,
    [searched, setFilter],
  )

  // Chip counts reflect search and set, not the status chip itself, so each
  // chip says what clicking it would show.
  const statusCounts = useMemo(() => {
    const counts: Partial<Record<MemberStatus, number>> = {}
    for (const m of setScoped) counts[m.status] = (counts[m.status] ?? 0) + 1
    return counts
  }, [setScoped])

  const items = useMemo(() => {
    const list = statusFilter ? setScoped.filter((m) => m.status === statusFilter) : setScoped
    const dir = sortDir === 'asc' ? 1 : -1
    const byName = (a: MemberListItem, b: MemberListItem) =>
      a.display_name.localeCompare(b.display_name, undefined, { sensitivity: 'base', numeric: true })
    return [...list].sort((a, b) => {
      if (sortKey === 'status') {
        const d = MEMBER_STATUS_ORDER.indexOf(a.status) - MEMBER_STATUS_ORDER.indexOf(b.status)
        return d * dir || byName(a, b)
      }
      if (sortKey === 'set') {
        const as = primarySetName(a)
        const bs = primarySetName(b)
        // Setless members sink to the bottom whichever way the column sorts.
        if (!as !== !bs) return as ? -1 : 1
        return as.localeCompare(bs, undefined, { sensitivity: 'base' }) * dir || byName(a, b)
      }
      return byName(a, b) * dir
    })
  }, [setScoped, statusFilter, sortKey, sortDir])

  // Selection only ever covers rows the current filters show.
  useEffect(() => {
    setSelected((prev) => {
      if (prev.size === 0) return prev
      const visible = new Set(items.map((m) => m.id))
      const next = new Set([...prev].filter((id) => visible.has(id)))
      return next.size === prev.size ? prev : next
    })
    setMobileLimit(MOBILE_STEP)
  }, [items])

  const tableScrollRef = useRef<HTMLDivElement | null>(null)
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 57,
    overscan: 10,
  })
  const virtualRows = rowVirtualizer.getVirtualItems()
  const padTop = virtualRows[0]?.start ?? 0
  const padBottom = rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)

  if (!universe) return <NoUniverse />

  const listLoading = isLoading || (isSearching && !searchResults)
  const hasFilters = !!statusFilter || !!setFilter
  const hasSelection = selected.size > 0

  function patch(next: Partial<MembersSearch>) {
    navigate({ search: (prev) => ({ ...prev, ...next }), replace: true })
  }

  function clearFilters() {
    patch({ status: undefined, set: undefined })
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) patch({ order: sortDir === 'asc' ? 'desc' : 'asc' })
    else patch({ sort: key === 'name' ? undefined : key, order: undefined })
  }

  function ariaSort(key: SortKey) {
    return sortKey === key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'
  }

  function sortGlyph(key: SortKey) {
    return sortKey === key ? (sortDir === 'asc' ? '↑' : '↓') : '↕'
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    setSelected(selected.size === items.length ? new Set() : new Set(items.map((m) => m.id)))
  }

  async function applyBulkStatus() {
    if (selected.size === 0) return
    const count = selected.size
    try {
      await bulkUpdate.mutateAsync({ member_ids: Array.from(selected), status: bulkStatus })
      toast.success(`Updated ${count} member${count === 1 ? '' : 's'} to ${bulkStatus}`)
      setSelected(new Set())
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Bulk update failed')
    }
  }

  function exportFilename() {
    const date = new Date().toISOString().slice(0, 10)
    return `members-${universe!.slug}-${date}.csv`
  }

  const emptyState = (
    <div className="flex flex-col items-center py-14 text-center">
      <Users className="mb-3 h-8 w-8 text-zinc-500" />
      <p className="text-sm text-zinc-400">
        {isSearching ? `No members match “${debouncedQ}”` : hasFilters ? 'No members match these filters' : 'No members yet'}
      </p>
      {!isSearching && !hasFilters && (
        <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 transition-colors hover:text-violet-300">Add the first member →</button>
      )}
      {(hasFilters || isSearching) && (
        <button
          onClick={() => { setQ(''); navigate({ search: {}, replace: true }) }}
          className="mt-2 text-xs text-violet-400 transition-colors hover:text-violet-300"
        >
          Clear search and filters
        </button>
      )}
    </div>
  )

  const shownCount = listLoading ? null : items.length

  return (
    <div className={hasSelection ? 'pb-28' : 'pb-8'}>
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-white">Members</h1>
          <p className="mt-1 text-xs text-zinc-400" aria-live="polite">
            {isLoading
              ? 'Loading…'
              : shownCount === allMembers.length
                ? `${allMembers.length.toLocaleString()} members`
                : `${(shownCount ?? 0).toLocaleString()} of ${allMembers.length.toLocaleString()} members`}
          </p>
        </div>
        <Button size="sm" onClick={() => setCreating(true)}>
          <Plus className="mr-1.5 h-4 w-4" />Add member
        </Button>
      </div>

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] max-w-md flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            className="h-9 pl-8 pr-8 text-sm"
            placeholder="Search name, legal name or alias…"
            aria-label="Search members"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape' && q) { e.stopPropagation(); setQ('') } }}
          />
          {q && (
            <button
              type="button"
              aria-label="Clear search"
              onClick={() => setQ('')}
              className="absolute right-1.5 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-white"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
          {searchFetching && isSearching && (
            <span className="absolute -bottom-0.5 left-2 right-2 h-px animate-pulse bg-violet-500/60" aria-hidden />
          )}
        </div>
        <div className="w-48">
          <AffiliationCombobox
            label="Set"
            value={setFilter}
            onChange={(v) => patch({ set: v || undefined })}
            items={(setsData?.items ?? []).map((s) => ({ id: s.id, name: s.name }))}
            placeholder="All sets"
          />
        </div>
        <Button
          variant="outline" size="sm" className="h-9"
          onClick={() => downloadCsv(`/members/?universe_id=${universe.id}&format=csv`, exportFilename())}
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />Export all
        </Button>
      </div>

      {/* Status chips */}
      <div className="mb-3 flex min-h-[26px] flex-wrap gap-1.5">
        {!listLoading && ALL_STATUSES.filter((s) => (statusCounts[s] ?? 0) > 0 || statusFilter === s).map((s) => {
          const active = statusFilter === s
          return (
            <button
              key={s}
              onClick={() => patch({ status: active ? undefined : s })}
              aria-pressed={active}
              className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 ${
                active ? MEMBER_STATUS_CHIP_ACTIVE[s] : 'border-zinc-800 bg-zinc-900/40 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200'
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${MEMBER_STATUS_DOT[s]}`} />
              {titleCase(s)}
              <span className="tabular-nums opacity-80">{statusCounts[s] ?? 0}</span>
            </button>
          )
        })}
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-400 transition-colors hover:text-white"
          >
            <X className="h-3 w-3" /> Clear filters
          </button>
        )}
      </div>

      {/* Table (sm and up). Always virtualised: the whole universe is in it. */}
      <div
        ref={tableScrollRef}
        className="hidden overflow-y-auto rounded-lg border border-zinc-800 sm:block"
        style={{ maxHeight: 'calc(100dvh - 15rem)' }}
      >
        <table className="w-full table-fixed text-sm">
          <colgroup>
            <col className="w-10" />
            <col />
            <col className="w-[34%]" />
            <col className="w-28" />
            <col className="w-12" />
          </colgroup>
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-zinc-800 bg-zinc-900/95 backdrop-blur">
              <th className="px-3 py-2.5" scope="col">
                <input
                  id="members-select-all"
                  type="checkbox"
                  aria-label="Select all shown members"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={toggleAll}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              {([['name', 'Name'], ['set', 'Set'], ['status', 'Status']] as const).map(([key, label]) => (
                <th key={key} className="px-3 py-2.5 text-left" scope="col" aria-sort={ariaSort(key)}>
                  <button
                    onClick={() => toggleSort(key)}
                    className={`flex items-center gap-1 text-xs font-medium transition-colors hover:text-white focus-visible:text-white focus-visible:outline-none ${sortKey === key ? 'text-zinc-200' : 'text-zinc-400'}`}
                  >
                    {label} <span className="text-zinc-500" aria-hidden>{sortGlyph(key)}</span>
                  </button>
                </th>
              ))}
              <th className="px-3 py-2.5" scope="col"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {listLoading && Array.from({ length: 10 }).map((_, i) => <RowSkeleton key={i} />)}
            {!listLoading && items.length === 0 && (
              <tr><td colSpan={5}>{emptyState}</td></tr>
            )}
            {!listLoading && padTop > 0 && <tr aria-hidden><td colSpan={5} style={{ height: padTop }} /></tr>}
            {!listLoading && virtualRows.map((vRow) => {
              const member = items[vRow.index]
              const isSelected = selected.has(member.id)
              return (
                <tr
                  key={member.id}
                  ref={rowVirtualizer.measureElement}
                  data-index={vRow.index}
                  className={`group transition-colors hover:bg-zinc-900/60 ${isSelected ? 'bg-violet-950/25' : ''}`}
                >
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      aria-label={`Select ${member.display_name}`}
                      checked={isSelected}
                      onChange={() => toggleSelect(member.id)}
                      className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                    />
                  </td>
                  <td className="p-0">
                    <Link
                      to="/members/$id"
                      params={{ id: member.slug ?? member.id }}
                      className="flex min-w-0 items-center gap-3 px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500"
                    >
                      <MemberAvatar member={member} />
                      <span className="min-w-0 flex-1 truncate">
                        <MemberName member={member} />
                      </span>
                    </Link>
                  </td>
                  <td className="px-3 py-2"><SetChips member={member} /></td>
                  <td className="px-3 py-2"><MemberStatusBadge status={member.status} /></td>
                  <td className="px-2 py-2">
                    <button
                      type="button"
                      aria-label={`Edit ${member.display_name}`}
                      onClick={() => setEditingMemberId(member.id)}
                      className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              )
            })}
            {!listLoading && padBottom > 0 && <tr aria-hidden><td colSpan={5} style={{ height: padBottom }} /></tr>}
          </tbody>
        </table>
      </div>

      {/* Phone list: rendered in steps of 100 rather than virtualised, so the
          page scrolls as one surface instead of a box inside a box. */}
      <div className="space-y-2 sm:hidden">
        {listLoading ? (
          Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-[72px] w-full rounded-lg" />)
        ) : items.length === 0 ? (
          <div className="rounded-lg border border-zinc-800">{emptyState}</div>
        ) : (
          <>
            {items.slice(0, mobileLimit).map((member) => {
              const isSelected = selected.has(member.id)
              return (
                <div
                  key={member.id}
                  className={`flex items-center gap-3 rounded-lg border p-3 ${isSelected ? 'border-violet-700 bg-violet-950/20' : 'border-zinc-800 bg-zinc-900/30'}`}
                >
                  <input
                    type="checkbox"
                    aria-label={`Select ${member.display_name}`}
                    checked={isSelected}
                    onChange={() => toggleSelect(member.id)}
                    className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                  />
                  <Link to="/members/$id" params={{ id: member.slug ?? member.id }} className="flex min-w-0 flex-1 items-center gap-3">
                    <MemberAvatar member={member} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate"><MemberName member={member} /></span>
                      <span className="mt-1 flex min-w-0 items-center gap-2">
                        <MemberStatusBadge status={member.status} />
                        {primaryAffiliation(member.affiliations) && (
                          <span className="truncate text-xs text-zinc-400">{primarySetName(member)}</span>
                        )}
                      </span>
                    </span>
                  </Link>
                  <button
                    type="button"
                    aria-label={`Edit ${member.display_name}`}
                    onClick={() => setEditingMemberId(member.id)}
                    className="rounded p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-400"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                </div>
              )
            })}
            {items.length > mobileLimit && (
              <Button variant="outline" className="w-full" onClick={() => setMobileLimit((n) => n + MOBILE_STEP)}>
                Show {Math.min(MOBILE_STEP, items.length - mobileLimit)} more ({items.length - mobileLimit} left)
              </Button>
            )}
          </>
        )}
      </div>

      {/* Bulk action bar */}
      {hasSelection && (
        <div
          className="fixed left-1/2 z-40 flex w-max max-w-[calc(100vw-2rem)] -translate-x-1/2 flex-wrap items-center justify-center gap-x-3 gap-y-2 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 shadow-2xl shadow-black/50"
          style={{ bottom: 'max(1.5rem, env(safe-area-inset-bottom))' }}
          role="region"
          aria-label="Bulk actions for selected members"
        >
          <span className="text-sm font-medium text-white">{selected.size} selected</span>
          <div className="hidden h-4 w-px bg-zinc-700 sm:block" />
          <span className="text-xs text-zinc-400">Set status:</span>
          <Select value={bulkStatus} onValueChange={(v) => setBulkStatus(v as MemberStatus)}>
            <SelectTrigger aria-label="Set status for selected members" className="h-7 w-28 border-zinc-700 bg-zinc-800 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              {ALL_STATUSES.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button size="sm" className="h-7 text-xs" onClick={applyBulkStatus} disabled={bulkUpdate.isPending}>
            {bulkUpdate.isPending ? 'Applying…' : 'Apply'}
          </Button>
          <button onClick={() => setSelected(new Set())} aria-label="Clear selection" className="text-zinc-400 transition-colors hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <MemberFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingMemberId && (
        <EditMemberSheet memberId={editingMemberId} universeId={universe.id} onClose={() => setEditingMemberId(null)} />
      )}
    </div>
  )
}
