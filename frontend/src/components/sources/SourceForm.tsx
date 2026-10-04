import { AlertTriangle, Lock } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useDebounce } from '@/hooks/useDebounce'
import { ApiError } from '@/lib/api'
import { useCreateSource, useSourceLookup, useUpdateSource } from '@/lib/queries'
import { KIND_META, KIND_ORDER } from '@/lib/sourceMeta'
import { RELIABILITY_DESCRIPTION, RELIABILITY_LABEL, RELIABILITY_ORDER } from '@/lib/statusColors'
import type { SourceKind, SourceRead, SourceReliability, UUID } from '@/lib/types'

export interface SourceFormProps {
  universeId: UUID
  /** Edit this source; absent, the form creates one. */
  initial?: SourceRead
  defaultUrl?: string
  defaultTitle?: string
  /** Called with the saved source. */
  onSaved: (source: SourceRead) => void
  onCancel: () => void
  /** The URL is already a source: use that one instead of adding a copy. */
  onUseExisting?: (sourceId: UUID) => void
  /** The URL is a custody lookup: cite the system's source with this number. */
  onUseLookup?: (sourceId: UUID, locator: string | null) => void
  submitLabel?: string
}

/** Every field a source has, with a warning before a duplicate is made. */
export function SourceForm({
  universeId, initial, defaultUrl, defaultTitle, onSaved, onCancel, onUseExisting, onUseLookup,
  submitLabel,
}: SourceFormProps) {
  const create = useCreateSource()
  const update = useUpdateSource(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const [url, setUrl] = useState(initial?.url ?? defaultUrl ?? '')
  const [title, setTitle] = useState(initial?.title ?? defaultTitle ?? '')
  const [publication, setPublication] = useState(initial?.publication ?? '')
  const [reliability, setReliability] = useState<SourceReliability>(initial?.reliability ?? 'UNVERIFIED')
  // '' leaves the kind to the URL; a value overrides it.
  const [kind, setKind] = useState<SourceKind | ''>(initial?.kind ?? '')
  const [published, setPublished] = useState<FuzzyDateValue | null>(initial?.published_at ?? null)
  const [accessed, setAccessed] = useState(initial?.accessed_at ?? '')
  const [notes, setNotes] = useState(initial?.notes ?? '')
  const [archiveUrl, setArchiveUrl] = useState(initial?.archive_url ?? '')
  const [error, setError] = useState<string | null>(null)
  const [allowDuplicate, setAllowDuplicate] = useState(false)

  const debouncedUrl = useDebounce(url.trim(), 300)
  const changedUrl = !isEdit || debouncedUrl !== initial?.url
  const { data: lookup } = useSourceLookup(changedUrl ? universeId : null, debouncedUrl)
  const exact = lookup?.exact && lookup.exact.id !== initial?.id ? lookup.exact : null
  const custody = lookup?.lookup && lookup.lookup.source.id !== initial?.id ? lookup.lookup : null

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const body: Record<string, unknown> = {
      url: url.trim(),
      title: title.trim(),
      publication: publication.trim() || null,
      reliability,
      published_at: published && published.precision !== 'UNKNOWN' ? published : null,
      accessed_at: accessed || null,
      notes: notes.trim() || null,
      archive_url: archiveUrl.trim() || null,
    }
    if (kind) body.kind = kind
    try {
      const saved = isEdit
        ? await update.mutateAsync(body)
        : await create.mutateAsync({ ...body, universe_id: universeId, allow_duplicate: allowDuplicate })
      toast.success(`${isEdit ? 'Updated' : 'Added'} "${saved.title}"`)
      onSaved(saved)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'lookup_source' && onUseLookup) {
        onUseLookup(String(err.body?.existing_id), (err.body?.suggested_locator as string) ?? null)
        return
      }
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} source`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="s-url">URL *</Label>
        <Input id="s-url" required value={url} onChange={(e) => { setUrl(e.target.value); setAllowDuplicate(false) }} placeholder="https://…" />
        {custody && (
          <div className="flex items-start gap-2 rounded-md border border-sky-900/60 bg-sky-950/30 px-3 py-2 text-xs text-sky-200">
            <Lock className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <div className="min-w-0 flex-1">
              A custody lookup: <span className="font-medium">{custody.source.title}</span> is already a source.
              Cite it with the record number{custody.suggested_locator ? ` (${custody.suggested_locator})` : ''} rather than adding another.
            </div>
            {onUseLookup && (
              <Button type="button" size="sm" variant="secondary" className="h-6 shrink-0 px-2 text-xs"
                onClick={() => onUseLookup(custody.source.id, custody.suggested_locator)}>
                Cite it
              </Button>
            )}
          </div>
        )}
        {exact && !custody && (
          <div className="flex items-start gap-2 rounded-md border border-amber-900/60 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <div className="min-w-0 flex-1">
              Already on file as <span className="font-medium">{exact.title}</span>.
              {!isEdit && (
                <label className="mt-1 flex items-center gap-1.5 text-amber-300/80">
                  <input type="checkbox" checked={allowDuplicate} onChange={(e) => setAllowDuplicate(e.target.checked)} />
                  Add a second source with this URL anyway
                </label>
              )}
            </div>
            {onUseExisting && (
              <Button type="button" size="sm" variant="secondary" className="h-6 shrink-0 px-2 text-xs"
                onClick={() => onUseExisting(exact.id)}>
                Use it
              </Button>
            )}
          </div>
        )}
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="s-title">Title *</Label>
        <Input id="s-title" required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Article or document title" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="s-pub">Publication</Label>
          <Input id="s-pub" value={publication} onChange={(e) => setPublication(e.target.value)} placeholder="e.g. Detroit Free Press" />
        </div>
        <div className="space-y-1.5">
          <Label>Kind</Label>
          <Select value={kind || '__auto__'} onValueChange={(v) => setKind(v === '__auto__' ? '' : (v as SourceKind))}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__auto__">From the URL</SelectItem>
              {KIND_ORDER.map((k) => <SelectItem key={k} value={k}>{KIND_META[k].label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="space-y-1.5">
        <Label>Reliability</Label>
        <Select value={reliability} onValueChange={(v) => setReliability(v as SourceReliability)}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {RELIABILITY_ORDER.map((r) => (
              <SelectItem key={r} value={r}>{RELIABILITY_LABEL[r]}: {RELIABILITY_DESCRIPTION[r]}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <FuzzyDateInput label="Published" idPrefix="s-published" value={published} onChange={setPublished} />
      <div className="space-y-1.5">
        <Label htmlFor="s-accessed">Read on</Label>
        <Input id="s-accessed" type="date" value={accessed} onChange={(e) => setAccessed(e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="s-notes">Notes</Label>
        <Textarea id="s-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What the document is, where its text came from…" />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="s-archive">Archive URL</Label>
        <Input id="s-archive" value={archiveUrl} onChange={(e) => setArchiveUrl(e.target.value)} placeholder="https://web.archive.org/…" />
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div className="flex gap-2 pt-2">
        <Button type="submit" disabled={isPending || (!!exact && !allowDuplicate && !isEdit)} className="flex-1">
          {isPending ? 'Saving…' : submitLabel ?? (isEdit ? 'Save changes' : 'Add source')}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  )
}
