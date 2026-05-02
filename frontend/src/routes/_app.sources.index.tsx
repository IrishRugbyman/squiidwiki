import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, ExternalLink, FileText, HelpCircle, Plus, Search, Trash2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { EmptyState } from '@/components/EmptyState'
import { TableRowSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useCreateSource, useUpdateSource, useSources, useDeleteSource } from '@/lib/queries'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import type { UUID } from '@/lib/types'
import { downloadCsv } from '@/lib/download'
import { RELIABILITY_DESCRIPTION } from '@/lib/statusColors'
import type { SourceRead, SourceReliability } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/sources/')({
  component: SourcesPage,
})

interface SourceFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: SourceRead
  defaultUrl?: string
}

export function SourceFormSheet({ universeId, open, onClose, initial, defaultUrl }: SourceFormProps) {
  const create = useCreateSource()
  const update = useUpdateSource(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const [url, setUrl] = useState(initial?.url ?? defaultUrl ?? '')
  const [title, setTitle] = useState(initial?.title ?? '')
  const [publication, setPublication] = useState(initial?.publication ?? '')
  const [reliability, setReliability] = useState<SourceReliability>(initial?.reliability ?? 'UNVERIFIED')
  const [notes, setNotes] = useState(initial?.notes ?? '')
  const [archiveUrl, setArchiveUrl] = useState(initial?.archive_url ?? '')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const body = {
      universe_id: universeId,
      url,
      title,
      publication: publication || null,
      reliability,
      notes: notes || null,
      archive_url: archiveUrl || null,
    }
    try {
      if (isEdit) {
        await update.mutateAsync(body)
        toast.success(`Updated "${title}"`)
      } else {
        await create.mutateAsync(body)
        toast.success(`Added "${title}"`)
        setUrl(''); setTitle(''); setPublication(''); setReliability('UNVERIFIED'); setNotes(''); setArchiveUrl('')
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} source`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Source' : 'Add Source'}
        description={isEdit ? 'Update this source' : 'Add a citation or reference'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="s-url">URL *</Label>
            <Input id="s-url" type="url" required value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="s-title">Title *</Label>
            <Input id="s-title" required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Article or document title" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="s-pub">Publication</Label>
            <Input id="s-pub" value={publication} onChange={(e) => setPublication(e.target.value)} placeholder="e.g. Detroit Free Press" />
          </div>
          <div className="space-y-1.5">
            <Label>Reliability</Label>
            <Select value={reliability} onValueChange={(v) => setReliability(v as SourceReliability)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="HIGH">High — {RELIABILITY_DESCRIPTION.HIGH}</SelectItem>
                <SelectItem value="MEDIUM">Medium — {RELIABILITY_DESCRIPTION.MEDIUM}</SelectItem>
                <SelectItem value="LOW">Low — {RELIABILITY_DESCRIPTION.LOW}</SelectItem>
                <SelectItem value="UNVERIFIED">Unverified — {RELIABILITY_DESCRIPTION.UNVERIFIED}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="s-notes">Notes</Label>
            <Textarea id="s-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Caveats or context…" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="s-archive">Archive URL</Label>
            <Input id="s-archive" type="url" value={archiveUrl} onChange={(e) => setArchiveUrl(e.target.value)} placeholder="https://web.archive.org/…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Source'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}

const RELIABILITY_FILTERS: (SourceReliability | 'ALL')[] = ['ALL', 'HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED']

function SourcesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [publicationFilter, setPublicationFilter] = useState<string>('ALL')
  const [reliabilityFilter, setReliabilityFilter] = useState<SourceReliability | 'ALL'>('ALL')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const [selected, setSelected] = useState<Set<UUID>>(new Set())
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const PAGE = 20

  const { data, isLoading } = useSources(universe?.id ?? null, offset)
  const deleteSource = useDeleteSource(universe?.id ?? '')

  const rawItems = data?.items ?? []

  const publications = useMemo(() => {
    const set = new Set<string>()
    for (const s of rawItems) {
      // publication is on SourceRead; we only have SourceListItem in the list query
      const pub = (s as unknown as { publication?: string | null }).publication
      if (pub) set.add(pub)
    }
    return Array.from(set).sort()
  }, [rawItems])

  if (!universe) return <NoUniverse />

  const total = data?.total ?? 0

  const items = rawItems
    .filter((s) => !q || s.title.toLowerCase().includes(q.toLowerCase()))
    .filter((s) => reliabilityFilter === 'ALL' || s.reliability === reliabilityFilter)
    .filter((s) => {
      if (publicationFilter === 'ALL') return true
      const pub = (s as unknown as { publication?: string | null }).publication
      return pub === publicationFilter
    })

  function toggleSelect(id: UUID) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    setSelected(selected.size === items.length ? new Set() : new Set(items.map((s) => s.id)))
  }

  async function bulkDelete() {
    if (selected.size === 0) return
    const ids = Array.from(selected)
    setBulkDeleting(true)
    try {
      await Promise.all(ids.map((id) => deleteSource.mutateAsync(id)))
      toast.success(`Deleted ${ids.length} source${ids.length === 1 ? '' : 's'}`)
      setSelected(new Set())
      setConfirmingDelete(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Bulk delete failed')
    } finally {
      setBulkDeleting(false)
    }
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div>
        <PageHeader
          title="Sources"
          description={total > 0 ? `${total} total` : 'No sources yet'}
          action={
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => {
                const date = new Date().toISOString().slice(0, 10)
                downloadCsv(`/sources/?universe_id=${universe.id}&format=csv`, `sources-${universe.slug}-${date}.csv`)
              }}>
                <Download className="mr-1.5 h-3.5 w-3.5" />Export
              </Button>
              <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Source</Button>
            </div>
          }
        />

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-48 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
            <Input className="pl-8" placeholder="Filter sources…" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <Select value={reliabilityFilter} onValueChange={(v) => setReliabilityFilter(v as SourceReliability | 'ALL')}>
            <SelectTrigger className="h-8 w-36 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              {RELIABILITY_FILTERS.map((r) => (
                <SelectItem key={r} value={r}>{r === 'ALL' ? 'All reliability' : r}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {publications.length > 0 && (
            <Select value={publicationFilter} onValueChange={setPublicationFilter}>
              <SelectTrigger className="h-8 w-40 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All publications</SelectItem>
                {publications.map((pub) => (
                  <SelectItem key={pub} value={pub}>{pub}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        <div className="overflow-hidden rounded-lg border border-zinc-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900/50">
                <th className="w-10 px-3 py-2.5" scope="col">
                  <input
                    type="checkbox"
                    aria-label="Select all sources"
                    checked={items.length > 0 && selected.size === items.length}
                    onChange={toggleAll}
                    className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                  />
                </th>
                <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Title</th>
                <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">
                  <span className="inline-flex items-center gap-1">
                    Reliability
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-3 w-3 text-zinc-600 hover:text-zinc-400" />
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <div className="space-y-1 max-w-xs">
                          <div><strong>HIGH</strong> — {RELIABILITY_DESCRIPTION.HIGH}</div>
                          <div><strong>MEDIUM</strong> — {RELIABILITY_DESCRIPTION.MEDIUM}</div>
                          <div><strong>LOW</strong> — {RELIABILITY_DESCRIPTION.LOW}</div>
                          <div><strong>UNVERIFIED</strong> — {RELIABILITY_DESCRIPTION.UNVERIFIED}</div>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </span>
                </th>
                <th className="px-4 py-2.5 text-left font-medium text-zinc-400 w-10" scope="col" aria-label="Open external link"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={4} height={52} />)
                : items.map((source) => (
                    <tr key={source.id} className={`hover:bg-zinc-900/50 transition-colors ${selected.has(source.id) ? 'bg-violet-950/20' : ''}`}>
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          aria-label={`Select ${source.title}`}
                          checked={selected.has(source.id)}
                          onChange={() => toggleSelect(source.id)}
                          className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                        />
                      </td>
                      <td className="p-0">
                        <Link to="/sources/$id" params={{ id: source.id }} className="block px-4 py-3 font-medium text-white hover:text-violet-400 transition-colors">
                          {source.title}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="inline-block">
                              <ReliabilityBadge reliability={source.reliability} />
                            </span>
                          </TooltipTrigger>
                          <TooltipContent side="top">{RELIABILITY_DESCRIPTION[source.reliability]}</TooltipContent>
                        </Tooltip>
                      </td>
                      <td className="px-4 py-3">
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label="Open source in new tab"
                          className="rounded p-1 text-zinc-500 hover:text-violet-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      </td>
                    </tr>
                  ))}
              {!isLoading && items.length === 0 && (
                <tr>
                  <td colSpan={4}>
                    <EmptyState
                      icon={FileText}
                      title={q ? `No sources match "${q}"` : 'No sources yet'}
                      description={!q ? 'Add a citation to underpin the incidents you record.' : undefined}
                      action={
                        !q ? (
                          <Button size="sm" onClick={() => setCreating(true)}>
                            <Plus className="mr-1.5 h-4 w-4" /> Add the first source
                          </Button>
                        ) : undefined
                      }
                    />
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {!q && total > PAGE && (
          <nav className="mt-4 flex items-center justify-between text-sm text-zinc-400" aria-label="Pagination">
            <span>Showing {offset + 1}–{Math.min(offset + PAGE, total)} of {total}</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" aria-disabled={offset === 0} disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Prev</Button>
              <Button variant="outline" size="sm" aria-disabled={offset + PAGE >= total} disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>Next</Button>
            </div>
          </nav>
        )}

        <SourceFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />

        <BulkActionBar count={selected.size} label="source" onClear={() => setSelected(new Set())}>
          <Button
            size="sm"
            variant="destructive"
            className="h-7 text-xs"
            onClick={() => setConfirmingDelete(true)}
            disabled={bulkDeleting}
          >
            <Trash2 className="mr-1 h-3 w-3" />
            Delete
          </Button>
        </BulkActionBar>

        <ConfirmDialog
          open={confirmingDelete}
          title={`Delete ${selected.size} source${selected.size === 1 ? '' : 's'}?`}
          description="This cannot be undone. Incidents and members citing these sources will lose the link."
          confirmLabel="Delete"
          destructive
          pending={bulkDeleting}
          onConfirm={bulkDelete}
          onCancel={() => setConfirmingDelete(false)}
        />
      </div>
    </TooltipProvider>
  )
}
