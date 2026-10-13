import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { MapPin, Mic, Plus, Search, Users, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '@/components/EmptyState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useDebounce } from '@/hooks/useDebounce'
import { useRapGroups } from '@/lib/queries'
import { nonPrimaryVariantsText, variantExtras, variantsSearchText } from '@/lib/setDisplay'
import type { RapGroupKind, RapGroupListItem, RapGroupStatus } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import {
  RAP_KIND_LABEL, RAP_STATUS_LABEL, RapGroupFormSheet, type RapGroupSortKey, type RapGroupsSearch,
} from './_app.$universe.rap-groups.index'
import { SetAvatar } from './_app.$universe.sets.index'

// The Rap groups & labels list, in its own chunk; the route file keeps
// validateSearch and the form sheet, which the detail page imports.
export const Route = createLazyFileRoute('/_app/$universe/rap-groups/')({
  component: RapGroupsPage,
})

const KINDS: RapGroupKind[] = ['GROUP', 'LABEL']
const KIND_TAB_LABEL: Record<RapGroupKind, string> = { GROUP: 'Groups', LABEL: 'Labels' }
const STATUSES: RapGroupStatus[] = ['ACTIVE', 'DISBANDED']
const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

function haystack(g: RapGroupListItem): string {
  return fold([g.name, variantsSearchText(g.name_variants), g.municipality?.name].filter(Boolean).join(' '))
}

function GroupName({ group }: { group: RapGroupListItem }) {
  const primary = group.name_variants?.find((v) => v.is_primary)
  const extras = primary ? variantExtras(primary).map((e) => e.value) : []
  const aka = [...extras, nonPrimaryVariantsText(group.name_variants)].filter(Boolean).join(' · ')
  return (
    <span className="block min-w-0">
      <span className="block truncate font-medium text-white transition-colors group-hover:text-fuchsia-300">{group.name}</span>
      {aka && <span className="block truncate text-[11px] text-zinc-500">{aka}</span>}
    </span>
  )
}

function KindPill({ kind }: { kind: RapGroupKind }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] ring-1 ${
      kind === 'LABEL' ? 'bg-sky-950/50 text-sky-300 ring-sky-800/60' : 'bg-fuchsia-950/50 text-fuchsia-300 ring-fuchsia-800/60'
    }`}>
      <Mic className="h-3 w-3" aria-hidden />{RAP_KIND_LABEL[kind]}
    </span>
  )
}

function Years({ group }: { group: RapGroupListItem }) {
  if (!group.active_from && !group.active_to) return <span className="text-xs text-zinc-600" aria-label="None">-</span>
  return (
    <span className="text-xs tabular-nums text-zinc-400">
      {group.active_from ? <FuzzyDate value={group.active_from} /> : '?'} to {group.active_to ? <FuzzyDate value={group.active_to} /> : 'present'}
    </span>
  )
}

function RowSkeleton() {
  return (
    <tr aria-hidden className="h-[53px]">
      <td className="px-3">
        <span className="flex items-center gap-3">
          <Skeleton className="h-7 w-7 shrink-0 rounded-md" />
          <Skeleton className="h-3.5 w-32" />
        </span>
      </td>
      <td className="hidden px-3 md:table-cell"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td className="hidden px-3 lg:table-cell"><Skeleton className="h-3.5 w-24" /></td>
      <td className="px-3"><Skeleton className="ml-auto h-3.5 w-8" /></td>
      <td className="px-3"><Skeleton className="h-5 w-16 rounded-full" /></td>
    </tr>
  )
}

function StatusText({ status }: { status: RapGroupStatus }) {
  return <span className={`text-xs ${status === 'ACTIVE' ? 'text-emerald-300' : 'text-zinc-400'}`}>{RAP_STATUS_LABEL[status]}</span>
}

function RapGroupsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const search = Route.useSearch()
  const navigate = useNavigate({ from: '/$universe/rap-groups/' })

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
  const kind = search.kind
  const status = search.status
  const sort: RapGroupSortKey = search.sort ?? 'name'
  const order = search.order ?? (sort === 'member_count' ? 'desc' : 'asc')

  const { data, isLoading } = useRapGroups(universeId)
  const all = useMemo(() => data?.items ?? [], [data])
  const haystacks = useMemo(() => new Map(all.map((g) => [g.id, haystack(g)])), [all])

  // The kind tabs count what the search leaves, so each says what clicking it shows.
  const { kindCounts, searched } = useMemo(() => {
    const terms = fold(q.trim()).split(/\s+/).filter(Boolean)
    const counts: Record<RapGroupKind, number> = { GROUP: 0, LABEL: 0 }
    const hits = all.filter((g) => {
      const hay = haystacks.get(g.id) ?? ''
      if (!terms.every((t) => hay.includes(t))) return false
      if (status && g.status !== status) return false
      counts[g.kind]++
      return true
    })
    return { kindCounts: counts, searched: hits }
  }, [all, haystacks, q, status])

  const items = useMemo(() => {
    const dir = order === 'asc' ? 1 : -1
    const byName = (a: RapGroupListItem, b: RapGroupListItem) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base', numeric: true })
    const list = kind ? searched.filter((g) => g.kind === kind) : searched
    return [...list].sort((a, b) => {
      switch (sort) {
        case 'status': return (STATUSES.indexOf(a.status) - STATUSES.indexOf(b.status)) * dir || byName(a, b)
        case 'member_count': return (a.member_count - b.member_count) * dir || byName(a, b)
        default: return byName(a, b) * dir
      }
    })
  }, [searched, kind, sort, order])

  if (!universe) return <NoUniverse />

  const hasFilters = !!kind || !!status || !!q.trim()

  function patch(next: Partial<RapGroupsSearch>) {
    navigate({
      search: (prev) => {
        const merged: RapGroupsSearch = { ...prev, ...next }
        for (const k of Object.keys(merged) as (keyof RapGroupsSearch)[]) {
          if (merged[k] === undefined) delete merged[k]
        }
        return merged
      },
      replace: true,
    })
  }

  function toggleSort(key: RapGroupSortKey) {
    if (sort === key) patch({ order: order === 'asc' ? 'desc' : 'asc' })
    else patch({ sort: key === 'name' ? undefined : key, order: undefined })
  }

  function clearFilters() {
    setQ('')
    navigate({ search: (prev) => ({ sort: prev.sort, order: prev.order }), replace: true })
  }

  function sortHeader(key: RapGroupSortKey, label: string, className = '', align: 'left' | 'right' = 'left') {
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
      icon={Mic}
      title={hasFilters ? 'Nothing matches these filters' : 'No rap groups or labels yet'}
      description={hasFilters ? undefined : 'A rap group is not a set: its members keep their real set.'}
      action={hasFilters
        ? <Button size="sm" variant="outline" onClick={clearFilters}>Clear search and filters</Button>
        : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add the first one</Button>}
    />
  )

  const searchedTotal = kindCounts.GROUP + kindCounts.LABEL

  return (
    <div className="pb-8">
      <PageHeader
        title="Rap groups & labels"
        description={
          isLoading ? 'Loading…'
            : all.length === 0 ? 'None yet'
            : hasFilters ? `${items.length} of ${all.length}`
            : `${plural(all.filter((g) => g.kind === 'GROUP').length, 'group')} · ${plural(all.filter((g) => g.kind === 'LABEL').length, 'label')}`
        }
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add</Button>}
      />

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            className="h-9 pl-8 pr-8 text-sm"
            placeholder="Search name or alias…"
            aria-label="Search rap groups and labels"
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

        <div className="flex h-9 items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="group" aria-label="Kind">
          {([undefined, ...KINDS] as const).map((k) => {
            const active = kind === k
            const n = k ? kindCounts[k] : searchedTotal
            return (
              <button
                key={k ?? 'all'}
                onClick={() => patch({ kind: k })}
                aria-pressed={active}
                className={`flex h-full items-center gap-1.5 rounded-md px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fuchsia-500/60 ${
                  active ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {k ? KIND_TAB_LABEL[k] : 'All'}
                {!isLoading && <span className={`tabular-nums ${active ? 'text-zinc-300' : 'text-zinc-500'}`}>{n}</span>}
              </button>
            )
          })}
        </div>

        <div className="flex h-9 items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="group" aria-label="Status">
          {([undefined, ...STATUSES] as const).map((s) => {
            const active = status === s
            return (
              <button
                key={s ?? 'any'}
                onClick={() => patch({ status: s })}
                aria-pressed={active}
                className={`flex h-full items-center rounded-md px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fuchsia-500/60 ${
                  active ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {s ? RAP_STATUS_LABEL[s] : 'Any status'}
              </button>
            )
          })}
        </div>

        {hasFilters && (
          <button onClick={clearFilters} className="inline-flex h-9 items-center gap-1 rounded-md px-2 text-xs text-zinc-400 transition-colors hover:text-white">
            <X className="h-3 w-3" /> Clear
          </button>
        )}
      </div>

      {/* Phone: rows, with the counts under the name. */}
      <div className="space-y-2 sm:hidden">
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-[62px] w-full rounded-lg" />)
          : items.length === 0 ? emptyState
          : items.map((g) => (
              <Link
                key={g.id}
                from="/$universe" to="/$universe/rap-groups/$id"
                params={{ id: g.slug ?? g.id }}
                className="group flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2.5 transition-colors active:bg-zinc-800/60"
              >
                <SetAvatar name={g.name} thumbUrl={g.primary_photo_url} />
                <span className="min-w-0 flex-1 text-sm">
                  <GroupName group={g} />
                  <span className="mt-0.5 flex items-center gap-3 text-[11px] text-zinc-400">
                    <span className="inline-flex items-center gap-1 tabular-nums"><Users className="h-3 w-3" aria-hidden />{g.member_count}</span>
                    {g.municipality && <span className="inline-flex items-center gap-1 truncate"><MapPin className="h-3 w-3" aria-hidden />{g.municipality.name}</span>}
                  </span>
                </span>
                <KindPill kind={g.kind} />
              </Link>
            ))}
      </div>

      <div className="hidden overflow-hidden rounded-lg border border-zinc-800 sm:block">
        <table className="w-full table-fixed text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/60">
              {sortHeader('name', 'Name')}
              <th scope="col" className="hidden w-28 px-3 py-2.5 text-left text-xs font-medium text-zinc-400 md:table-cell">Kind</th>
              <th scope="col" className="hidden w-[22%] px-3 py-2.5 text-left text-xs font-medium text-zinc-400 lg:table-cell">Home area and years</th>
              {sortHeader('member_count', 'Members', 'w-28', 'right')}
              {sortHeader('status', 'Status', 'w-28')}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {isLoading && Array.from({ length: 6 }).map((_, i) => <RowSkeleton key={i} />)}
            {!isLoading && items.length === 0 && <tr><td colSpan={5}>{emptyState}</td></tr>}
            {!isLoading && items.map((g) => (
              <tr key={g.id} className="group transition-colors hover:bg-zinc-900/50">
                <td className="p-0">
                  <Link from="/$universe" to="/$universe/rap-groups/$id" params={{ id: g.slug ?? g.id }} className="flex min-h-[52px] items-center gap-3 px-3 py-2">
                    <SetAvatar name={g.name} thumbUrl={g.primary_photo_url} size="sm" />
                    <GroupName group={g} />
                  </Link>
                </td>
                <td className="hidden px-3 py-2 md:table-cell"><KindPill kind={g.kind} /></td>
                <td className="hidden px-3 py-2 lg:table-cell">
                  <span className="block truncate text-xs text-zinc-300">{g.municipality?.name ?? ''}</span>
                  <Years group={g} />
                </td>
                <td className="px-3 py-2 text-right">
                  <span title={plural(g.member_count, 'member')} className={`inline-flex items-center gap-1 text-xs tabular-nums ${g.member_count === 0 ? 'text-zinc-600' : 'text-zinc-300'}`}>
                    <Users className="h-3 w-3" aria-hidden />{g.member_count.toLocaleString()}
                  </span>
                </td>
                <td className="px-3 py-2"><StatusText status={g.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <RapGroupFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} defaultKind={kind} />
    </div>
  )
}
