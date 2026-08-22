import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Mic, Pencil, Plus, Search, Users, X } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  useMembers, useMemberSearch,
  useSets, useBulkMemberStatus,
  useUniverseAnalytics,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import { currentAffiliations, primaryAffiliation } from '@/lib/utils'
import { useDebounce } from '@/hooks/useDebounce'
import { MemberRowSkeleton } from '@/components/skeletons'
import { MemberStatusBadge } from '@/components/StatusBadge'
import {
  MemberFormSheet,
  EditMemberSheet,
} from '@/components/members/MemberFormSheet'
import type { MemberListItem, MemberStatus } from '@/lib/types'

// Re-export so existing import paths keep working.
export {
  MemberFormSheet,
  familyDictToEntries,
  familyEntriesToDict,
  FAMILY_ROLES,
  ROLE_LABEL,
} from '@/components/members/MemberFormSheet'
export type { FamilyRole, FamilyEntry } from '@/components/members/MemberFormSheet'

export const Route = createFileRoute('/_app/members/')({
  component: MembersPage,
})

// ─── Status styling ───────────────────────────────────────────────────────────

const STATUS_DOT: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-400',
  LOCKED: 'bg-orange-400',
  DEAD: 'bg-zinc-600',
  UNKNOWN: 'bg-zinc-600',
  ESCAPEE: 'bg-amber-400',
  ABSCONDER: 'bg-yellow-400',
}

const STATUS_CHIP_ACTIVE: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-900/60 text-emerald-300 border-emerald-700',
  LOCKED: 'bg-orange-900/60 text-orange-300 border-orange-700',
  DEAD: 'bg-zinc-800 text-zinc-400 border-zinc-600',
  UNKNOWN: 'bg-zinc-800 text-zinc-400 border-zinc-600',
  ESCAPEE: 'bg-amber-900/60 text-amber-300 border-amber-700',
  ABSCONDER: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
}

const ALL_STATUSES: MemberStatus[] = ['FREE', 'LOCKED', 'ESCAPEE', 'ABSCONDER', 'DEAD', 'UNKNOWN']

// ─── Main page ────────────────────────────────────────────────────────────────

function MembersPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)
  const [editingMemberId, setEditingMemberId] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkStatus, setBulkStatus] = useState<MemberStatus>('FREE')
  const [statusFilter, setStatusFilter] = useState<MemberStatus | null>(null)
  const [setFilter, setSetFilter] = useState<string>('')
  const [sortKey, setSortKey] = useState<'display_name' | 'status' | null>('display_name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const bulkUpdate = useBulkMemberStatus(universe?.id ?? '')

  const debouncedQ = useDebounce(q, 250)
  const { data, isLoading } = useMembers(universe?.id ?? null, cursor)
  const { data: searchResults, isLoading: searchLoading } = useMemberSearch(universe?.id ?? null, debouncedQ)
  const { data: setsData } = useSets(universe?.id ?? null)
  const { data: analytics } = useUniverseAnalytics(universe?.id ?? null)

  const isSearching = debouncedQ.length >= 2
  const baseItems = isSearching ? (searchResults ?? []) : (data?.items ?? [])

  // While searching, count from results; otherwise use universe-wide analytics
  // so pills don't reflect just the current cursor page.
  const statusCounts = useMemo(() => {
    if (isSearching) {
      const counts: Partial<Record<MemberStatus, number>> = {}
      for (const m of baseItems) counts[m.status] = (counts[m.status] ?? 0) + 1
      return counts
    }
    return (analytics?.member_by_status ?? {}) as Partial<Record<MemberStatus, number>>
  }, [analytics, baseItems, isSearching])

  const items: MemberListItem[] = useMemo(() => {
    let list = baseItems
    if (statusFilter) list = list.filter((m) => m.status === statusFilter)
    if (setFilter)
      list = list.filter((m) =>
        currentAffiliations(m.affiliations).some((a) => a.set_id === setFilter),
      )
    if (!sortKey) return list
    return [...list].sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [baseItems, statusFilter, setFilter, sortKey, sortDir])

  // Virtualize the desktop table tbody when the list grows past 50 rows.
  const tableScrollRef = useRef<HTMLDivElement | null>(null)
  const isVirtualized = items.length > 50
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 56,
    overscan: 8,
  })
  const virtualRows = isVirtualized ? rowVirtualizer.getVirtualItems() : []
  const virtualPaddingTop = virtualRows[0]?.start ?? 0
  const virtualPaddingBottom = isVirtualized
    ? rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)
    : 0

  if (!universe) return <NoUniverse />

  const total = data?.total
  const listLoading = isSearching ? searchLoading : isLoading

  function toggleSort(key: 'display_name' | 'status') {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
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

  const hasFilters = statusFilter || setFilter
  const hasSelection = selected.size > 0
  const universeSlug = universe.slug

  function exportFilename() {
    const date = new Date().toISOString().slice(0, 10)
    return `members-${universeSlug}-${date}.csv`
  }

  return (
    <div className={hasSelection ? 'pb-28' : 'pb-20'}>
      {/* Header */}
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Members</h1>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-400">
            {total != null && <span>{total} total</span>}
            {(statusCounts.FREE ?? 0) > 0 && <span className="text-emerald-500">{statusCounts.FREE} free</span>}
            {(statusCounts.LOCKED ?? 0) > 0 && <span className="text-orange-400">{statusCounts.LOCKED} locked</span>}
            {(statusCounts.DEAD ?? 0) > 0 && <span>{statusCounts.DEAD} dead</span>}
            {(statusCounts.ESCAPEE ?? 0) > 0 && <span className="text-amber-400">{statusCounts.ESCAPEE} escaped</span>}
          </div>
        </div>
        <Button size="sm" onClick={() => setCreating(true)}>
          <Plus className="mr-1.5 h-4 w-4" />Add Member
        </Button>
      </div>

      {/* Status filter chips */}
      {!isLoading && baseItems.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-1.5">
          {ALL_STATUSES.filter((s) => (statusCounts[s] ?? 0) > 0).map((s) => {
            const active = statusFilter === s
            return (
              <button
                key={s}
                onClick={() => setStatusFilter(active ? null : s)}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all ${
                  active ? STATUS_CHIP_ACTIVE[s] : 'border-zinc-800 bg-zinc-900/40 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300'
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[s]}`} />
                {s}
                <span className={active ? 'opacity-70' : 'opacity-50'}>{statusCounts[s]}</span>
              </button>
            )
          })}
          {hasFilters && (
            <button
              onClick={() => { setStatusFilter(null); setSetFilter('') }}
              className="flex items-center gap-1 rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-400 hover:text-white transition-colors"
            >
              <X className="h-3 w-3" /> Clear filters
            </button>
          )}
        </div>
      )}

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input className="pl-8 h-8 text-sm" placeholder="Search members…" value={q} onChange={(e) => { setQ(e.target.value); setCursor(undefined) }} />
        </div>
        <Select value={setFilter || 'all'} onValueChange={(v) => setSetFilter(v === 'all' ? '' : v)}>
          <SelectTrigger className="h-8 w-36 text-xs"><SelectValue placeholder="All sets" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all" className="text-xs">All sets</SelectItem>
            {(setsData?.items ?? []).map((s) => (
              <SelectItem key={s.id} value={s.id} className="text-xs">{s.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline" size="sm" className="h-8" onClick={() => downloadCsv(`/members/?universe_id=${universe.id}&format=csv`, exportFilename())}>
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      {/* Table — hidden on narrow viewports */}
      <div
        ref={tableScrollRef}
        className="hidden rounded-lg border border-zinc-800 sm:block"
        style={isVirtualized
          ? { maxHeight: 'calc(100vh - 18rem)', overflowY: 'auto' }
          : { overflow: 'hidden' }}
      >
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-zinc-800 bg-zinc-900/90 backdrop-blur">
              <th className="w-10 px-3 py-2.5" scope="col">
                <input
                  id="members-select-all"
                  type="checkbox"
                  aria-label="Select all members"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={toggleAll}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              <th className="px-3 py-2.5 text-left" scope="col" aria-sort={sortKey === 'display_name' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <button onClick={() => toggleSort('display_name')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white">
                  Name <span className="text-zinc-400" aria-hidden>{sortKey === 'display_name' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
              <th className="hidden px-3 py-2.5 text-left sm:table-cell" scope="col">
                <span className="text-xs font-medium text-zinc-400">Set</span>
              </th>
              <th className="px-3 py-2.5 text-left" scope="col" aria-sort={sortKey === 'status' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <button onClick={() => toggleSort('status')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white">
                  Status <span className="text-zinc-400" aria-hidden>{sortKey === 'status' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
              <th className="w-8 px-3 py-2.5" scope="col" aria-label="Actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {listLoading
              ? Array.from({ length: 8 }).map((_, i) => <MemberRowSkeleton key={i} />)
              : isVirtualized && virtualPaddingTop > 0
                ? <tr aria-hidden><td colSpan={5} style={{ height: virtualPaddingTop }} /></tr>
                : null}
            {!listLoading && (isVirtualized ? virtualRows.map((vRow) => items[vRow.index]) : items).map((member, idx) => {
                  const linkId = member.slug ?? member.id
                  const currentAffs = currentAffiliations(member.affiliations)
                  const primaryAff = primaryAffiliation(member.affiliations)
                  const extraCount = currentAffs.length - 1
                  const isDead = member.status === 'DEAD'
                  const measureRef = isVirtualized ? rowVirtualizer.measureElement : undefined
                  const dataIndex = isVirtualized ? virtualRows[idx]?.index : undefined
                  return (
                    <tr key={member.id} ref={measureRef} data-index={dataIndex} className={`group transition-colors hover:bg-zinc-900/40 ${selected.has(member.id) ? 'bg-violet-950/20' : ''} ${isDead ? 'opacity-60' : ''}`}>
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          aria-label={`Select ${member.display_name}`}
                          checked={selected.has(member.id)}
                          onChange={() => toggleSelect(member.id)}
                          className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                        />
                      </td>
                      <td className="p-0">
                        <Link to="/members/$id" params={{ id: linkId }} className="block px-3 py-3 transition-colors group-hover:text-violet-400">
                          <span className={`font-medium ${isDead ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'}`}>{member.display_name}</span>{member.is_rapper && <Mic aria-label="Rapper" className="ml-1.5 inline h-3 w-3 align-baseline text-fuchsia-400" />}
                          {member.aliases && member.aliases.length > 0 && (
                            <span className="mt-0.5 block text-[11px] text-zinc-400 group-hover:text-zinc-200 transition-colors">
                              {member.aliases.slice(0, 3).join(' · ')}
                            </span>
                          )}
                        </Link>
                      </td>
                      <td className="hidden px-3 py-3 sm:table-cell">
                        {primaryAff ? (
                          <span className="inline-flex flex-wrap items-center gap-1">
                            <Link to="/sets/$id" params={{ id: primaryAff.set_slug ?? primaryAff.set_id }} className="inline-flex items-center rounded-full bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors ring-1 ring-transparent ring-inset [.is-primary_&]:ring-violet-700/40">
                              {primaryAff.set_name}
                            </Link>
                            {extraCount > 0 && (
                              <span className="inline-flex items-center rounded-full bg-zinc-800/40 px-1.5 py-0.5 text-[10px] text-zinc-400" title={currentAffiliations(member.affiliations).filter((a) => !a.is_primary).map((a) => a.set_name).join(', ')}>
                                +{extraCount}
                              </span>
                            )}
                          </span>
                        ) : <span className="text-xs text-zinc-500">—</span>}
                      </td>
                      <td className="px-3 py-3">
                        <MemberStatusBadge status={member.status} />
                      </td>
                      <td className="px-3 py-3">
                        <button
                          type="button"
                          aria-label={`Edit ${member.display_name}`}
                          onClick={(e) => { e.preventDefault(); e.stopPropagation(); setEditingMemberId(member.id) }}
                          className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
            {!listLoading && isVirtualized && virtualPaddingBottom > 0 && (
              <tr aria-hidden><td colSpan={5} style={{ height: virtualPaddingBottom }} /></tr>
            )}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <div className="flex flex-col items-center py-14 text-center">
                    <Users className="mb-3 h-8 w-8 text-zinc-500" />
                    <p className="text-sm text-zinc-400">
                      {q ? 'No members match your search' : hasFilters ? 'No members match these filters' : 'No members yet'}
                    </p>
                    {!q && !hasFilters && (
                      <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Add the first member →</button>
                    )}
                    {hasFilters && (
                      <button onClick={() => { setStatusFilter(null); setSetFilter('') }} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Clear filters</button>
                    )}
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards — shown below sm */}
      <div className="space-y-2 sm:hidden">
        {listLoading ? (
          Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-lg" />)
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center rounded-lg border border-zinc-800 py-12 text-center">
            <Users className="mb-3 h-8 w-8 text-zinc-500" />
            <p className="text-sm text-zinc-400">
              {q ? 'No members match your search' : hasFilters ? 'No members match these filters' : 'No members yet'}
            </p>
            {!q && !hasFilters && (
              <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Add the first member →</button>
            )}
            {hasFilters && (
              <button onClick={() => { setStatusFilter(null); setSetFilter('') }} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Clear filters</button>
            )}
          </div>
        ) : (
          items.map((member) => {
            const linkId = member.slug ?? member.id
            const currentAffsMobile = currentAffiliations(member.affiliations)
            const primaryAffMobile = primaryAffiliation(member.affiliations)
            const extraCountMobile = currentAffsMobile.length - 1
            const isDead = member.status === 'DEAD'
            const isSelected = selected.has(member.id)
            return (
              <div
                key={member.id}
                className={`relative rounded-lg border bg-zinc-900/30 p-3 ${
                  isSelected ? 'border-violet-700 bg-violet-950/20' : 'border-zinc-800'
                } ${isDead ? 'opacity-60' : ''}`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    aria-label={`Select ${member.display_name}`}
                    checked={isSelected}
                    onChange={() => toggleSelect(member.id)}
                    className="mt-1 rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                  />
                  <div className="min-w-0 flex-1">
                    <Link
                      to="/members/$id"
                      params={{ id: linkId }}
                      className="block"
                    >
                      <span className={`font-medium ${isDead ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'}`}>
                        {member.display_name}
                      </span>
                      {member.is_rapper && <Mic aria-label="Rapper" className="ml-1.5 inline h-3 w-3 align-baseline text-fuchsia-400" />}
                      {member.aliases && member.aliases.length > 0 && (
                        <span className="mt-0.5 block text-[11px] text-zinc-400">
                          {member.aliases.slice(0, 3).join(' · ')}
                        </span>
                      )}
                    </Link>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <MemberStatusBadge status={member.status} />
                      {primaryAffMobile && (
                        <>
                          <Link
                            to="/sets/$id"
                            params={{ id: primaryAffMobile.set_slug ?? primaryAffMobile.set_id }}
                            className="inline-flex items-center rounded-full bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors"
                          >
                            {primaryAffMobile.set_name}
                          </Link>
                          {extraCountMobile > 0 && (
                            <span className="inline-flex items-center rounded-full bg-zinc-800/40 px-1.5 py-0.5 text-[10px] text-zinc-400" title={currentAffiliations(member.affiliations).filter((a) => !a.is_primary).map((a) => a.set_name).join(', ')}>
                              +{extraCountMobile}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    aria-label={`Edit ${member.display_name}`}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); setEditingMemberId(member.id) }}
                    className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-400"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Load more */}
      {!q && data?.next_cursor && (
        <div className="mt-4 flex items-center justify-between text-xs text-zinc-400">
          {total != null && items.length > 0 && <span>Showing {items.length} of {total}</span>}
          <Button variant="outline" size="sm" onClick={() => setCursor(data.next_cursor ?? undefined)}>Load more</Button>
        </div>
      )}

      {/* Bulk action bar */}
      {selected.size > 0 && (
        <div
          className="fixed left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 shadow-2xl shadow-black/50"
          style={{ bottom: 'max(1.5rem, env(safe-area-inset-bottom))' }}
          role="region"
          aria-label="Bulk actions for selected members"
        >
          <span className="text-sm font-medium text-white">{selected.size} selected</span>
          <div className="h-4 w-px bg-zinc-700" />
          <span className="text-xs text-zinc-400">Set status:</span>
          <Select value={bulkStatus} onValueChange={(v) => setBulkStatus(v as MemberStatus)}>
            <SelectTrigger className="h-7 w-28 text-xs border-zinc-700 bg-zinc-800"><SelectValue /></SelectTrigger>
            <SelectContent>
              {ALL_STATUSES.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button size="sm" className="h-7 text-xs" onClick={applyBulkStatus} disabled={bulkUpdate.isPending}>
            {bulkUpdate.isPending ? 'Applying…' : 'Apply'}
          </Button>
          <button onClick={() => setSelected(new Set())} className="text-zinc-400 hover:text-white transition-colors">
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
