import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Download, MoreVertical, Network, Pencil, Plus, Search, Shield, Trash2, Users, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Sheet, SheetContent } from '@/components/Sheet'
import { AllianceStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useDebounce } from '@/hooks/useDebounce'
import { downloadCsv } from '@/lib/download'
import { useAlliance, useAlliances, useDeleteAlliance } from '@/lib/queries'
import type { AllianceListItem, AllianceStatus, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import { AllianceFormSheet, type AlliancesSearch, type AllianceSortKey } from './_app.alliances.index'
import { GangPill, SetAvatar } from './_app.sets.index'

// The Alliances list, in its own chunk; the route file keeps validateSearch
// and the form sheet, which the alliance page imports.
export const Route = createLazyFileRoute('/_app/alliances/')({
  component: AlliancesPage,
})

const STATUSES: AllianceStatus[] = ['ACTIVE', 'DORMANT', 'EXTINCT']
const STATUS_LABEL: Record<AllianceStatus, string> = { ACTIVE: 'Active', DORMANT: 'Dormant', EXTINCT: 'Extinct' }
/** Counts read best biggest first; names and statuses read in order. */
const DESC_FIRST: AllianceSortKey[] = ['set_count', 'member_count']

const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

function haystack(a: AllianceListItem): string {
  return fold([a.name, a.gang_name, ...(a.aliases ?? [])].filter(Boolean).join(' '))
}

const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

// ─── Pieces ───────────────────────────────────────────────────────────────────

function Count({ n, icon: Icon, label }: { n: number; icon: typeof Users; label: string }) {
  return (
    <span title={plural(n, label)} className={`inline-flex items-center gap-1 text-xs tabular-nums ${n === 0 ? 'text-zinc-600' : 'text-zinc-300'}`}>
      <Icon className="h-3 w-3" aria-hidden />
      {n.toLocaleString()}
    </span>
  )
}

function AllianceName({ alliance }: { alliance: AllianceListItem }) {
  const aliases = (alliance.aliases ?? []).filter(Boolean).join(' · ')
  return (
    <span className="block min-w-0">
      <span className="block truncate font-medium text-white transition-colors group-hover:text-violet-300">{alliance.name}</span>
      {aliases && <span className="block truncate text-[11px] text-zinc-500">{aliases}</span>}
    </span>
  )
}

function RowActions({ alliance, onEdit, onDelete }: { alliance: AllianceListItem; onEdit: () => void; onDelete: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label={`Actions for ${alliance.name}`}
          className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
        >
          <MoreVertical className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onSelect={onEdit}><Pencil className="mr-2 h-3.5 w-3.5" />Edit</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onDelete} className="text-red-400 focus:bg-red-950/40 focus:text-red-300">
          <Trash2 className="mr-2 h-3.5 w-3.5" />Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** The list row lacks the description and founding date, so edit loads the full alliance first. */
function EditAllianceSheet({ id, universeId, onClose }: { id: UUID; universeId: UUID; onClose: () => void }) {
  const { data } = useAlliance(id, universeId)
  if (!data) {
    return (
      <Sheet open onOpenChange={(v) => !v && onClose()}>
        <SheetContent title="Edit Alliance" description="Loading…">
          <div className="space-y-3 pt-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        </SheetContent>
      </Sheet>
    )
  }
  return <AllianceFormSheet universeId={universeId} open onClose={onClose} initial={data} />
}

function RowSkeleton() {
  return (
    <tr aria-hidden className="h-[53px]">
      <td className="px-3"><Skeleton className="h-3.5 w-3.5 rounded-sm" /></td>
      <td className="px-3">
        <span className="flex items-center gap-3">
          <Skeleton className="h-7 w-7 shrink-0 rounded-md" />
          <Skeleton className="h-3.5 w-32" />
        </span>
      </td>
      <td className="hidden px-3 md:table-cell"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td className="px-3"><Skeleton className="ml-auto h-3.5 w-8" /></td>
      <td className="px-3"><Skeleton className="ml-auto h-3.5 w-8" /></td>
      <td className="px-3"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td />
    </tr>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function AlliancesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const search = Route.useSearch()
  const navigate = useNavigate({ from: '/alliances/' })

  const [q, setQ] = useState(search.q ?? '')
  const debouncedQ = useDebounce(q.trim(), 250)
  useEffect(() => {
    if (debouncedQ === (search.q ?? '')) return
    navigate({ search: (prev) => ({ ...prev, q: debouncedQ || undefined }), replace: true })
    // On debouncedQ alone: also firing on search.q would push the stale
    // debounced text back over a Back navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ])
  const [urlQ, setUrlQ] = useState(search.q)
  if (search.q !== urlQ) {
    setUrlQ(search.q)
    if ((search.q ?? '') !== q.trim()) setQ(search.q ?? '')
  }

  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<UUID | null>(null)
  const [deleting, setDeleting] = useState<AllianceListItem | null>(null)
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [selected, setSelected] = useState<Set<UUID>>(new Set())

  const status = search.status
  const sort: AllianceSortKey = search.sort ?? 'name'
  const order = search.order ?? (DESC_FIRST.includes(sort) ? 'desc' : 'asc')

  const { data, isLoading } = useAlliances(universeId)
  const deleteAlliance = useDeleteAlliance(universe?.id ?? '')
  const all = useMemo(() => data?.items ?? [], [data])
  const haystacks = useMemo(() => new Map(all.map((a) => [a.id, haystack(a)])), [all])

  // The status tabs count what the search leaves, so each says what clicking it shows.
  const { statusCounts, searched } = useMemo(() => {
    const terms = fold(q.trim()).split(/\s+/).filter(Boolean)
    const counts: Record<AllianceStatus, number> = { ACTIVE: 0, DORMANT: 0, EXTINCT: 0 }
    const hits = all.filter((a) => {
      const hay = haystacks.get(a.id) ?? ''
      if (!terms.every((t) => hay.includes(t))) return false
      counts[a.status]++
      return true
    })
    return { statusCounts: counts, searched: hits }
  }, [all, haystacks, q])

  const items = useMemo(() => {
    const dir = order === 'asc' ? 1 : -1
    const byName = (a: AllianceListItem, b: AllianceListItem) =>
      a.name.localeCompare(b.name, undefined, { sensitivity: 'base', numeric: true })
    const list = status ? searched.filter((a) => a.status === status) : searched
    return [...list].sort((a, b) => {
      switch (sort) {
        case 'status': return (STATUSES.indexOf(a.status) - STATUSES.indexOf(b.status)) * dir || byName(a, b)
        case 'set_count': return (a.set_count - b.set_count) * dir || byName(a, b)
        case 'member_count': return (a.member_count - b.member_count) * dir || byName(a, b)
        default: return byName(a, b) * dir
      }
    })
  }, [searched, status, sort, order])

  const selectedShown = useMemo(() => items.filter((a) => selected.has(a.id)), [items, selected])
  const allSelected = items.length > 0 && selectedShown.length === items.length

  if (!universe) return <NoUniverse />

  const hasFilters = !!status || !!q.trim()
  const totals = {
    sets: all.reduce((n, a) => n + a.set_count, 0),
    active: all.filter((a) => a.status === 'ACTIVE').length,
  }

  function patch(next: Partial<AlliancesSearch>) {
    navigate({
      search: (prev) => {
        const merged: AlliancesSearch = { ...prev, ...next }
        for (const k of Object.keys(merged) as (keyof AlliancesSearch)[]) {
          if (merged[k] === undefined) delete merged[k]
        }
        return merged
      },
      replace: true,
    })
  }

  function toggleSort(key: AllianceSortKey) {
    if (sort === key) patch({ order: order === 'asc' ? 'desc' : 'asc' })
    else patch({ sort: key === 'name' ? undefined : key, order: undefined })
  }

  function clearFilters() {
    setQ('')
    navigate({ search: (prev) => ({ sort: prev.sort, order: prev.order }), replace: true })
  }

  function toggleSelect(id: UUID) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function bulkDelete() {
    const targets = selectedShown
    if (targets.length === 0) return
    setBulkDeleting(true)
    // Settled: one refusal must not hide how many went through. Failures
    // already toast from the global mutation handler.
    const results = await Promise.allSettled(targets.map((a) => deleteAlliance.mutateAsync(a.id)))
    const done = targets.filter((_, i) => results[i].status === 'fulfilled').map((a) => a.id)
    if (done.length > 0) toast.success(`Deleted ${plural(done.length, 'alliance')}`)
    setSelected((prev) => {
      const next = new Set(prev)
      for (const id of done) next.delete(id)
      return next
    })
    setBulkDeleting(false)
    setConfirmingBulkDelete(false)
  }

  async function deleteOne(a: AllianceListItem) {
    try {
      await deleteAlliance.mutateAsync(a.id)
      toast.success(`Deleted "${a.name}"`)
    } finally {
      setDeleting(null)
    }
  }

  const impact = (list: AllianceListItem[]) => {
    const sets = list.reduce((n, a) => n + a.set_count, 0)
    const members = list.reduce((n, a) => n + a.member_count, 0)
    return `${plural(sets, 'set')} and ${plural(members, 'current member')} lose this alliance.`
  }

  function sortHeader(key: AllianceSortKey, label: string, className = '', align: 'left' | 'right' = 'left') {
    const sorted = sort === key
    return (
      <th scope="col" className={`px-3 py-2.5 ${align === 'right' ? 'text-right' : 'text-left'} ${className}`} aria-sort={sorted ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}>
        <button
          onClick={() => toggleSort(key)}
          className={`inline-flex items-center gap-1 text-xs font-medium transition-colors hover:text-white focus-visible:text-white focus-visible:outline-none ${sorted ? 'text-zinc-200' : 'text-zinc-400'}`}
        >
          {label} <span className="text-zinc-500" aria-hidden>{sorted ? (order === 'asc' ? '↑' : '↓') : '↕'}</span>
        </button>
      </th>
    )
  }

  const emptyState = (
    <EmptyState
      icon={Network}
      title={hasFilters ? 'No alliances match these filters' : 'No alliances yet'}
      description={hasFilters ? undefined : 'Create an alliance to organise sets.'}
      action={hasFilters
        ? <Button size="sm" variant="outline" onClick={clearFilters}>Clear search and filters</Button>
        : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Create the first alliance</Button>}
    />
  )

  const searchedTotal = searched.length

  return (
    <div className={selectedShown.length > 0 ? 'pb-28' : 'pb-8'}>
      <PageHeader
        title="Alliances"
        description={
          isLoading ? 'Loading…'
            : all.length === 0 ? 'No alliances yet'
            : hasFilters ? `${items.length} of ${plural(all.length, 'alliance')}`
            : `${plural(all.length, 'alliance')} · ${totals.active} active · ${plural(totals.sets, 'set')} in them`
        }
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add alliance</Button>}
      />

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            className="h-9 pl-8 pr-8 text-sm"
            placeholder="Search name, alias or gang…"
            aria-label="Search alliances"
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

        <div className="flex h-9 items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="group" aria-label="Status">
          {([undefined, ...STATUSES] as const).map((s) => {
            const active = status === s
            const n = s ? statusCounts[s] : searchedTotal
            // A status nothing holds is left out, unless it is the one picked.
            if (s && n === 0 && !active && !isLoading) return null
            return (
              <button
                key={s ?? 'all'}
                onClick={() => patch({ status: s })}
                aria-pressed={active}
                className={`flex h-full items-center gap-1.5 rounded-md px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60 ${
                  active ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {s ? STATUS_LABEL[s] : 'All'}
                {!isLoading && <span className={`tabular-nums ${active ? 'text-zinc-300' : 'text-zinc-500'}`}>{n}</span>}
              </button>
            )
          })}
        </div>

        {hasFilters && (
          <button onClick={clearFilters} className="inline-flex h-9 items-center gap-1 rounded-md px-2 text-xs text-zinc-400 transition-colors hover:text-white">
            <X className="h-3 w-3" /> Clear
          </button>
        )}

        <Button
          variant="outline" size="sm" className="ml-auto h-9"
          onClick={() => {
            const date = new Date().toISOString().slice(0, 10)
            downloadCsv(`/alliances/?universe_id=${universe.id}&format=csv`, `alliances-${universe.slug}-${date}.csv`)
          }}
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />Export all
        </Button>
      </div>

      {/* Phone: rows, with the counts under the name. */}
      <div className="space-y-2 sm:hidden">
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-[62px] w-full rounded-lg" />)
          : items.length === 0 ? emptyState
          : items.map((a) => (
              <Link
                key={a.id}
                to="/alliances/$id"
                params={{ id: a.slug ?? a.id }}
                className="group flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2.5 transition-colors active:bg-zinc-800/60"
              >
                <SetAvatar name={a.name} thumbUrl={a.primary_photo_thumb_url} gangColor={a.gang_color} />
                <span className="min-w-0 flex-1 text-sm">
                  <AllianceName alliance={a} />
                  <span className="mt-0.5 flex items-center gap-3">
                    <Count n={a.set_count} icon={Shield} label="set" />
                    <Count n={a.member_count} icon={Users} label="member" />
                    {a.gang_name && <span className="truncate text-[11px] text-zinc-400">{a.gang_name}</span>}
                  </span>
                </span>
                <AllianceStatusBadge status={a.status} />
              </Link>
            ))}
      </div>

      <div className="hidden overflow-hidden rounded-lg border border-zinc-800 sm:block">
        <table className="w-full table-fixed text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/60">
              <th className="w-10 px-3 py-2.5" scope="col">
                <input
                  type="checkbox"
                  aria-label="Select all shown alliances"
                  checked={allSelected}
                  onChange={() => setSelected(allSelected ? new Set() : new Set(items.map((a) => a.id)))}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              {sortHeader('name', 'Alliance')}
              <th scope="col" className="hidden w-[18%] px-3 py-2.5 text-left text-xs font-medium text-zinc-400 md:table-cell">Gang</th>
              {sortHeader('set_count', 'Sets', 'w-24', 'right')}
              {sortHeader('member_count', 'Members', 'w-28', 'right')}
              {sortHeader('status', 'Status', 'w-28')}
              <th className="w-12" scope="col"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {isLoading && Array.from({ length: 6 }).map((_, i) => <RowSkeleton key={i} />)}
            {!isLoading && items.length === 0 && <tr><td colSpan={7}>{emptyState}</td></tr>}
            {!isLoading && items.map((a) => {
              const isSelected = selected.has(a.id)
              return (
                <tr key={a.id} className={`group transition-colors hover:bg-zinc-900/50 ${isSelected ? 'bg-violet-950/20' : ''}`}>
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      aria-label={`Select ${a.name}`}
                      checked={isSelected}
                      onChange={() => toggleSelect(a.id)}
                      className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                    />
                  </td>
                  <td className="p-0">
                    <Link to="/alliances/$id" params={{ id: a.slug ?? a.id }} className="flex min-h-[52px] items-center gap-3 px-3 py-2">
                      <SetAvatar name={a.name} thumbUrl={a.primary_photo_thumb_url} gangColor={a.gang_color} size="sm" />
                      <AllianceName alliance={a} />
                    </Link>
                  </td>
                  <td className="hidden px-3 py-2 md:table-cell">
                    {a.gang_name ? <GangPill name={a.gang_name} /> : <span className="text-xs text-zinc-600" aria-label="None">-</span>}
                  </td>
                  <td className="px-3 py-2 text-right"><Count n={a.set_count} icon={Shield} label="set" /></td>
                  <td className="px-3 py-2 text-right"><Count n={a.member_count} icon={Users} label="current member" /></td>
                  <td className="px-3 py-2"><AllianceStatusBadge status={a.status} /></td>
                  <td className="pr-2 text-right">
                    <RowActions alliance={a} onEdit={() => setEditingId(a.id)} onDelete={() => setDeleting(a)} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <AllianceFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingId && <EditAllianceSheet key={editingId} id={editingId} universeId={universe.id} onClose={() => setEditingId(null)} />}

      <BulkActionBar count={selectedShown.length} label="alliance" onClear={() => setSelected(new Set())}>
        <Button size="sm" variant="destructive" className="h-7 text-xs" onClick={() => setConfirmingBulkDelete(true)} disabled={bulkDeleting}>
          <Trash2 className="mr-1 h-3 w-3" />Delete
        </Button>
      </BulkActionBar>

      <ConfirmDialog
        open={confirmingBulkDelete}
        title={`Delete ${plural(selectedShown.length, 'alliance')}?`}
        description="This cannot be undone. Their sets and members stay, unaffiliated."
        impact={impact(selectedShown)}
        confirmLabel="Delete"
        destructive
        pending={bulkDeleting}
        onConfirm={bulkDelete}
        onCancel={() => setConfirmingBulkDelete(false)}
      />
      <ConfirmDialog
        open={!!deleting}
        title={`Delete "${deleting?.name ?? ''}"?`}
        description="This cannot be undone. Its sets and members stay, unaffiliated."
        impact={deleting ? impact([deleting]) : undefined}
        confirmLabel="Delete"
        destructive
        pending={deleteAlliance.isPending}
        onConfirm={() => deleting && deleteOne(deleting)}
        onCancel={() => setDeleting(null)}
      />
    </div>
  )
}
