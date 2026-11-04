import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import {
  Download, ExternalLink, FileText, GitMerge, MoreVertical, Pencil, Plus, Search, Trash2, X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { ReliabilityDot } from '@/components/sources/ReliabilityDot'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useCurrentUser } from '@/hooks/useCurrentUser'
import { useDebounce } from '@/hooks/useDebounce'
import { downloadCsv } from '@/lib/download'
import {
  sourcesCsvUrl, useBulkUpdateSources, useDeleteSource, useMergeSource, useSource, useSources,
  type SourceListParams,
} from '@/lib/queries'
import { KIND_META, KIND_ORDER, isValidUrl } from '@/lib/sourceMeta'
import { RELIABILITY_DOT, RELIABILITY_LABEL, RELIABILITY_ORDER } from '@/lib/statusColors'
import type { SourceCounts, SourceKind, SourceListItem, SourceReliability, UUID } from '@/lib/types'
import { cn } from '@/lib/utils'
import { useUniverseStore } from '@/stores/universe'
import { SourceFormSheet, type SourceSortKey } from './_app.$universe.sources.index'

export const Route = createLazyFileRoute('/_app/$universe/sources/')({ component: SourcesPage })

const PAGE = 50
const plural = (n: number, w: string) => `${n.toLocaleString()} ${w}${n === 1 ? '' : 's'}`

const COUNT_LABELS: [keyof SourceCounts, string][] = [
  ['member', 'member'], ['incident', 'incident'], ['set', 'set'], ['alliance', 'alliance'],
  ['court_case', 'court case'], ['municipality', 'place'], ['business', 'business'],
  ['custody_id', 'custody number'], ['alias', 'alias'], ['media', 'photo'],
]

function countsText(c: SourceCounts): string {
  const parts = COUNT_LABELS.filter(([k]) => (c[k] as number) > 0).map(([k, w]) => plural(c[k] as number, w))
  return parts.length ? parts.join(', ') : 'Nothing cites it.'
}

function CitedCell({ counts }: { counts: SourceCounts }) {
  if (counts.total === 0) return <span className="text-xs text-zinc-500">uncited</span>
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="cursor-default tabular-nums text-sm text-zinc-300">{counts.total.toLocaleString()}</span>
      </TooltipTrigger>
      <TooltipContent>{countsText(counts)}</TooltipContent>
    </Tooltip>
  )
}

function SourceTitleCell({ s }: { s: SourceListItem }) {
  const Icon = (KIND_META[s.kind] ?? KIND_META.OTHER).icon
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <Icon className="h-3.5 w-3.5 shrink-0 text-zinc-500" aria-label={KIND_META[s.kind]?.label} />
      <div className="min-w-0">
        <Link
          from="/$universe" to="/$universe/sources/$id" params={{ id: s.id }}
          className="block truncate text-sm text-zinc-100 hover:text-violet-400" title={s.title}
        >
          {s.title}
        </Link>
        <div className="truncate text-xs text-zinc-500">{[s.publication, s.domain].filter(Boolean).join(' · ')}</div>
      </div>
    </div>
  )
}

function EditSourceSheet({ id, universeId, onClose }: { id: UUID; universeId: UUID; onClose: () => void }) {
  const { data } = useSource(id, universeId)
  if (!data) return null
  return <SourceFormSheet universeId={universeId} open onClose={onClose} initial={data} />
}

function MergeDialog({ universeId, sources, onClose }: { universeId: UUID; sources: SourceListItem[]; onClose: () => void }) {
  const merge = useMergeSource(universeId)
  const [keep, setKeep] = useState<UUID>(
    () => [...sources].sort((a, b) => b.counts.total - a.counts.total)[0]?.id ?? '',
  )
  const [busy, setBusy] = useState(false)

  async function run() {
    setBusy(true)
    let moved = 0
    let combined = 0
    try {
      for (const s of sources) {
        if (s.id === keep) continue
        const r = await merge.mutateAsync({ id: s.id, intoId: keep })
        moved += r.moved
        combined += r.combined
      }
      toast.success(`Merged ${plural(sources.length - 1, 'source')}: ${moved} links moved, ${combined} combined`)
      onClose()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open onOpenChange={(v) => !v && !busy && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><GitMerge className="h-4 w-4 text-violet-400" /> Merge sources</DialogTitle>
          <DialogDescription>
            Keep one; the others are folded into it. Everything that cites them moves across, and a
            record citing two of them keeps one citation with both locators.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5">
          {sources.map((s) => (
            <label key={s.id} className={cn(
              'flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2',
              keep === s.id ? 'border-violet-600 bg-violet-950/30' : 'border-zinc-800 hover:border-zinc-700',
            )}>
              <input type="radio" name="keep" checked={keep === s.id} onChange={() => setKeep(s.id)} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm text-zinc-200">{s.title}</span>
                <span className="block truncate text-xs text-zinc-500">{s.domain} · {countsText(s.counts)}</span>
              </span>
              {keep === s.id && <span className="text-xs text-violet-300">keep</span>}
            </label>
          ))}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose} disabled={busy}>Cancel</Button>
          <Button onClick={run} disabled={busy || !keep}>{busy ? 'Merging…' : `Merge into the kept one`}</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function SourcesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const { data: user } = useCurrentUser()
  const isAdmin = user?.global_role === 'ADMIN'
  const search = Route.useSearch()
  const navigate = useNavigate({ from: '/$universe/sources/' })

  const [q, setQ] = useState(search.q ?? '')
  const debouncedQ = useDebounce(q.trim(), 250)
  useEffect(() => {
    if (debouncedQ === (search.q ?? '')) return
    navigate({ search: (prev) => ({ ...prev, q: debouncedQ || undefined, page: undefined }), replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ])

  const sort: SourceSortKey = search.sort ?? 'added'
  const order = search.order ?? 'desc'
  const page = search.page ?? 1
  const params: SourceListParams = {
    q: search.q, kind: search.kind, reliability: search.reliability, publication: search.publication,
    uncited: search.uncited, sort, order, offset: (page - 1) * PAGE, limit: PAGE,
  }
  const { data, isLoading, isFetching } = useSources(universeId, params)
  const items = data?.items ?? []
  const total = data?.total ?? 0
  const facets = data?.facets

  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<UUID | null>(null)
  const [selected, setSelected] = useState<Map<UUID, SourceListItem>>(new Map())
  const [deleting, setDeleting] = useState<SourceListItem[] | null>(null)
  const [merging, setMerging] = useState(false)
  const del = useDeleteSource(universeId ?? '')
  const bulk = useBulkUpdateSources(universeId ?? '')

  const hasFilters = !!(search.q || search.kind || search.reliability || search.publication || search.uncited)
  const set = (patch: Partial<typeof search>) =>
    navigate({ search: (prev) => ({ ...prev, ...patch, page: undefined }), replace: true })

  function toggleSort(key: SourceSortKey) {
    const next = sort === key ? (order === 'asc' ? 'desc' : 'asc') : key === 'title' ? 'asc' : 'desc'
    navigate({ search: (prev) => ({ ...prev, sort: key, order: next, page: undefined }), replace: true })
  }

  function toggle(s: SourceListItem) {
    setSelected((prev) => {
      const next = new Map(prev)
      if (next.has(s.id)) next.delete(s.id)
      else next.set(s.id, s)
      return next
    })
  }
  const pageAllSelected = items.length > 0 && items.every((s) => selected.has(s.id))
  const selectedList = useMemo(() => [...selected.values()], [selected])

  async function bulkSet(body: { reliability?: SourceReliability; kind?: SourceKind }) {
    const r = await bulk.mutateAsync({ ids: selectedList.map((s) => s.id), ...body })
    toast.success(`Updated ${plural(r.updated, 'source')}`)
    setSelected(new Map())
  }

  async function confirmDelete() {
    if (!deleting) return
    const results = await Promise.allSettled(deleting.map((s) => del.mutateAsync({ id: s.id, force: true })))
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed) toast.error(`${failed} could not be deleted`)
    else toast.success(`Deleted ${plural(deleting.length, 'source')}`)
    setDeleting(null)
    setSelected(new Map())
  }

  if (!universe) return <NoUniverse />

  function sortHeader(key: SourceSortKey, label: string, className = '') {
    const sorted = sort === key
    return (
      <th scope="col" className={`px-3 py-2.5 text-left ${className}`} aria-sort={sorted ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}>
        <button onClick={() => toggleSort(key)}
          className={`inline-flex items-center gap-1 text-xs font-medium transition-colors hover:text-white ${sorted ? 'text-zinc-200' : 'text-zinc-400'}`}>
          {label} <span className="text-zinc-500" aria-hidden>{sorted ? (order === 'asc' ? '↑' : '↓') : '↕'}</span>
        </button>
      </th>
    )
  }

  const rowMenu = (s: SourceListItem) => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button type="button" aria-label={`Actions for ${s.title}`} className="rounded p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200">
          <MoreVertical className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link from="/$universe" to="/$universe/sources/$id" params={{ id: s.id }}><FileText className="mr-2 h-3.5 w-3.5" />Open</Link>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setEditingId(s.id)}><Pencil className="mr-2 h-3.5 w-3.5" />Edit</DropdownMenuItem>
        {isAdmin && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-400 focus:text-red-300" onClick={() => setDeleting([s])}>
              <Trash2 className="mr-2 h-3.5 w-3.5" />Delete
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )

  const from = total === 0 ? 0 : (page - 1) * PAGE + 1
  const to = Math.min(page * PAGE, total)
  const lastPage = Math.max(1, Math.ceil(total / PAGE))
  const kindTotal = facets ? Object.values(facets.kind).reduce((a, b) => a + (b ?? 0), 0) : 0

  return (
    <div className={selected.size > 0 ? 'pb-28' : 'pb-8'}>
      <PageHeader
        title="Sources"
        description={isLoading ? 'Loading…' : hasFilters ? `${plural(total, 'source')} match` : plural(total, 'source')}
        action={
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => {
              const date = new Date().toISOString().slice(0, 10)
              downloadCsv(sourcesCsvUrl(universe.id, params), `sources-${universe.slug}-${date}.csv`)
            }}>
              <Download className="mr-1.5 h-4 w-4" />CSV
            </Button>
            <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add source</Button>
          </div>
        }
      />

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            className="h-9 pl-8 pr-8 text-sm"
            placeholder="Search title, site, publication, notes…"
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
        <div className="flex h-9 items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="group" aria-label="Reliability">
          {RELIABILITY_ORDER.map((r) => {
            const n = facets?.reliability[r] ?? 0
            const on = search.reliability === r
            return (
              <button key={r} type="button" aria-pressed={on}
                onClick={() => set({ reliability: on ? undefined : r })}
                className={cn('inline-flex h-7 items-center gap-1.5 rounded-md px-2 text-xs transition-colors',
                  on ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200')}>
                <span className={cn('h-1.5 w-1.5 rounded-full', RELIABILITY_DOT[r])} />
                {RELIABILITY_LABEL[r]} <span className="tabular-nums text-zinc-500">{n}</span>
              </button>
            )
          })}
        </div>
        <button type="button" aria-pressed={!!search.uncited}
          onClick={() => set({ uncited: search.uncited ? undefined : true })}
          className={cn('h-9 rounded-lg border px-3 text-xs transition-colors',
            search.uncited ? 'border-violet-700 bg-violet-950/40 text-violet-200' : 'border-zinc-800 text-zinc-400 hover:text-zinc-200')}>
          Uncited
        </button>
        {hasFilters && (
          <Button size="sm" variant="ghost" onClick={() => { setQ(''); navigate({ search: { sort: search.sort, order: search.order }, replace: true }) }}>
            Clear
          </Button>
        )}
      </div>

      {/* Kind chips, with how many of each the other filters leave. */}
      <div className="mb-4 flex gap-1.5 overflow-x-auto pb-1 [scrollbar-width:none]">
        <button type="button" aria-pressed={!search.kind} onClick={() => set({ kind: undefined })}
          className={cn('shrink-0 rounded-full border px-3 py-1 text-xs', !search.kind ? 'border-zinc-600 bg-zinc-800 text-white' : 'border-zinc-800 text-zinc-400 hover:text-zinc-200')}>
          All <span className="tabular-nums text-zinc-500">{kindTotal}</span>
        </button>
        {KIND_ORDER.filter((k) => (facets?.kind[k] ?? 0) > 0 || search.kind === k).map((k) => {
          const Icon = KIND_META[k].icon
          const on = search.kind === k
          return (
            <button key={k} type="button" aria-pressed={on} onClick={() => set({ kind: on ? undefined : k })}
              className={cn('inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1 text-xs',
                on ? 'border-zinc-600 bg-zinc-800 text-white' : 'border-zinc-800 text-zinc-400 hover:text-zinc-200')}>
              <Icon className="h-3 w-3" />{KIND_META[k].plural}
              <span className="tabular-nums text-zinc-500">{facets?.kind[k] ?? 0}</span>
            </button>
          )
        })}
      </div>

      {/* Sort, on a phone, where the table headers are not shown. */}
      <div className="mb-3 md:hidden">
        <Select value={`${sort}:${order}`} onValueChange={(v) => {
          const [k, o] = v.split(':') as [SourceSortKey, 'asc' | 'desc']
          navigate({ search: (prev) => ({ ...prev, sort: k, order: o, page: undefined }), replace: true })
        }}>
          <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="added:desc">Newest first</SelectItem>
            <SelectItem value="title:asc">Title A–Z</SelectItem>
            <SelectItem value="published:desc">Published, latest</SelectItem>
            <SelectItem value="cited:desc">Most cited</SelectItem>
            <SelectItem value="reliability:desc">Most reliable</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {!isLoading && items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={hasFilters ? 'No sources match these filters' : 'No sources yet'}
          action={hasFilters ? undefined : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add the first source</Button>}
        />
      ) : (
        <>
          <div className={cn('hidden overflow-hidden rounded-lg border border-zinc-800 md:block', isFetching && 'opacity-80')}>
            <table className="w-full table-fixed">
              <thead className="border-b border-zinc-800 bg-zinc-900/60">
                <tr>
                  <th className="w-10 px-3">
                    <input type="checkbox" aria-label="Select this page" checked={pageAllSelected}
                      onChange={() => setSelected((prev) => {
                        const next = new Map(prev)
                        if (pageAllSelected) items.forEach((s) => next.delete(s.id))
                        else items.forEach((s) => next.set(s.id, s))
                        return next
                      })} />
                  </th>
                  {sortHeader('title', 'Source')}
                  {sortHeader('published', 'Published', 'w-32')}
                  {sortHeader('cited', 'Cited', 'w-20')}
                  {sortHeader('reliability', 'Reliability', 'w-32')}
                  <th className="w-20" />
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/70">
                {isLoading
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i} className="h-[53px]">
                        <td /><td className="px-3"><Skeleton className="h-4 w-3/4" /></td>
                        <td className="px-3"><Skeleton className="h-4 w-16" /></td>
                        <td className="px-3"><Skeleton className="h-4 w-8" /></td>
                        <td className="px-3"><Skeleton className="h-4 w-16" /></td><td />
                      </tr>
                    ))
                  : items.map((s) => (
                      <tr key={s.id} className={cn('h-[53px] hover:bg-zinc-900/40', selected.has(s.id) && 'bg-violet-950/20')}>
                        <td className="px-3"><input type="checkbox" aria-label={`Select ${s.title}`} checked={selected.has(s.id)} onChange={() => toggle(s)} /></td>
                        <td className="min-w-0 px-3"><SourceTitleCell s={s} /></td>
                        <td className="px-3 text-sm text-zinc-400"><FuzzyDate value={s.published_at} fallback="" /></td>
                        <td className="px-3"><CitedCell counts={s.counts} /></td>
                        <td className="px-3">
                          <span className="inline-flex items-center gap-1.5 text-xs text-zinc-300">
                            <ReliabilityDot reliability={s.reliability} />{RELIABILITY_LABEL[s.reliability]}
                          </span>
                        </td>
                        <td className="px-2 text-right">
                          {isValidUrl(s.url) && (
                            <a href={s.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${s.title} in a new tab`}
                              className="inline-flex rounded p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          )}
                          {rowMenu(s)}
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>

          <ul className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 md:hidden">
            {items.map((s) => (
              <li key={s.id} className="flex items-start gap-3 px-3 py-3">
                <input type="checkbox" className="mt-1" aria-label={`Select ${s.title}`} checked={selected.has(s.id)} onChange={() => toggle(s)} />
                <div className="min-w-0 flex-1">
                  <SourceTitleCell s={s} />
                  <div className="mt-1 flex items-center gap-3 text-xs text-zinc-500">
                    <span className="inline-flex items-center gap-1"><ReliabilityDot reliability={s.reliability} />{RELIABILITY_LABEL[s.reliability]}</span>
                    <FuzzyDate value={s.published_at} fallback="" />
                    <span>{s.counts.total ? `${s.counts.total} cites` : 'uncited'}</span>
                  </div>
                </div>
                {rowMenu(s)}
              </li>
            ))}
          </ul>

          {total > PAGE && (
            <nav className="mt-3 flex items-center justify-between text-xs text-zinc-400" aria-label="Pages">
              <span className="tabular-nums">{from.toLocaleString()}–{to.toLocaleString()} of {total.toLocaleString()}</span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" aria-disabled={page <= 1} disabled={page <= 1}
                  onClick={() => navigate({ search: (prev) => ({ ...prev, page: page - 1 > 1 ? page - 1 : undefined }) })}>
                  Previous
                </Button>
                <Button size="sm" variant="outline" aria-disabled={page >= lastPage} disabled={page >= lastPage}
                  onClick={() => navigate({ search: (prev) => ({ ...prev, page: page + 1 }) })}>
                  Next
                </Button>
              </div>
            </nav>
          )}
        </>
      )}

      <BulkActionBar count={selected.size} label="source" onClear={() => setSelected(new Map())}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild><Button size="sm" variant="outline">Reliability</Button></DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuLabel>Set reliability</DropdownMenuLabel>
            {RELIABILITY_ORDER.map((r) => (
              <DropdownMenuItem key={r} onClick={() => bulkSet({ reliability: r })}>
                <span className={cn('mr-2 h-2 w-2 rounded-full', RELIABILITY_DOT[r])} />{RELIABILITY_LABEL[r]}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <DropdownMenu>
          <DropdownMenuTrigger asChild><Button size="sm" variant="outline">Kind</Button></DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuLabel>Set kind</DropdownMenuLabel>
            {KIND_ORDER.map((k) => {
              const Icon = KIND_META[k].icon
              return <DropdownMenuItem key={k} onClick={() => bulkSet({ kind: k })}><Icon className="mr-2 h-3.5 w-3.5" />{KIND_META[k].label}</DropdownMenuItem>
            })}
          </DropdownMenuContent>
        </DropdownMenu>
        {isAdmin && selected.size >= 2 && (
          <Button size="sm" variant="outline" onClick={() => setMerging(true)}><GitMerge className="mr-1.5 h-3.5 w-3.5" />Merge</Button>
        )}
        {isAdmin && (
          <Button size="sm" variant="destructive" onClick={() => setDeleting(selectedList)}><Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete</Button>
        )}
      </BulkActionBar>

      {creating && <SourceFormSheet universeId={universe.id} open onClose={() => setCreating(false)} />}
      {editingId && <EditSourceSheet id={editingId} universeId={universe.id} onClose={() => setEditingId(null)} />}
      {merging && <MergeDialog universeId={universe.id} sources={selectedList} onClose={() => { setMerging(false); setSelected(new Map()) }} />}
      <ConfirmDialog
        open={!!deleting}
        title={deleting?.length === 1 ? `Delete "${deleting[0].title}"?` : `Delete ${plural(deleting?.length ?? 0, 'source')}?`}
        description="Every citation of it is removed from the records that cite it. This cannot be undone."
        impact={deleting && countsText(deleting.reduce((acc, s) => {
          const out = { ...acc }
          for (const [k] of COUNT_LABELS) (out[k] as number) += s.counts[k] as number
          out.total += s.counts.total
          return out
        }, { member: 0, incident: 0, set: 0, alliance: 0, court_case: 0, municipality: 0, business: 0, custody_id: 0, alias: 0, media: 0, total: 0 } as SourceCounts))}
        confirmLabel="Delete"
        destructive
        pending={del.isPending}
        onConfirm={confirmDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  )
}
