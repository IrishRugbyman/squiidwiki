import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import {
  Archive, ChevronDown, ExternalLink, Link2, MoreHorizontal, Pencil, Trash2, Unlink,
} from 'lucide-react'
import { lazy, Suspense, useMemo, useState } from 'react'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { CopyButton } from '@/components/CopyButton'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { LinkifiedText } from '@/components/LinkifiedText'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { CitationEditDialog } from '@/components/sources/CitationEditDialog'
import { EntityCitePicker } from '@/components/sources/EntityCitePicker'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Skeleton } from '@/components/ui/skeleton'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useCurrentUser } from '@/hooks/useCurrentUser'
import { useEditShortcut } from '@/hooks/useKeymap'
import {
  useDeleteCitation, useDeleteSource, useSource, useSourceCitations, useSourceCustodyIds,
} from '@/lib/queries'
import { KIND_META, LOOKUP_LABEL, isValidUrl, lookupDeepLink } from '@/lib/sourceMeta'
import type {
  CitableType, CitationRead, EntityRef, SourceCitationRow, SourceCounts, SourceReadDetail, UUID,
} from '@/lib/types'
import { cn, timeAgo } from '@/lib/utils'
import { useRecordRecent } from '@/stores/recents'
import { useUniverseStore } from '@/stores/universe'
import { SourceFormSheet } from './_app.$universe.sources.index'

const PhotoGallery = lazy(() =>
  import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })),
)

export const Route = createLazyFileRoute('/_app/$universe/sources/$id')({ component: SourceDetailPage })

type Tab = CitableType | 'custody' | 'photos'
const TABS: { key: Tab; label: string; count: (c: SourceCounts) => number }[] = [
  { key: 'member', label: 'Members', count: (c) => c.member },
  { key: 'incident', label: 'Incidents', count: (c) => c.incident },
  { key: 'set', label: 'Sets', count: (c) => c.set },
  { key: 'alliance', label: 'Alliances', count: (c) => c.alliance },
  { key: 'court_case', label: 'Cases', count: (c) => c.court_case },
  { key: 'municipality', label: 'Places', count: (c) => c.municipality },
  { key: 'business', label: 'Businesses', count: (c) => c.business },
  { key: 'custody', label: 'Custody numbers', count: (c) => c.custody_id },
  { key: 'photos', label: 'Photos', count: (c) => c.media },
]
const PAGE = 50

/** A link to any record, by its type's route. Businesses have no page. */
function EntityLink({ e }: { e: EntityRef }) {
  const cls = 'min-w-0 truncate text-sm text-zinc-100 hover:text-violet-400'
  const params = { id: e.slug ?? e.id }
  switch (e.type) {
    case 'member': return <Link from="/$universe" to="/$universe/members/$id" params={params} className={cls}>{e.label}</Link>
    case 'incident': return <Link from="/$universe" to="/$universe/incidents/$id" params={{ id: e.id }} className={cls}>{e.label}</Link>
    case 'set': return <Link from="/$universe" to="/$universe/sets/$id" params={params} className={cls}>{e.label}</Link>
    case 'alliance': return <Link from="/$universe" to="/$universe/alliances/$id" params={params} className={cls}>{e.label}</Link>
    case 'court_case': return <Link from="/$universe" to="/$universe/cases/$id" params={params} className={cls}>{e.label}</Link>
    case 'municipality': return <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: e.id }} className={cls}>{e.label}</Link>
    default: return <span className={cls}>{e.label}</span>
  }
}

function asCitation(row: SourceCitationRow, source: SourceReadDetail): CitationRead {
  return { ...row, source: { ...source } }
}

function CitationRows({ source, universeId, type }: { source: SourceReadDetail; universeId: UUID; type: CitableType }) {
  const [page, setPage] = useState(0)
  const { data, isLoading } = useSourceCitations(source.id, universeId, type, page * PAGE, PAGE)
  const [open, setOpen] = useState<UUID | null>(null)
  const [editing, setEditing] = useState<SourceCitationRow | null>(null)
  const [detaching, setDetaching] = useState<SourceCitationRow | null>(null)
  const detach = useDeleteCitation(universeId, type)
  const total = data?.total ?? 0
  const rows = data?.items ?? []

  if (isLoading) return <div className="space-y-2">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-11 w-full" />)}</div>

  return (
    <div>
      <ul className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800">
        {rows.map((r) => {
          const hasDetail = !!(r.quote || r.note)
          const deep = lookupDeepLink(source.lookup_system, r.locator)
          return (
            <li key={r.id} className="group px-3 py-2.5 hover:bg-zinc-900/40">
              <div className="flex items-center gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex min-w-0 items-center gap-2"><EntityLink e={r.entity} /></div>
                  <div className="mt-0.5 flex flex-wrap items-center gap-x-1.5 text-xs text-zinc-500">
                    {r.entity.detail && <span>{r.entity.detail.replace(/_/g, ' ').toLowerCase()}</span>}
                    {r.entity.date?.year && <><span aria-hidden>·</span><FuzzyDate value={r.entity.date} /></>}
                    {r.locator && (
                      <>
                        <span aria-hidden>·</span>
                        <span className="font-mono text-zinc-300">
                          {source.lookup_system ? `${LOOKUP_LABEL[source.lookup_system]} ${r.locator}` : r.locator}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                {deep && (
                  <a href={deep} target="_blank" rel="noopener noreferrer" aria-label="Open this record"
                    className="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200"><ExternalLink className="h-3.5 w-3.5" /></a>
                )}
                {hasDetail && (
                  <button type="button" aria-expanded={open === r.id} aria-label="What it supports"
                    onClick={() => setOpen(open === r.id ? null : r.id)}
                    className="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200">
                    <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', open === r.id && 'rotate-180')} />
                  </button>
                )}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button type="button" aria-label="Citation actions" className="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200">
                      <MoreHorizontal className="h-3.5 w-3.5" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => setEditing(r)}><Pencil className="mr-2 h-3.5 w-3.5" />Edit what it supports</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-red-400 focus:text-red-300" onClick={() => setDetaching(r)}>
                      <Unlink className="mr-2 h-3.5 w-3.5" />Detach
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              {open === r.id && (
                <div className="mt-2 space-y-1.5 border-l-2 border-zinc-800 pl-3 text-sm">
                  {r.quote && <blockquote className="whitespace-pre-wrap italic text-zinc-300">“{r.quote}”</blockquote>}
                  {r.note && <p className="whitespace-pre-wrap text-zinc-400"><LinkifiedText text={r.note} /></p>}
                </div>
              )}
            </li>
          )
        })}
      </ul>
      {total > PAGE && (
        <nav className="mt-3 flex items-center justify-between text-xs text-zinc-400" aria-label="Pages">
          <span className="tabular-nums">{page * PAGE + 1}–{Math.min((page + 1) * PAGE, total)} of {total.toLocaleString()}</span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={page === 0} aria-disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</Button>
            <Button size="sm" variant="outline" disabled={(page + 1) * PAGE >= total} aria-disabled={(page + 1) * PAGE >= total}
              onClick={() => setPage(page + 1)}>Next</Button>
          </div>
        </nav>
      )}
      {editing && (
        <CitationEditDialog universeId={universeId} entityType={type} citation={asCitation(editing, source)} onClose={() => setEditing(null)} />
      )}
      <ConfirmDialog
        open={!!detaching}
        title="Detach this citation?"
        description={detaching ? `${detaching.entity.label} will no longer cite this source.` : ''}
        confirmLabel="Detach"
        destructive
        pending={detach.isPending}
        onConfirm={async () => { if (detaching) await detach.mutateAsync(detaching.id); setDetaching(null) }}
        onCancel={() => setDetaching(null)}
      />
    </div>
  )
}

function CustodyRows({ sourceId, universeId }: { sourceId: UUID; universeId: UUID }) {
  const { data, isLoading } = useSourceCustodyIds(sourceId, universeId)
  if (isLoading) return <Skeleton className="h-24 w-full" />
  return (
    <ul className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800">
      {(data ?? []).map((c) => (
        <li key={c.id} className="flex items-center gap-3 px-3 py-2.5 text-sm">
          <span className="w-16 shrink-0 text-xs text-zinc-500">{c.system}</span>
          <span className="w-32 shrink-0 font-mono text-zinc-300">{c.number}</span>
          <Link from="/$universe" to="/$universe/members/$id" params={{ id: c.member_slug ?? c.member_id }}
            className="min-w-0 flex-1 truncate text-zinc-100 hover:text-violet-400">{c.member_label}</Link>
          {c.retrieved_at && <span className="shrink-0 text-xs text-zinc-500">read {c.retrieved_at}</span>}
        </li>
      ))}
    </ul>
  )
}

function SourceDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data: user } = useCurrentUser()
  const navigate = useNavigate()
  const { data: source, isLoading, isError, refetch } = useSource(id, universe?.id ?? null)
  const deleteSource = useDeleteSource(universe?.id ?? '')
  const [editing, setEditing] = useState(false)
  const [citing, setCiting] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [tab, setTab] = useState<Tab | null>(null)

  useRecordRecent(source ? { type: 'source', id: source.id, slug: null, label: source.title } : null)
  useEditShortcut(() => source && setEditing(true))

  const tabs = useMemo(() => (source ? TABS.filter((t) => t.count(source.counts) > 0) : []), [source])
  // The chosen tab while it still has rows, else the first that does.
  const active: Tab | null = tab && tabs.some((t) => t.key === tab) ? tab : (tabs[0]?.key ?? null)

  if (isError) return <ErrorState title="Source not found" onRetry={() => refetch()} />
  if (isLoading || !source || !universe) return <DetailHeaderSkeleton />

  const kind = KIND_META[source.kind] ?? KIND_META.OTHER
  const KindIcon = kind.icon
  const impact = TABS.filter((t) => t.count(source.counts) > 0)
    .map((t) => `${t.count(source.counts)} ${t.label.toLowerCase()}`).join(', ')

  return (
    <TooltipProvider delayDuration={200}>
      <div className="pb-10">
        <Breadcrumbs items={[{ label: 'Sources', to: '/$universe/sources' }, { label: source.title }]} />

        <header className="mb-6 space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-400">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-800 px-2 py-0.5">
              <KindIcon className="h-3 w-3" />{kind.label}
            </span>
            <ReliabilityBadge reliability={source.reliability} />
            {source.lookup_system && <span className="rounded-full border border-sky-900/60 px-2 py-0.5 text-sky-300">one source per universe</span>}
          </div>
          <div className="flex items-start gap-2">
            <h1 className="min-w-0 text-xl font-bold text-white">{source.title}</h1>
            <CopyButton value={window.location.href} />
          </div>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-zinc-400">
            {source.publication && <span>{source.publication}</span>}
            {source.domain && <><span aria-hidden>·</span><span className="text-zinc-500">{source.domain}</span></>}
            {source.published_at?.year && <><span aria-hidden>·</span><span>Published <FuzzyDate value={source.published_at} /></span></>}
            {source.accessed_at && <><span aria-hidden>·</span><span>Read {source.accessed_at}</span></>}
            <span aria-hidden>·</span><span className="text-zinc-500">Updated {timeAgo(source.updated_at)}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {isValidUrl(source.url) && (
              <Button size="sm" variant="outline" asChild>
                <a href={source.url} target="_blank" rel="noopener noreferrer"><ExternalLink className="mr-1.5 h-3.5 w-3.5" />Open</a>
              </Button>
            )}
            {source.archive_url && isValidUrl(source.archive_url) && (
              <Button size="sm" variant="outline" asChild>
                <a href={source.archive_url} target="_blank" rel="noopener noreferrer"><Archive className="mr-1.5 h-3.5 w-3.5" />Archived copy</a>
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={() => setCiting(true)}><Link2 className="mr-1.5 h-3.5 w-3.5" />Cite on records</Button>
            <Button size="sm" variant="outline" onClick={() => setEditing(true)}><Pencil className="mr-1.5 h-3.5 w-3.5" />Edit</Button>
            {user?.global_role === 'ADMIN' && (
              <Button size="sm" variant="outline" className="text-red-400 hover:text-red-300" onClick={() => setDeleting(true)}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
              </Button>
            )}
          </div>
          {source.notes && (
            <p className="max-w-3xl whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-sm text-zinc-300">
              <LinkifiedText text={source.notes} />
            </p>
          )}
        </header>

        {tabs.length === 0 ? (
          <p className="rounded-lg border border-dashed border-zinc-800 px-4 py-6 text-center text-sm text-zinc-500">
            Nothing cites this source yet. <button type="button" className="text-violet-400 hover:underline" onClick={() => setCiting(true)}>Cite it on records…</button>
          </p>
        ) : (
          <>
            <div className="mb-4 flex gap-1 overflow-x-auto border-b border-zinc-800 [scrollbar-width:none]" role="tablist">
              {tabs.map((t) => (
                <button key={t.key} type="button" role="tab" aria-selected={active === t.key} onClick={() => setTab(t.key)}
                  className={cn('-mb-px shrink-0 border-b-2 px-3 py-2 text-sm transition-colors',
                    active === t.key ? 'border-violet-500 text-white' : 'border-transparent text-zinc-400 hover:text-zinc-200')}>
                  {t.label} <span className="tabular-nums text-zinc-500">{t.count(source.counts).toLocaleString()}</span>
                </button>
              ))}
            </div>
            {active === 'custody' && <CustodyRows sourceId={source.id} universeId={universe.id} />}
            {active === 'photos' && (
              <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                <PhotoGallery entityType="source" entityId={source.id} universeId={universe.id} />
              </Suspense>
            )}
            {active && active !== 'custody' && active !== 'photos' && (
              <CitationRows key={active} source={source} universeId={universe.id} type={active} />
            )}
          </>
        )}

        {editing && <SourceFormSheet universeId={universe.id} open onClose={() => setEditing(false)} initial={source} />}
        {citing && (
          <EntityCitePicker universeId={universe.id} sourceId={source.id} lookupSystem={source.lookup_system}
            open onClose={() => setCiting(false)} />
        )}
        <ConfirmDialog
          open={deleting}
          title={`Delete "${source.title}"?`}
          description="Every citation of it is removed from the records that cite it. This cannot be undone."
          impact={impact || 'Nothing cites it.'}
          confirmLabel="Delete"
          destructive
          pending={deleteSource.isPending}
          onConfirm={async () => {
            await deleteSource.mutateAsync({ id: source.id, force: true })
            navigate({ from: '/$universe', to: '/$universe/sources' })
          }}
          onCancel={() => setDeleting(false)}
        />
      </div>
    </TooltipProvider>
  )
}
