import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { toast } from 'sonner'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useCreateSource, useUpdateSource } from '@/lib/queries'
import { RELIABILITY_DESCRIPTION } from '@/lib/statusColors'
import type { SourceRead, SourceReliability } from '@/lib/types'
import { textParam } from '@/lib/searchParams'

export type SourceSortKey = 'added' | 'title' | 'published' | 'cited' | 'reliability'

export interface SourcesSearch {
  q?: string
  reliability?: SourceReliability
  /** A publication name, or '__none__' for sources without one. */
  publication?: string
  uncited?: boolean
  sort?: SourceSortKey
  order?: 'asc' | 'desc'
}

const SORT_KEYS: SourceSortKey[] = ['added', 'title', 'published', 'cited', 'reliability']
const RELIABILITY_KEYS: SourceReliability[] = ['HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED']

// The page is in _app.sources.index.lazy.tsx, its own chunk; this file keeps
// the URL schema and the form sheet, which other screens import.
export const Route = createFileRoute('/_app/sources/')({
  validateSearch: (s: Record<string, unknown>): SourcesSearch => ({
    q: textParam(s.q),
    reliability: typeof s.reliability === 'string' && (RELIABILITY_KEYS as string[]).includes(s.reliability) ? (s.reliability as SourceReliability) : undefined,
    publication: textParam(s.publication),
    uncited: s.uncited === true || s.uncited === 'true' ? true : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as SourceSortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
  }),
})

interface SourceFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: SourceRead
  defaultUrl?: string
}

/**
 * Seeded from props at mount and never resynced, so one mounted sheet reused
 * for a second source kept the first's values in any field the second leaves
 * empty - and saving wrote them. Keying on the target forces a fresh instance.
 * See SetFormSheet in routes/_app.sets.index.tsx for the full note.
 */
export function SourceFormSheet(props: SourceFormProps) {
  return <SourceFormSheetInner key={props.initial?.id ?? 'new'} {...props} />
}

function SourceFormSheetInner({ universeId, open, onClose, initial, defaultUrl }: SourceFormProps) {
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
                <SelectItem value="HIGH">High: {RELIABILITY_DESCRIPTION.HIGH}</SelectItem>
                <SelectItem value="MEDIUM">Medium: {RELIABILITY_DESCRIPTION.MEDIUM}</SelectItem>
                <SelectItem value="LOW">Low: {RELIABILITY_DESCRIPTION.LOW}</SelectItem>
                <SelectItem value="UNVERIFIED">Unverified: {RELIABILITY_DESCRIPTION.UNVERIFIED}</SelectItem>
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
