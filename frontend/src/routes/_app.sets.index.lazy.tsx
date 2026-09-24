import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Copy, Download, LayoutGrid, MapPin, MoreVertical, Pencil, Plus, Rows3, Search, Shield, Trash2, Users, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { SetStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useDebounce } from '@/hooks/useDebounce'
import { downloadCsv } from '@/lib/download'
import { setBadge } from '@/lib/emoji'
import { useAlliances, useAllSets, useDeleteSet, useGangs, useMunicipalities } from '@/lib/queries'
import { gangColorStyle, nonPrimaryVariantsText, setColorStyle } from '@/lib/setDisplay'
import type { SetListItem, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import {
  DuplicateSetSheet, EditSetSheet, GangPill, ReservedSetIcon, SetAvatar, SetFormSheet,
  type SetsSearch, type SortKey, type ViewMode,
} from './_app.sets.index'

// The Sets list. Its own chunk: the route file it belongs to is in the main
// bundle, because the set form is imported from there by half the app.
export const Route = createLazyFileRoute('/_app/sets/')({
  component: SetsPage,
})

// ─── Small UI bits ────────────────────────────────────────────────────────────

/** Counts and dates read best biggest or newest first; names read A to Z. */
const DESC_FIRST: SortKey[] = ['member_count', 'updated_at', 'created_at']

type StatusFilter = 'ALL' | 'ACTIVE' | 'EXTINCT'

function StatusTabs({ value, onChange, counts }: {
  value: StatusFilter
  onChange: (v: StatusFilter) => void
  /** Null while loading, so the tabs never claim a universe holds 0 sets. */
  counts: Record<StatusFilter, number> | null
}) {
  const tabs: { key: StatusFilter; label: string }[] = [
    { key: 'ALL', label: 'All' },
    { key: 'ACTIVE', label: 'Active' },
    { key: 'EXTINCT', label: 'Extinct' },
  ]
  return (
    <div className="flex h-9 items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="group" aria-label="Status">
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          aria-pressed={value === key}
          className={`flex h-full items-center gap-1.5 rounded-md px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60 ${
            value === key ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          {label}
          {counts && <span className={`tabular-nums ${value === key ? 'text-zinc-300' : 'text-zinc-500'}`}>{counts[key]}</span>}
        </button>
      ))}
    </div>
  )
}

function SortHeader({ label, col, sort, order, onSort, align = 'left', className = '' }: {
  label: string; col: SortKey; sort: SortKey; order: 'asc' | 'desc'
  onSort: (k: SortKey) => void; align?: 'left' | 'right'; className?: string
}) {
  const sorted = sort === col
  return (
    <th
      className={`px-3 py-2.5 ${align === 'right' ? 'text-right' : 'text-left'} ${className}`}
      scope="col"
      aria-sort={sorted ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <button
        onClick={() => onSort(col)}
        className={`inline-flex items-center gap-1 text-xs font-medium transition-colors hover:text-white focus-visible:text-white focus-visible:outline-none ${
          sorted ? 'text-zinc-200' : 'text-zinc-400'
        }`}
      >
        {label}
        <span className="text-zinc-500" aria-hidden>{sorted ? (order === 'asc' ? '↑' : '↓') : '↕'}</span>
      </button>
    </th>
  )
}

const ALL_SENTINEL = '__all__'
const NONE_SENTINEL = 'none'

/**
 * A filter dropdown whose options carry how many sets each would show given the
 * other filters. Options that would show nothing are left out, unless selected,
 * so a narrowed list never offers a dead end.
 */
function FacetSelect({ value, onChange, options, counts, allLabel, noneLabel, widthClass }: {
  value: string | undefined
  onChange: (v: string | undefined) => void
  options: { id: string; name: string }[]
  counts: Map<string, number>
  allLabel: string
  noneLabel: string
  widthClass: string
}) {
  const shown = options
    .filter((o) => (counts.get(o.id) ?? 0) > 0 || o.id === value)
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base', numeric: true }))
  const noneCount = counts.get(NONE_SENTINEL) ?? 0
  // A stale id from an old link still renders, rather than a blank trigger.
  const unknown = value && value !== NONE_SENTINEL && !options.some((o) => o.id === value)
  return (
    <Select value={value ?? ALL_SENTINEL} onValueChange={(v) => onChange(v === ALL_SENTINEL ? undefined : v)}>
      <SelectTrigger
        className={`h-9 text-xs ${widthClass} ${value ? 'border-violet-700/60 bg-violet-950/20 text-zinc-100' : ''}`}
        aria-label={allLabel}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL_SENTINEL}>{allLabel}</SelectItem>
        {(noneCount > 0 || value === NONE_SENTINEL) && (
          <SelectItem value={NONE_SENTINEL}>
            {noneLabel} <span className="ml-1 tabular-nums text-zinc-500">{noneCount}</span>
          </SelectItem>
        )}
        {unknown && <SelectItem value={value}>Unknown</SelectItem>}
        {shown.map((o) => (
          <SelectItem key={o.id} value={o.id}>
            {o.name} <span className="ml-1 tabular-nums text-zinc-500">{counts.get(o.id) ?? 0}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function AlliancePill({ name, id }: { name: string; id: string }) {
  return (
    <Link
      to="/alliances/$id"
      params={{ id }}
      title={`Alliance: ${name}`}
      onClick={(e) => e.stopPropagation()}
      className="inline-flex max-w-full items-center rounded-full bg-blue-950/60 px-2 py-0.5 text-[11px] font-medium text-blue-300 ring-1 ring-blue-800/50 transition-colors hover:ring-blue-600"
    >
      <span className="truncate">{name}</span>
    </Link>
  )
}

function MunicipalityPill({ name }: { name: string }) {
  return (
    <span title={name} className="inline-flex max-w-full items-center gap-1 rounded-full bg-zinc-800/80 px-2 py-0.5 text-[11px] font-medium text-zinc-300 ring-1 ring-zinc-700">
      <MapPin className="h-2.5 w-2.5 shrink-0" aria-hidden />
      <span className="truncate">{name}</span>
    </span>
  )
}

function MemberCount({ n, large = false }: { n: number; large?: boolean }) {
  return (
    <span
      title={`${n} current member${n === 1 ? '' : 's'}`}
      className={`inline-flex items-center gap-1 tabular-nums ${large ? 'text-sm text-zinc-200' : 'text-xs'} ${n === 0 ? 'text-zinc-600' : large ? '' : 'text-zinc-300'}`}
    >
      <Users className={large ? 'h-3.5 w-3.5' : 'h-3 w-3'} aria-hidden />
      {n}
    </span>
  )
}

const Dash = () => <span className="text-xs text-zinc-600" aria-label="None">-</span>

/** The set's name with its badge, and its other names underneath when it has any. */
function SetName({ set, className = '' }: { set: SetListItem; className?: string }) {
  const badge = setBadge(set.emojis)
  const aka = nonPrimaryVariantsText(set.name_variants)
  return (
    <span className={`block min-w-0 ${className}`}>
      <span className="block truncate font-medium text-white transition-colors group-hover:text-violet-300">
        {badge && <span className="mr-1.5" title={set.emojis?.join(' ')}>{badge}</span>}
        {set.name}
      </span>
      {aka && <span className="block truncate text-[11px] text-zinc-500">{aka}</span>}
    </span>
  )
}

// ─── Row actions ──────────────────────────────────────────────────────────────

function RowActions({ set, onEdit, onDuplicate, onDelete }: {
  set: SetListItem
  onEdit: () => void
  onDuplicate: () => void
  onDelete: () => void
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label={`Actions for ${set.name}`}
          onClick={(e) => e.stopPropagation()}
          className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
        >
          <MoreVertical className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onSelect={onEdit}>
          <Pencil className="mr-2 h-3.5 w-3.5" />Edit
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={onDuplicate}>
          <Copy className="mr-2 h-3.5 w-3.5" />Duplicate
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onDelete} className="text-red-400 focus:bg-red-950/40 focus:text-red-300">
          <Trash2 className="mr-2 h-3.5 w-3.5" />Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ─── Card view ────────────────────────────────────────────────────────────────

function SetCard({ set, isSelected, onToggleSelect, onEdit, onDuplicate, onDelete }: {
  set: SetListItem
  isSelected: boolean
  onToggleSelect: () => void
  onEdit: () => void
  onDuplicate: () => void
  onDelete: () => void
}) {
  const [imgError, setImgError] = useState(false)
  const photo = set.primary_photo_thumb_url && !imgError ? set.primary_photo_thumb_url : null
  return (
    <div className={`group relative flex flex-col overflow-hidden rounded-lg border bg-zinc-900/40 transition-colors ${
      isSelected ? 'border-violet-700/70 bg-violet-950/20' : 'border-zinc-800 hover:border-zinc-700'
    }`}>
      <Link to="/sets/$id" params={{ id: set.slug ?? set.id }} className="flex flex-1 flex-col focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500/60">
        {/* Header band: the set's photo when it has one, else its gang or hashed color. */}
        <div className="relative h-20 w-full overflow-hidden bg-zinc-950">
          {photo ? (
            <img src={photo} alt="" loading="lazy" decoding="async" onError={() => setImgError(true)} className="h-full w-full object-cover opacity-70" />
          ) : (
            <div className="h-full w-full" style={set.gang_color ? gangColorStyle(set.gang_color) : setColorStyle(set.name)} aria-hidden />
          )}
          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-zinc-950 via-zinc-950/80 to-transparent px-3 pb-2 pt-6 text-sm">
            <SetName set={set} />
          </div>
        </div>
        <div className="flex flex-1 flex-wrap content-start gap-1.5 p-3">
          {set.gang_name && <GangPill name={set.gang_name} />}
          {set.alliance_name && <span className="inline-flex max-w-full items-center rounded-full bg-blue-950/60 px-2 py-0.5 text-[11px] font-medium text-blue-300 ring-1 ring-blue-800/50"><span className="truncate">{set.alliance_name}</span></span>}
          {set.municipality_name && <MunicipalityPill name={set.municipality_name} />}
          {!set.gang_name && !set.alliance_name && !set.municipality_name && (
            <span className="text-[11px] text-zinc-500">No affiliations</span>
          )}
        </div>
        <div className="flex items-center justify-between border-t border-zinc-800/80 px-3 py-2">
          <MemberCount n={set.member_count} large />
          <SetStatusBadge status={set.status} />
        </div>
      </Link>
      {/* Always shown on touch screens, which have no hover to reveal them. */}
      <div className={`absolute right-2 top-2 flex items-center gap-1 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 ${
        isSelected ? '' : 'pointer-fine:opacity-0'
      }`}>
        <button
          onClick={onToggleSelect}
          aria-pressed={isSelected}
          aria-label={`Select ${set.name}`}
          className={`rounded border px-1.5 py-1 text-[10px] font-medium uppercase tracking-wide transition-colors ${
            isSelected
              ? 'border-violet-500 bg-violet-700 text-white'
              : 'border-zinc-700 bg-zinc-900/80 text-zinc-300 hover:bg-zinc-800'
          }`}
        >
          {isSelected ? 'Selected' : 'Select'}
        </button>
        <div className="rounded bg-zinc-900/80">
          <RowActions set={set} onEdit={onEdit} onDuplicate={onDuplicate} onDelete={onDelete} />
        </div>
      </div>
    </div>
  )
}

/** Phone row: the table's columns don't fit, so the affiliations fold into one line. */
function SetPhoneRow({ set }: { set: SetListItem }) {
  const affiliations = [set.gang_name, set.alliance_name, set.municipality_name].filter(Boolean).join(' · ')
  return (
    <Link
      to="/sets/$id"
      params={{ id: set.slug ?? set.id }}
      className="group flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2.5 transition-colors active:bg-zinc-800/60"
    >
      <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} gangColor={set.gang_color} />
      <span className="min-w-0 flex-1 text-sm">
        <SetName set={set} />
        {affiliations && <span className="block truncate text-[11px] text-zinc-400">{affiliations}</span>}
      </span>
      <span className="flex shrink-0 flex-col items-end gap-1">
        <SetStatusBadge status={set.status} />
        <MemberCount n={set.member_count} />
      </span>
    </Link>
  )
}

function RowSkeleton() {
  return (
    <tr aria-hidden className="h-[53px]">
      <td className="px-3"><Skeleton className="h-3.5 w-3.5 rounded-sm" /></td>
      <td className="px-3">
        <span className="flex items-center gap-3">
          <Skeleton className="h-7 w-7 shrink-0 rounded-md" />
          <Skeleton className="h-3.5 w-36" />
        </span>
      </td>
      <td className="hidden px-3 md:table-cell"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td className="hidden px-3 md:table-cell"><Skeleton className="h-5 w-20 rounded-full" /></td>
      <td className="hidden px-3 lg:table-cell"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td className="px-3"><Skeleton className="ml-auto h-3.5 w-8" /></td>
      <td className="px-3"><Skeleton className="h-5 w-14 rounded-full" /></td>
      <td />
    </tr>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

/** Cards and phone rows render in steps; the table virtualises instead. */
const STEP = 60

const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

/** Everything a search term can hit: every name variant, the emojis, and the affiliations. */
function haystack(s: SetListItem): string {
  const parts: (string | null | undefined)[] = [s.name, s.gang_name, s.alliance_name, s.municipality_name]
  for (const v of s.name_variants ?? []) parts.push(v.name, v.initials, v.number)
  for (const e of s.emojis ?? []) parts.push(e)
  return fold(parts.filter(Boolean).join(' '))
}

function bump(map: Map<string, number>, key: string) {
  map.set(key, (map.get(key) ?? 0) + 1)
}

function SetsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const search = Route.useSearch()
  const navigate = useNavigate({ from: '/sets/' })

  // Filtering is instant on the typed text; the URL follows it, debounced and
  // replacing, so a word is not a dozen history entries.
  const [q, setQ] = useState(search.q ?? '')
  const debouncedQ = useDebounce(q.trim(), 250)
  useEffect(() => {
    if (debouncedQ === (search.q ?? '')) return
    navigate({ search: (prev) => ({ ...prev, q: debouncedQ || undefined }), replace: true })
    // Deliberately on debouncedQ alone: also firing on search.q would push the
    // stale debounced text straight back over a Back navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ])

  // Back and Forward move the URL under the field; follow them during render.
  const [urlQ, setUrlQ] = useState(search.q)
  if (search.q !== urlQ) {
    setUrlQ(search.q)
    if ((search.q ?? '') !== q.trim()) setQ(search.q ?? '')
  }

  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null)
  const [deletingSet, setDeletingSet] = useState<SetListItem | null>(null)
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [selected, setSelected] = useState<Set<UUID>>(new Set())

  const view: ViewMode = search.view ?? 'table'
  const sort: SortKey = search.sort ?? 'name'
  const order: 'asc' | 'desc' = search.order ?? (DESC_FIRST.includes(sort) ? 'desc' : 'asc')
  const statusFilter: StatusFilter = search.status ?? 'ALL'
  const { alliance, gang, muni } = search

  const { data, isLoading } = useAllSets(universeId)
  const { data: alliancesData } = useAlliances(universeId)
  const { data: gangsData } = useGangs(universeId)
  const { data: munisData } = useMunicipalities(universeId)
  const deleteSet = useDeleteSet(universe?.id ?? '')

  const allSets = useMemo(() => data?.items ?? [], [data])
  // The system sets (Civilian, Police, Unknown) stand in their own row, outside
  // every search and filter, and never in the list or its counts.
  const reservedSets = useMemo(
    () => allSets.filter((s) => s.is_reserved).sort((a, b) => a.name.localeCompare(b.name)),
    [allSets],
  )
  const realSets = useMemo(() => allSets.filter((s) => !s.is_reserved), [allSets])
  const haystacks = useMemo(() => new Map(realSets.map((s) => [s.id, haystack(s)])), [realSets])
  const universeCounts = useMemo(() => {
    let active = 0
    for (const s of realSets) if (s.status === 'ACTIVE') active++
    return { total: realSets.length, active, extinct: realSets.length - active }
  }, [realSets])

  // One pass computes the list and every facet. Each facet counts what its own
  // choices would show under all the *other* filters, so a count is always
  // what clicking it gives.
  const facets = useMemo(() => {
    const terms = fold(q.trim()).split(/\s+/).filter(Boolean)
    const key = (id: string | null) => id ?? NONE_SENTINEL
    const statusCounts: Record<StatusFilter, number> = { ALL: 0, ACTIVE: 0, EXTINCT: 0 }
    const allianceCounts = new Map<string, number>()
    const gangCounts = new Map<string, number>()
    const muniCounts = new Map<string, number>()
    const shown: SetListItem[] = []
    for (const s of realSets) {
      const hay = haystacks.get(s.id) ?? ''
      if (!terms.every((t) => hay.includes(t))) continue
      const st = statusFilter === 'ALL' || s.status === statusFilter
      const al = !alliance || key(s.alliance_id) === alliance
      const ga = !gang || key(s.gang_id) === gang
      const mu = !muni || key(s.municipality_id) === muni
      if (al && ga && mu) { statusCounts.ALL++; statusCounts[s.status]++ }
      if (st && ga && mu) bump(allianceCounts, key(s.alliance_id))
      if (st && al && mu) bump(gangCounts, key(s.gang_id))
      if (st && al && ga) bump(muniCounts, key(s.municipality_id))
      if (st && al && ga && mu) shown.push(s)
    }
    return { statusCounts, allianceCounts, gangCounts, muniCounts, shown }
  }, [realSets, haystacks, q, statusFilter, alliance, gang, muni])

  const items = useMemo(() => {
    const dir = order === 'asc' ? 1 : -1
    const byName = (a: SetListItem, b: SetListItem) =>
      a.name.localeCompare(b.name, undefined, { sensitivity: 'base', numeric: true })
    // Sets without the value sink to the bottom whichever way the column sorts.
    const byText = (x: string | null, y: string | null) => {
      if (!x !== !y) return x ? -1 : 1
      return (x ?? '').localeCompare(y ?? '', undefined, { sensitivity: 'base' }) * dir
    }
    const byDate = (x: string, y: string) => (x < y ? -1 : x > y ? 1 : 0) * dir
    return [...facets.shown].sort((a, b) => {
      switch (sort) {
        case 'status': return (a.status === b.status ? 0 : a.status === 'ACTIVE' ? -1 : 1) * dir || byName(a, b)
        case 'member_count': return (a.member_count - b.member_count) * dir || byName(a, b)
        case 'alliance': return byText(a.alliance_name, b.alliance_name) || byName(a, b)
        case 'municipality': return byText(a.municipality_name, b.municipality_name) || byName(a, b)
        case 'updated_at': return byDate(a.updated_at, b.updated_at) || byName(a, b)
        case 'created_at': return byDate(a.created_at, b.created_at) || byName(a, b)
        default: return byName(a, b) * dir
      }
    })
  }, [facets.shown, sort, order])

  // Selection only ever acts on sets the current filters show.
  const selectedShown = useMemo(() => items.filter((s) => selected.has(s.id)), [items, selected])
  const allSelected = items.length > 0 && selectedShown.length === items.length

  // Cards and phone rows grow in steps, and start over when the list changes.
  const [limit, setLimit] = useState(STEP)
  const [limitFor, setLimitFor] = useState(items)
  if (limitFor !== items) {
    setLimitFor(items)
    setLimit(STEP)
  }

  const tableScrollRef = useRef<HTMLDivElement | null>(null)
  const rowVirtualizer = useVirtualizer({
    count: view === 'table' ? items.length : 0,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 53,
    overscan: 12,
  })
  const virtualRows = rowVirtualizer.getVirtualItems()
  const padTop = virtualRows[0]?.start ?? 0
  const padBottom = rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)

  if (!universe) return <NoUniverse />

  const hasFilters = statusFilter !== 'ALL' || !!alliance || !!gang || !!muni || !!q.trim()

  function patch(next: Partial<SetsSearch>) {
    navigate({
      search: (prev) => {
        const merged: SetsSearch = { ...prev, ...next }
        for (const k of Object.keys(merged) as (keyof SetsSearch)[]) {
          if (merged[k] === undefined) delete merged[k]
        }
        return merged
      },
      replace: true,
    })
  }

  function toggleSort(key: SortKey) {
    if (sort === key) patch({ order: order === 'asc' ? 'desc' : 'asc' })
    else patch({ sort: key === 'name' ? undefined : key, order: undefined })
  }

  function clearFilters() {
    setQ('')
    navigate({ search: (prev) => ({ view: prev.view, sort: prev.sort, order: prev.order }), replace: true })
  }

  function toggleSelect(id: UUID) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function bulkDeleteSets() {
    const targets = selectedShown
    if (targets.length === 0) return
    setBulkDeleting(true)
    // Settled, not all: one refusal must not hide how many went through. Each
    // failure already raised its own toast from the global mutation handler.
    const results = await Promise.allSettled(targets.map((s) => deleteSet.mutateAsync(s.id)))
    const deleted = targets.filter((_, i) => results[i].status === 'fulfilled').map((s) => s.id)
    if (deleted.length > 0) toast.success(`Deleted ${deleted.length} set${deleted.length === 1 ? '' : 's'}`)
    setSelected((prev) => {
      const next = new Set(prev)
      for (const id of deleted) next.delete(id)
      return next
    })
    setBulkDeleting(false)
    setConfirmingBulkDelete(false)
  }

  async function deleteSingleSet(s: SetListItem) {
    try {
      await deleteSet.mutateAsync(s.id)
      toast.success(`Deleted "${s.name}"`)
    } finally {
      setDeletingSet(null)
    }
  }

  const allianceOptions = alliancesData?.items ?? []
  const gangOptions = gangsData?.items ?? []
  const muniOptions = (munisData?.items ?? []).filter((m) => !m.parent_id)
  const duplicateFallback = duplicatingId ? allSets.find((s) => s.id === duplicatingId) ?? null : null
  const bulkMembers = selectedShown.reduce((n, s) => n + s.member_count, 0)
  const members = (n: number) => `${n.toLocaleString()} current member${n === 1 ? '' : 's'}`

  const emptyState = (
    <EmptyState
      icon={Shield}
      title={hasFilters ? 'No sets match these filters' : 'No sets yet'}
      description={hasFilters ? undefined : 'Create a set to start tracking a crew.'}
      action={hasFilters
        ? <Button size="sm" variant="outline" onClick={clearFilters}>Clear search and filters</Button>
        : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Create the first set</Button>
      }
    />
  )

  const showMore = items.length > limit && (
    <Button variant="outline" className="mt-3 w-full" onClick={() => setLimit((n) => n + STEP)}>
      Show {Math.min(STEP, items.length - limit)} more ({items.length - limit} left)
    </Button>
  )

  const rowHandlers = (set: SetListItem) => ({
    onEdit: () => setEditingId(set.id),
    onDuplicate: () => setDuplicatingId(set.id),
    onDelete: () => setDeletingSet(set),
  })

  return (
    <div className={selectedShown.length > 0 ? 'pb-28' : 'pb-8'}>
      <PageHeader
        title="Sets"
        description={
          isLoading ? 'Loading…'
            : universeCounts.total === 0 ? 'No sets yet'
            : hasFilters
              ? `${items.length.toLocaleString()} of ${universeCounts.total.toLocaleString()} sets`
              : `${universeCounts.total.toLocaleString()} sets · ${universeCounts.active} active · ${universeCounts.extinct} extinct`
        }
        action={
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus className="mr-1.5 h-4 w-4" />Add set
          </Button>
        }
      />

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            className="h-9 pl-8 pr-8 text-sm"
            placeholder="Search name, initials, number, emoji…"
            aria-label="Search sets"
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
        </div>

        {/* On a phone the filters are one row that scrolls sideways; wrapped,
            they stacked five rows deep above the first set. From sm up the
            wrapper dissolves and they flow as before. */}
        <div className="flex w-full items-center gap-2 overflow-x-auto [scrollbar-width:none] sm:contents [&::-webkit-scrollbar]:hidden [&>*]:shrink-0">
        <StatusTabs
          value={statusFilter}
          onChange={(v) => patch({ status: v === 'ALL' ? undefined : v })}
          counts={isLoading ? null : facets.statusCounts}
        />

        <FacetSelect
          value={alliance}
          onChange={(v) => patch({ alliance: v })}
          options={allianceOptions}
          counts={facets.allianceCounts}
          allLabel="All alliances"
          noneLabel="No alliance"
          widthClass="w-auto min-w-32 max-w-56"
        />
        {/* Nations only matter once a universe has them. */}
        {(gangOptions.length > 0 || gang) && (
          <FacetSelect
            value={gang}
            onChange={(v) => patch({ gang: v })}
            options={gangOptions}
            counts={facets.gangCounts}
            allLabel="All gangs"
            noneLabel="No gang"
            widthClass="w-auto min-w-28 max-w-48"
          />
        )}
        <FacetSelect
          value={muni}
          onChange={(v) => patch({ muni: v })}
          options={muniOptions}
          counts={facets.muniCounts}
          allLabel="All municipalities"
          noneLabel="No municipality"
          widthClass="w-auto min-w-32 max-w-52"
        />

        {hasFilters && (
          <button
            onClick={clearFilters}
            className="inline-flex h-9 items-center gap-1 rounded-md px-2 text-xs text-zinc-400 transition-colors hover:text-white"
          >
            <X className="h-3 w-3" /> Clear
          </button>
        )}

        <div className="ml-auto flex items-center gap-2">
          {/* Cards and phone rows have no headers to click, so they sort from here. */}
          <div className={view === 'cards' ? '' : 'sm:hidden'}>
            <Select
              value={`${sort}:${order}`}
              onValueChange={(v) => {
                const [s, o] = v.split(':') as [SortKey, 'asc' | 'desc']
                patch({ sort: s === 'name' ? undefined : s, order: o })
              }}
            >
              <SelectTrigger className="h-9 w-auto min-w-32 text-xs" aria-label="Sort">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name:asc">Name A→Z</SelectItem>
                <SelectItem value="name:desc">Name Z→A</SelectItem>
                <SelectItem value="member_count:desc">Most members</SelectItem>
                <SelectItem value="member_count:asc">Fewest members</SelectItem>
                <SelectItem value="alliance:asc">Alliance</SelectItem>
                <SelectItem value="municipality:asc">Municipality</SelectItem>
                <SelectItem value="updated_at:desc">Recently updated</SelectItem>
                <SelectItem value="created_at:desc">Recently added</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="hidden items-center rounded-lg border border-zinc-800 bg-zinc-900/50 p-0.5 sm:flex">
            <button
              onClick={() => patch({ view: undefined })}
              aria-label="Table view"
              aria-pressed={view === 'table'}
              className={`rounded-md p-1.5 transition-colors ${view === 'table' ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'}`}
            >
              <Rows3 className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => patch({ view: 'cards' })}
              aria-label="Card view"
              aria-pressed={view === 'cards'}
              className={`rounded-md p-1.5 transition-colors ${view === 'cards' ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'}`}
            >
              <LayoutGrid className="h-3.5 w-3.5" />
            </button>
          </div>

          <Button
            variant="outline" size="sm" className="h-9"
            onClick={() => {
              const date = new Date().toISOString().slice(0, 10)
              const url = `/sets/?${new URLSearchParams({ universe_id: universe.id, format: 'csv' }).toString()}`
              downloadCsv(url, `sets-${universe.slug}-${date}.csv`)
            }}
          >
            <Download className="mr-1.5 h-3.5 w-3.5" />Export all
          </Button>
        </div>
        </div>
      </div>

      {/* System sets. Their own row, so it stands whatever is typed or filtered. */}
      {reservedSets.length > 0 && (
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">System</span>
          {reservedSets.map((s) => (
            // The icon sits bare inside the pill: a bordered tile within a bordered
            // capsule puts a square inside a round and reads as two nested boxes.
            <Link
              key={s.id}
              to="/sets/$id"
              params={{ id: s.slug ?? s.id }}
              title={`${s.name}: ${members(s.member_count)}`}
              className="group inline-flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-900/50 px-3 py-1 text-xs text-zinc-400 transition-colors hover:border-zinc-500 hover:text-zinc-200"
            >
              <ReservedSetIcon name={s.name} className="h-3.5 w-3.5 text-zinc-500 transition-colors group-hover:text-zinc-300" />
              {s.name}
              <span className="tabular-nums text-zinc-500 transition-colors group-hover:text-zinc-400">{s.member_count}</span>
            </Link>
          ))}
        </div>
      )}

      {/* Phone: compact rows, whichever view is picked. */}
      <div className="space-y-2 sm:hidden">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-[62px] w-full rounded-lg" />)
          : items.length === 0
            ? emptyState
            : items.slice(0, limit).map((set) => <SetPhoneRow key={set.id} set={set} />)}
        {!isLoading && showMore}
      </div>

      {view === 'cards' ? (
        <div className="hidden sm:block">
          {!isLoading && items.length === 0 ? emptyState : (
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-4">
              {isLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/40">
                      <Skeleton className="h-20 w-full rounded-none" />
                      <div className="space-y-2 p-3">
                        <Skeleton className="h-4 w-24 rounded-full" />
                      </div>
                      <div className="border-t border-zinc-800 px-3 py-2">
                        <Skeleton className="h-4 w-16" />
                      </div>
                    </div>
                  ))
                : items.slice(0, limit).map((set) => (
                    <SetCard
                      key={set.id}
                      set={set}
                      isSelected={selected.has(set.id)}
                      onToggleSelect={() => toggleSelect(set.id)}
                      {...rowHandlers(set)}
                    />
                  ))}
            </div>
          )}
          {!isLoading && showMore}
        </div>
      ) : (
        // Always virtualised: the whole universe is in it.
        <div
          ref={tableScrollRef}
          className="hidden overflow-y-auto rounded-lg border border-zinc-800 sm:block"
          style={{ maxHeight: 'calc(100dvh - 14rem)' }}
        >
          <table className="w-full table-fixed text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="border-b border-zinc-800 bg-zinc-900/95 backdrop-blur">
                <th className="w-10 px-3 py-2.5" scope="col">
                  <input
                    type="checkbox"
                    aria-label="Select all shown sets"
                    checked={allSelected}
                    onChange={() => setSelected(allSelected ? new Set() : new Set(items.map((s) => s.id)))}
                    className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                  />
                </th>
                <SortHeader label="Set" col="name" sort={sort} order={order} onSort={toggleSort} />
                <th className="hidden w-[15%] px-3 py-2.5 text-left text-xs font-medium text-zinc-400 md:table-cell" scope="col">Gang</th>
                <SortHeader label="Alliance" col="alliance" sort={sort} order={order} onSort={toggleSort} className="hidden w-[17%] md:table-cell" />
                <SortHeader label="Municipality" col="municipality" sort={sort} order={order} onSort={toggleSort} className="hidden w-[15%] lg:table-cell" />
                <SortHeader label="Members" col="member_count" sort={sort} order={order} onSort={toggleSort} align="right" className="w-28" />
                <SortHeader label="Status" col="status" sort={sort} order={order} onSort={toggleSort} className="w-24" />
                <th className="w-12" scope="col"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {isLoading && Array.from({ length: 10 }).map((_, i) => <RowSkeleton key={i} />)}
              {!isLoading && items.length === 0 && (
                <tr><td colSpan={8}>{emptyState}</td></tr>
              )}
              {padTop > 0 && <tr aria-hidden><td colSpan={8} style={{ height: padTop }} /></tr>}
              {!isLoading && virtualRows.map((vr) => {
                const set = items[vr.index]
                const isSelected = selected.has(set.id)
                return (
                  <tr
                    key={set.id}
                    data-index={vr.index}
                    ref={rowVirtualizer.measureElement}
                    className={`group transition-colors hover:bg-zinc-900/50 ${isSelected ? 'bg-violet-950/20' : ''}`}
                  >
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        aria-label={`Select ${set.name}`}
                        checked={isSelected}
                        onChange={() => toggleSelect(set.id)}
                        className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                      />
                    </td>
                    <td className="p-0">
                      <Link to="/sets/$id" params={{ id: set.slug ?? set.id }} className="flex min-h-[52px] items-center gap-3 px-3 py-2">
                        <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} gangColor={set.gang_color} size="sm" />
                        <SetName set={set} />
                      </Link>
                    </td>
                    <td className="hidden px-3 py-2 md:table-cell">{set.gang_name ? <GangPill name={set.gang_name} /> : <Dash />}</td>
                    <td className="hidden px-3 py-2 md:table-cell">
                      {set.alliance_id && set.alliance_name ? <AlliancePill name={set.alliance_name} id={set.alliance_id} /> : <Dash />}
                    </td>
                    <td className="hidden px-3 py-2 lg:table-cell">{set.municipality_name ? <MunicipalityPill name={set.municipality_name} /> : <Dash />}</td>
                    <td className="px-3 py-2 text-right"><MemberCount n={set.member_count} /></td>
                    <td className="px-3 py-2"><SetStatusBadge status={set.status} /></td>
                    <td className="pr-2 text-right"><RowActions set={set} {...rowHandlers(set)} /></td>
                  </tr>
                )
              })}
              {padBottom > 0 && <tr aria-hidden><td colSpan={8} style={{ height: padBottom }} /></tr>}
            </tbody>
          </table>
        </div>
      )}

      <SetFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingId && (
        <EditSetSheet setId={editingId} universeId={universe.id} open onClose={() => setEditingId(null)} />
      )}
      {duplicatingId && (
        <DuplicateSetSheet
          key={`dup-${duplicatingId}`}
          setId={duplicatingId}
          universeId={universe.id}
          open
          onClose={() => setDuplicatingId(null)}
          fallback={duplicateFallback}
        />
      )}

      <BulkActionBar count={selectedShown.length} label="set" onClear={() => setSelected(new Set())}>
        <Button
          size="sm"
          variant="destructive"
          className="h-7 text-xs"
          onClick={() => setConfirmingBulkDelete(true)}
          disabled={bulkDeleting}
        >
          <Trash2 className="mr-1 h-3 w-3" />
          Delete
        </Button>
      </BulkActionBar>

      <ConfirmDialog
        open={confirmingBulkDelete}
        title={`Delete ${selectedShown.length} set${selectedShown.length === 1 ? '' : 's'}?`}
        description="This cannot be undone. Members in these sets will be unassigned, and friend/enemy edges will be removed."
        impact={`${members(bulkMembers)} lose this affiliation.`}
        confirmLabel="Delete"
        destructive
        pending={bulkDeleting}
        onConfirm={bulkDeleteSets}
        onCancel={() => setConfirmingBulkDelete(false)}
      />

      <ConfirmDialog
        open={!!deletingSet}
        title={`Delete "${deletingSet?.name ?? ''}"?`}
        description="This cannot be undone. Members in this set will be unassigned, and friend/enemy edges will be removed."
        impact={deletingSet ? `${members(deletingSet.member_count)} lose this affiliation.` : undefined}
        confirmLabel="Delete"
        destructive
        pending={deleteSet.isPending}
        onConfirm={() => deletingSet && deleteSingleSet(deletingSet)}
        onCancel={() => setDeletingSet(null)}
      />
    </div>
  )
}
