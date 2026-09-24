import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Download, ExternalLink, FileText, MoreVertical, Pencil, Plus, Search, ShieldAlert, Trash2, Users, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Sheet, SheetContent } from '@/components/Sheet'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useDebounce } from '@/hooks/useDebounce'
import { downloadCsv } from '@/lib/download'
import { useAllSources, useDeleteSource, useSource } from '@/lib/queries'
import { RELIABILITY_DESCRIPTION } from '@/lib/statusColors'
import type { SourceListItem, SourceReliability, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import { SourceFormSheet, type SourceSortKey, type SourcesSearch } from './_app.sources.index'

// The Sources list, in its own chunk; the route file keeps validateSearch and
// the form sheet, which half the app imports.
export const Route = createLazyFileRoute('/_app/sources/')({
  component: SourcesPage,
})

const RELIABILITIES: SourceReliability[] = ['HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED']
const RELIABILITY_LABEL: Record<SourceReliability, string> = { HIGH: 'High', MEDIUM: 'Medium', LOW: 'Low', UNVERIFIED: 'Unverified' }
const RELIABILITY_DOT: Record<SourceReliability, string> = {
  HIGH: 'bg-emerald-400', MEDIUM: 'bg-sky-400', LOW: 'bg-amber-400', UNVERIFIED: 'bg-zinc-500',
}
/** Dates and citation counts read best newest or biggest first. */
const DESC_FIRST: SourceSortKey[] = ['added', 'published', 'cited']
const ALL = '__all__'
const NO_PUBLICATION = '__none__'
const STEP = 60

const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

function domainOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

/** Records other than incidents and members that cite it: sets, businesses, custody numbers, aliases. */
const otherCitations = (s: SourceListItem) => s.set_count + s.business_count + s.custody_count + s.alias_count
const citations = (s: SourceListItem) => s.incident_count + s.member_count + otherCitations(s)

function dateKey(d: FuzzyDateValue | null): string {
  if (!d?.year) return ''
  return `${String(d.year).padStart(4, '0')}-${String(d.month ?? 0).padStart(2, '0')}-${String(d.day ?? 0).padStart(2, '0')}`
}

const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

// ─── Pieces ───────────────────────────────────────────────────────────────────

function Citations({ s }: { s: SourceListItem }) {
  const other = otherCitations(s)
  if (citations(s) === 0) return <span className="text-xs text-zinc-600" title="Nothing cites this source">Uncited</span>
  return (
    <span className="inline-flex items-center gap-2.5 text-xs tabular-nums text-zinc-300">
      {s.incident_count > 0 && (
        <span className="inline-flex items-center gap-1" title={plural(s.incident_count, 'incident')}>
          <ShieldAlert className="h-3 w-3 text-zinc-500" aria-hidden />{s.incident_count}
        </span>
      )}
      {s.member_count > 0 && (
        <span className="inline-flex items-center gap-1" title={plural(s.member_count, 'member')}>
          <Users className="h-3 w-3 text-zinc-500" aria-hidden />{s.member_count}
        </span>
      )}
      {other > 0 && (
        <span className="text-zinc-500" title={[
          s.set_count && plural(s.set_count, 'set'),
          s.business_count && plural(s.business_count, 'business'),
          s.custody_count && plural(s.custody_count, 'custody number'),
          s.alias_count && plural(s.alias_count, 'alias'),
        ].filter(Boolean).join(', ')}>+{other}</span>
      )}
    </span>
  )
}

function SourceTitle({ s }: { s: SourceListItem }) {
  const meta = [s.publication, domainOf(s.url)].filter((x, i, a) => x && a.indexOf(x) === i).join(' · ')
  return (
    <span className="block min-w-0">
      <span className="block truncate font-medium text-white transition-colors group-hover:text-violet-300">{s.title}</span>
      <span className="block truncate text-[11px] text-zinc-500">{meta}</span>
    </span>
  )
}

function RowActions({ s, onEdit, onDelete }: { s: SourceListItem; onEdit: () => void; onDelete: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button aria-label={`Actions for ${s.title}`} className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50">
          <MoreVertical className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem asChild>
          <a href={s.url} target="_blank" rel="noopener noreferrer"><ExternalLink className="mr-2 h-3.5 w-3.5" />Open original</a>
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={onEdit}><Pencil className="mr-2 h-3.5 w-3.5" />Edit</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onDelete} className="text-red-400 focus:bg-red-950/40 focus:text-red-300">
          <Trash2 className="mr-2 h-3.5 w-3.5" />Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** The list row lacks notes and archive URL, so edit loads the full source first. */
function EditSourceSheet({ id, universeId, onClose }: { id: UUID; universeId: UUID; onClose: () => void }) {
  const { data } = useSource(id, universeId)
  if (!data) {
    return (
      <Sheet open onOpenChange={(v) => !v && onClose()}>
        <SheetContent title="Edit Source" description="Loading…">
          <div className="space-y-3 pt-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        </SheetContent>
      </Sheet>
    )
  }
  return <SourceFormSheet universeId={universeId} open onClose={onClose} initial={data} />
}

function RowSkeleton() {
  return (
    <tr aria-hidden className="h-[53px]">
      <td className="px-3"><Skeleton className="h-3.5 w-3.5 rounded-sm" /></td>
      <td className="px-3"><Skeleton className="h-3.5 w-64" /></td>
      <td className="hidden px-3 md:table-cell"><Skeleton className="h-3.5 w-20" /></td>
      <td className="px-3"><Skeleton className="h-3.5 w-12" /></td>
      <td className="px-3"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td />
    </tr>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function SourcesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const search = Route.useSearch()
  const navigate = useNavigate({ from: '/sources/' })

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
  const [deleting, setDeleting] = useState<SourceListItem | null>(null)
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [selected, setSelected] = useState<Set<UUID>>(new Set())

  const { reliability, publication, uncited } = search
  const sort: SourceSortKey = search.sort ?? 'added'
  const order = search.order ?? (DESC_FIRST.includes(sort) ? 'desc' : 'asc')

  const { data, isLoading } = useAllSources(universeId)
  const deleteSource = useDeleteSource(universe?.id ?? '')
  const all = useMemo(() => data?.items ?? [], [data])
  const haystacks = useMemo(
    () => new Map(all.map((s) => [s.id, fold([s.title, s.publication, domainOf(s.url)].filter(Boolean).join(' '))])),
    [all],
  )

  // One pass: the list plus each facet's counts under the *other* filters, so
  // every count is what clicking it would show.
  const facets = useMemo(() => {
    const terms = fold(q.trim()).split(/\s+/).filter(Boolean)
    const relCounts: Record<SourceReliability | 'ALL', number> = { ALL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, UNVERIFIED: 0 }
    const pubCounts = new Map<string, number>()
    let uncitedCount = 0
    const shown: SourceListItem[] = []
    for (const s of all) {
      const hay = haystacks.get(s.id) ?? ''
      if (!terms.every((t) => hay.includes(t))) continue
      const pubKey = s.publication ?? NO_PUBLICATION
      const re = !reliability || s.reliability === reliability
      const pu = !publication || pubKey === publication
      const un = !uncited || citations(s) === 0
      if (pu && un) { relCounts.ALL++; relCounts[s.reliability]++ }
      if (re && un) pubCounts.set(pubKey, (pubCounts.get(pubKey) ?? 0) + 1)
      if (re && pu && citations(s) === 0) uncitedCount++
      if (re && pu && un) shown.push(s)
    }
    return { relCounts, pubCounts, uncitedCount, shown }
  }, [all, haystacks, q, reliability, publication, uncited])

  const items = useMemo(() => {
    const dir = order === 'asc' ? 1 : -1
    const byTitle = (a: SourceListItem, b: SourceListItem) => a.title.localeCompare(b.title, undefined, { sensitivity: 'base', numeric: true })
    return [...facets.shown].sort((a, b) => {
      switch (sort) {
        case 'title': return byTitle(a, b) * dir
        case 'reliability': return (RELIABILITIES.indexOf(a.reliability) - RELIABILITIES.indexOf(b.reliability)) * dir || byTitle(a, b)
        case 'cited': return (citations(a) - citations(b)) * dir || byTitle(a, b)
        case 'published': {
          // Undated sources sink to the bottom whichever way the column sorts.
          const ka = dateKey(a.published_at), kb = dateKey(b.published_at)
          if (!ka !== !kb) return ka ? -1 : 1
          return ka.localeCompare(kb) * dir || byTitle(a, b)
        }
        default: return a.created_at.localeCompare(b.created_at) * dir || byTitle(a, b)
      }
    })
  }, [facets.shown, sort, order])

  // Publications by how many sources each holds, so the busiest come first.
  const publicationOptions = useMemo(
    () => [...facets.pubCounts.entries()]
      .filter(([k]) => k !== NO_PUBLICATION)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])),
    [facets.pubCounts],
  )

  const selectedShown = useMemo(() => items.filter((s) => selected.has(s.id)), [items, selected])
  const allSelected = items.length > 0 && selectedShown.length === items.length

  const [limit, setLimit] = useState(STEP)
  const [limitFor, setLimitFor] = useState(items)
  if (limitFor !== items) {
    setLimitFor(items)
    setLimit(STEP)
  }

  const tableScrollRef = useRef<HTMLDivElement | null>(null)
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 53,
    overscan: 12,
  })
  const virtualRows = rowVirtualizer.getVirtualItems()
  const padTop = virtualRows[0]?.start ?? 0
  const padBottom = rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)

  if (!universe) return <NoUniverse />

  const hasFilters = !!reliability || !!publication || !!uncited || !!q.trim()
  const uncitedTotal = all.filter((s) => citations(s) === 0).length

  function patch(next: Partial<SourcesSearch>) {
    navigate({
      search: (prev) => {
        const merged: SourcesSearch = { ...prev, ...next }
        for (const k of Object.keys(merged) as (keyof SourcesSearch)[]) {
          if (merged[k] === undefined) delete merged[k]
        }
        return merged
      },
      replace: true,
    })
  }

  function toggleSort(key: SourceSortKey) {
    if (sort === key) patch({ order: order === 'asc' ? 'desc' : 'asc' })
    else patch({ sort: key === 'added' ? undefined : key, order: undefined })
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
    const results = await Promise.allSettled(targets.map((s) => deleteSource.mutateAsync(s.id)))
    const done = targets.filter((_, i) => results[i].status === 'fulfilled').map((s) => s.id)
    if (done.length > 0) toast.success(`Deleted ${plural(done.length, 'source')}`)
    setSelected((prev) => {
      const next = new Set(prev)
      for (const id of done) next.delete(id)
      return next
    })
    setBulkDeleting(false)
    setConfirmingBulkDelete(false)
  }

  async function deleteOne(s: SourceListItem) {
    try {
      await deleteSource.mutateAsync(s.id)
      toast.success(`Deleted "${s.title}"`)
    } finally {
      setDeleting(null)
    }
  }

  const impact = (list: SourceListItem[]) => {
    const inc = list.reduce((n, s) => n + s.incident_count, 0)
    const mem = list.reduce((n, s) => n + s.member_count, 0)
    const other = list.reduce((n, s) => n + otherCitations(s), 0)
    if (inc + mem + other === 0) return 'Nothing cites it.'
    const parts = [inc && plural(inc, 'incident'), mem && plural(mem, 'member'), other && plural(other, 'other record')].filter(Boolean)
    return `${parts.join(', ')} lose this citation.`
  }

  function sortHeader(key: SourceSortKey, label: string, className = '') {
    const sorted = sort === key
    return (
      <th scope="col" className={`px-3 py-2.5 text-left ${className}`} aria-sort={sorted ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}>
        <button onClick={() => toggleSort(key)}
          className={`inline-flex items-center gap-1 text-xs font-medium transition-colors hover:text-white focus-visible:text-white focus-visible:outline-none ${sorted ? 'text-zinc-200' : 'text-zinc-400'}`}>
          {label} <span className="text-zinc-500" aria-hidden>{sorted ? (order === 'asc' ? '↑' : '↓') : '↕'}</span>
        </button>
      </th>
    )
  }

  const emptyState = (
    <EmptyState
      icon={FileText}
      title={hasFilters ? 'No sources match these filters' : 'No sources yet'}
      description={hasFilters ? undefined : 'Add a citation to underpin the incidents you record.'}
      action={hasFilters
        ? <Button size="sm" variant="outline" onClick={clearFilters}>Clear search and filters</Button>
        : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add the first source</Button>}
    />
  )

  return (
    <div className={selectedShown.length > 0 ? 'pb-28' : 'pb-8'}>
      <PageHeader
        title="Sources"
        description={
          isLoading ? 'Loading…'
            : all.length === 0 ? 'No sources yet'
            : hasFilters ? `${items.length.toLocaleString()} of ${plural(all.length, 'source')}`
            : `${plural(all.length, 'source')} · ${uncitedTotal.toLocaleString()} uncited`
        }
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add source</Button>}
      />

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            className="h-9 pl-8 pr-8 text-sm"
            placeholder="Search title, publication or site…"
            aria-label="Search sources"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape' && q) { e.stopPropagation(); setQ('') } }}
          />
          {q && (
            <button type="button" aria-label="Clear search" onClick={() => setQ('')}
              className="absolute right-1.5 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-white">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* One row that scrolls sideways on a phone; flows normally from sm up. */}
        <div className="flex w-full items-center gap-2 overflow-x-auto [scrollbar-width:none] sm:contents [&::-webkit-scrollbar]:hidden [&>*]:shrink-0">
          <div className="flex h-9 items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="group" aria-label="Reliability">
            {([undefined, ...RELIABILITIES] as const).map((r) => {
              const active = reliability === r
              const n = facets.relCounts[r ?? 'ALL']
              if (r && n === 0 && !active && !isLoading) return null
              return (
                <button key={r ?? 'all'} onClick={() => patch({ reliability: r })} aria-pressed={active}
                  title={r ? RELIABILITY_DESCRIPTION[r] : undefined}
                  className={`flex h-full items-center gap-1.5 rounded-md px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60 ${
                    active ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200'
                  }`}>
                  {r && <span className={`h-1.5 w-1.5 rounded-full ${RELIABILITY_DOT[r]}`} aria-hidden />}
                  {r ? RELIABILITY_LABEL[r] : 'All'}
                  {!isLoading && <span className={`tabular-nums ${active ? 'text-zinc-300' : 'text-zinc-500'}`}>{n}</span>}
                </button>
              )
            })}
          </div>

          <Select value={publication ?? ALL} onValueChange={(v) => patch({ publication: v === ALL ? undefined : v })}>
            <SelectTrigger aria-label="Publication" className={`h-9 w-auto min-w-36 max-w-60 text-xs ${publication ? 'border-violet-700/60 bg-violet-950/20 text-zinc-100' : ''}`}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="max-h-80">
              <SelectItem value={ALL}>All publications</SelectItem>
              {((facets.pubCounts.get(NO_PUBLICATION) ?? 0) > 0 || publication === NO_PUBLICATION) && (
                <SelectItem value={NO_PUBLICATION}>No publication <span className="ml-1 tabular-nums text-zinc-500">{facets.pubCounts.get(NO_PUBLICATION) ?? 0}</span></SelectItem>
              )}
              {publication && publication !== NO_PUBLICATION && !facets.pubCounts.has(publication) && (
                <SelectItem value={publication}>{publication} <span className="ml-1 tabular-nums text-zinc-500">0</span></SelectItem>
              )}
              {publicationOptions.map(([pub, n]) => (
                <SelectItem key={pub} value={pub}>{pub} <span className="ml-1 tabular-nums text-zinc-500">{n}</span></SelectItem>
              ))}
            </SelectContent>
          </Select>

          {(facets.uncitedCount > 0 || uncited) && (
            <button onClick={() => patch({ uncited: uncited ? undefined : true })} aria-pressed={!!uncited}
              title="Sources nothing cites yet"
              className={`inline-flex h-9 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium transition-colors ${
                uncited ? 'border-violet-700/60 bg-violet-950/30 text-violet-200' : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-200'
              }`}>
              Uncited <span className="tabular-nums opacity-70">{facets.uncitedCount}</span>
            </button>
          )}

          {hasFilters && (
            <button onClick={clearFilters} className="inline-flex h-9 items-center gap-1 rounded-md px-2 text-xs text-zinc-400 transition-colors hover:text-white">
              <X className="h-3 w-3" /> Clear
            </button>
          )}

          <div className="ml-auto flex items-center gap-2">
            {/* Phone rows have no headers to click. */}
            <div className="sm:hidden">
              <Select value={`${sort}:${order}`} onValueChange={(v) => {
                const [s, o] = v.split(':') as [SourceSortKey, 'asc' | 'desc']
                patch({ sort: s === 'added' ? undefined : s, order: o })
              }}>
                <SelectTrigger className="h-9 w-auto min-w-32 text-xs" aria-label="Sort"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="added:desc">Recently added</SelectItem>
                  <SelectItem value="published:desc">Newest published</SelectItem>
                  <SelectItem value="published:asc">Oldest published</SelectItem>
                  <SelectItem value="cited:desc">Most cited</SelectItem>
                  <SelectItem value="title:asc">Title A→Z</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm" className="h-9" onClick={() => {
              const date = new Date().toISOString().slice(0, 10)
              downloadCsv(`/sources/?universe_id=${universe.id}&format=csv`, `sources-${universe.slug}-${date}.csv`)
            }}>
              <Download className="mr-1.5 h-3.5 w-3.5" />Export all
            </Button>
          </div>
        </div>
      </div>

      {/* Phone rows */}
      <div className="space-y-2 sm:hidden">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-[64px] w-full rounded-lg" />)
          : items.length === 0 ? emptyState
          : items.slice(0, limit).map((s) => (
              <Link key={s.id} to="/sources/$id" params={{ id: s.id }}
                className="group block rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2.5 transition-colors active:bg-zinc-800/60">
                <span className="flex items-start gap-3 text-sm">
                  <span className="min-w-0 flex-1"><SourceTitle s={s} /></span>
                  <ReliabilityBadge reliability={s.reliability} />
                </span>
                <span className="mt-1.5 flex items-center justify-between gap-3">
                  <span className="text-xs text-zinc-400">{s.published_at ? <FuzzyDate value={s.published_at} /> : 'Undated'}</span>
                  <Citations s={s} />
                </span>
              </Link>
            ))}
        {!isLoading && items.length > limit && (
          <Button variant="outline" className="w-full" onClick={() => setLimit((n) => n + STEP)}>
            Show {Math.min(STEP, items.length - limit)} more ({items.length - limit} left)
          </Button>
        )}
      </div>

      {/* Table, always virtualised: the whole universe is in it. */}
      <div ref={tableScrollRef} className="hidden overflow-y-auto rounded-lg border border-zinc-800 sm:block" style={{ maxHeight: 'calc(100dvh - 14rem)' }}>
        <table className="w-full table-fixed text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-zinc-800 bg-zinc-900/95 backdrop-blur">
              <th className="w-10 px-3 py-2.5" scope="col">
                <input type="checkbox" aria-label="Select all shown sources" checked={allSelected}
                  onChange={() => setSelected(allSelected ? new Set() : new Set(items.map((s) => s.id)))}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600" />
              </th>
              {sortHeader('title', 'Source')}
              {sortHeader('published', 'Published', 'hidden w-32 md:table-cell')}
              {sortHeader('cited', 'Cited by', 'w-32')}
              {sortHeader('reliability', 'Reliability', 'w-32')}
              <th className="w-20" scope="col"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {isLoading && Array.from({ length: 10 }).map((_, i) => <RowSkeleton key={i} />)}
            {!isLoading && items.length === 0 && <tr><td colSpan={6}>{emptyState}</td></tr>}
            {padTop > 0 && <tr aria-hidden><td colSpan={6} style={{ height: padTop }} /></tr>}
            {!isLoading && virtualRows.map((vr) => {
              const s = items[vr.index]
              const isSelected = selected.has(s.id)
              return (
                <tr key={s.id} data-index={vr.index} ref={rowVirtualizer.measureElement}
                  className={`group transition-colors hover:bg-zinc-900/50 ${isSelected ? 'bg-violet-950/20' : ''}`}>
                  <td className="px-3 py-2">
                    <input type="checkbox" aria-label={`Select ${s.title}`} checked={isSelected} onChange={() => toggleSelect(s.id)}
                      className="rounded border-zinc-700 bg-zinc-900 accent-violet-600" />
                  </td>
                  <td className="p-0">
                    <Link to="/sources/$id" params={{ id: s.id }} className="flex min-h-[52px] items-center px-3 py-2">
                      <SourceTitle s={s} />
                    </Link>
                  </td>
                  <td className="hidden px-3 py-2 text-xs text-zinc-400 md:table-cell">
                    {s.published_at ? <FuzzyDate value={s.published_at} /> : <span className="text-zinc-600">-</span>}
                  </td>
                  <td className="px-3 py-2"><Citations s={s} /></td>
                  <td className="px-3 py-2" title={RELIABILITY_DESCRIPTION[s.reliability]}><ReliabilityBadge reliability={s.reliability} /></td>
                  <td className="pr-2">
                    <span className="flex items-center justify-end gap-0.5">
                      <a href={s.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${s.title} in a new tab`}
                        className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                      <RowActions s={s} onEdit={() => setEditingId(s.id)} onDelete={() => setDeleting(s)} />
                    </span>
                  </td>
                </tr>
              )
            })}
            {padBottom > 0 && <tr aria-hidden><td colSpan={6} style={{ height: padBottom }} /></tr>}
          </tbody>
        </table>
      </div>

      <SourceFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingId && <EditSourceSheet key={editingId} id={editingId} universeId={universe.id} onClose={() => setEditingId(null)} />}

      <BulkActionBar count={selectedShown.length} label="source" onClear={() => setSelected(new Set())}>
        <Button size="sm" variant="destructive" className="h-7 text-xs" onClick={() => setConfirmingBulkDelete(true)} disabled={bulkDeleting}>
          <Trash2 className="mr-1 h-3 w-3" />Delete
        </Button>
      </BulkActionBar>

      <ConfirmDialog
        open={confirmingBulkDelete}
        title={`Delete ${plural(selectedShown.length, 'source')}?`}
        description="This cannot be undone. Every citation of these sources is removed with them."
        impact={impact(selectedShown)}
        confirmLabel="Delete"
        destructive
        pending={bulkDeleting}
        onConfirm={bulkDelete}
        onCancel={() => setConfirmingBulkDelete(false)}
      />
      <ConfirmDialog
        open={!!deleting}
        title={`Delete "${deleting?.title ?? ''}"?`}
        description="This cannot be undone. Every citation of this source is removed with it."
        impact={deleting ? impact([deleting]) : undefined}
        confirmLabel="Delete"
        destructive
        pending={deleteSource.isPending}
        onConfirm={() => deleting && deleteOne(deleting)}
        onCancel={() => setDeleting(null)}
      />
    </div>
  )
}
