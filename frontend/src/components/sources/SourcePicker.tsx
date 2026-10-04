import { ArrowLeft, FilePlus, Library, Lock, Search } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { SourceForm } from '@/components/sources/SourceForm'
import { ReliabilityDot } from '@/components/sources/ReliabilityDot'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useDebounce } from '@/hooks/useDebounce'
import { ApiError } from '@/lib/api'
import { useCreateCitation, useSource, useSourceLookup, useSourceSearch } from '@/lib/queries'
import { KIND_META, LOOKUP_LABEL } from '@/lib/sourceMeta'
import type { CitableType, LookupSystem, SourceListItem, UUID } from '@/lib/types'
import { cn } from '@/lib/utils'

interface SourcePickerProps {
  universeId: UUID
  entityType: CitableType
  entityId: UUID
  /** Sources the record already cites: shown, not offered again. */
  citedSourceIds: UUID[]
  open: boolean
  onClose: () => void
}

type Step = { kind: 'search' } | { kind: 'create'; url: string } | { kind: 'detail'; sourceId: UUID; locator: string }

const looksLikeUrl = (s: string) => /^https?:\/\/\S+\.\S+/i.test(s.trim())

/**
 * Cite a source on a record, in one place: find it (a pasted URL finds its
 * source, or its custody lookup with the record number), or make it, then
 * say where in it and what it supports here.
 */
export function SourcePicker({ universeId, entityType, entityId, citedSourceIds, open, onClose }: SourcePickerProps) {
  const [step, setStep] = useState<Step>({ kind: 'search' })
  const [q, setQ] = useState('')

  function close() {
    setStep({ kind: 'search' })
    setQ('')
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && close()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Library className="h-4 w-4 text-violet-400" />
            {step.kind === 'create' ? 'New source' : step.kind === 'detail' ? 'Cite it' : 'Cite a source'}
          </DialogTitle>
          <DialogDescription>
            {step.kind === 'search' && 'Search by title, site or publication, or paste a link.'}
            {step.kind === 'create' && 'Add the document; it is cited here once saved.'}
            {step.kind === 'detail' && 'Where in the source, and what it shows here. All optional.'}
          </DialogDescription>
        </DialogHeader>
        {step.kind === 'search' && (
          <SearchStep
            universeId={universeId}
            q={q}
            setQ={setQ}
            cited={new Set(citedSourceIds)}
            onPick={(sourceId, locator) => setStep({ kind: 'detail', sourceId, locator: locator ?? '' })}
            onCreate={(url) => setStep({ kind: 'create', url })}
          />
        )}
        {step.kind === 'create' && (
          <div className="max-h-[70vh] overflow-y-auto pr-1">
            <SourceForm
              universeId={universeId}
              defaultUrl={step.url}
              submitLabel="Add and cite"
              onSaved={(s) => setStep({ kind: 'detail', sourceId: s.id, locator: '' })}
              onCancel={() => setStep({ kind: 'search' })}
              onUseExisting={(id) => setStep({ kind: 'detail', sourceId: id, locator: '' })}
              onUseLookup={(id, locator) => setStep({ kind: 'detail', sourceId: id, locator: locator ?? '' })}
            />
          </div>
        )}
        {step.kind === 'detail' && (
          <DetailStep
            key={step.sourceId}
            universeId={universeId}
            entityType={entityType}
            entityId={entityId}
            sourceId={step.sourceId}
            initialLocator={step.locator}
            alreadyCited={citedSourceIds.includes(step.sourceId)}
            onBack={() => setStep({ kind: 'search' })}
            onDone={(again) => {
              if (again) { setStep({ kind: 'search' }); setQ('') } else close()
            }}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

function SourceRow({ s, cited, onPick, hint }: {
  s: SourceListItem; cited: boolean; onPick: () => void; hint?: React.ReactNode
}) {
  const Icon = (KIND_META[s.kind] ?? KIND_META.OTHER).icon
  return (
    <button
      type="button"
      disabled={cited}
      onClick={onPick}
      className="flex w-full items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-zinc-800/70 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
    >
      <Icon className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2">
          <ReliabilityDot reliability={s.reliability} />
          <span className="truncate text-sm text-zinc-200">{s.title}</span>
        </span>
        <span className="block truncate text-xs text-zinc-500">
          {[s.publication, s.domain].filter(Boolean).join(' · ')}
          {hint && <> · {hint}</>}
        </span>
      </span>
      <span className="shrink-0 text-xs text-zinc-500">
        {cited ? 'cited' : s.counts.total > 0 ? `${s.counts.total} cite${s.counts.total === 1 ? 's' : ''}` : ''}
      </span>
    </button>
  )
}

function SearchStep({ universeId, q, setQ, cited, onPick, onCreate }: {
  universeId: UUID
  q: string
  setQ: (v: string) => void
  cited: Set<UUID>
  onPick: (sourceId: UUID, locator: string | null) => void
  onCreate: (url: string) => void
}) {
  const debounced = useDebounce(q.trim(), 200)
  const isUrl = looksLikeUrl(debounced)
  const { data: results, isFetching } = useSourceSearch(universeId, isUrl ? '' : debounced)
  const { data: lookup, isFetching: looking } = useSourceLookup(isUrl ? universeId : null, debounced)

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
        <Input
          autoFocus
          className="pl-8"
          placeholder="Title, site, publication, or paste a URL"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <div className="max-h-80 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950 empty:hidden">
        {isUrl && lookup && (
          <>
            {lookup.lookup && (
              <div>
                <div className="flex items-center gap-1.5 border-b border-zinc-800/80 px-3 pt-2 pb-1 text-[11px] uppercase tracking-wider text-sky-300/80">
                  <Lock className="h-3 w-3" /> Custody lookup
                </div>
                <SourceRow
                  s={lookup.lookup.source}
                  cited={false}
                  onPick={() => onPick(lookup.lookup!.source.id, lookup.lookup!.suggested_locator)}
                  hint={lookup.lookup.suggested_locator
                    ? `${LOOKUP_LABEL[lookup.lookup.source.lookup_system as LookupSystem]} ${lookup.lookup.suggested_locator}`
                    : 'record number to add'}
                />
              </div>
            )}
            {lookup.exact && (
              <div>
                <div className="border-b border-zinc-800/80 px-3 pt-2 pb-1 text-[11px] uppercase tracking-wider text-zinc-500">Already on file</div>
                <SourceRow s={lookup.exact} cited={cited.has(lookup.exact.id)} onPick={() => onPick(lookup.exact!.id, null)} />
              </div>
            )}
            {!lookup.lookup && !lookup.exact && (
              <>
                <button
                  type="button"
                  onClick={() => onCreate(debounced)}
                  className="flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm text-violet-300 hover:bg-zinc-800/70"
                >
                  <FilePlus className="h-4 w-4" /> Create a source from this URL
                </button>
                {lookup.same_host.length > 0 && (
                  <div>
                    <div className="border-y border-zinc-800/80 px-3 pt-2 pb-1 text-[11px] uppercase tracking-wider text-zinc-500">
                      Same site
                    </div>
                    {lookup.same_host.map((s) => (
                      <SourceRow key={s.id} s={s} cited={cited.has(s.id)} onPick={() => onPick(s.id, null)} />
                    ))}
                  </div>
                )}
              </>
            )}
          </>
        )}
        {!isUrl && debounced.length >= 2 && results && (
          results.length === 0 ? (
            <p className="px-3 py-3 text-sm text-zinc-500">{isFetching ? 'Searching…' : 'No matching sources.'}</p>
          ) : (
            results.map((s) => (
              <SourceRow key={s.id} s={s} cited={cited.has(s.id)} onPick={() => onPick(s.id, null)} />
            ))
          )
        )}
        {isUrl && looking && !lookup && <p className="px-3 py-3 text-sm text-zinc-500">Checking…</p>}
      </div>
      <Button type="button" variant="outline" className="w-full justify-start" onClick={() => onCreate(isUrl ? debounced : '')}>
        <FilePlus className="mr-2 h-4 w-4" /> New source
      </Button>
    </div>
  )
}

function DetailStep({ universeId, entityType, entityId, sourceId, initialLocator, alreadyCited, onBack, onDone }: {
  universeId: UUID
  entityType: CitableType
  entityId: UUID
  sourceId: UUID
  initialLocator: string
  alreadyCited: boolean
  onBack: () => void
  onDone: (again: boolean) => void
}) {
  const { data: source } = useSource(sourceId, universeId)
  const cite = useCreateCitation(universeId)
  const [locator, setLocator] = useState(initialLocator)
  const [quote, setQuote] = useState('')
  const [note, setNote] = useState('')
  const [accessed, setAccessed] = useState('')
  const lookup = source?.lookup_system ?? null

  async function submit(again: boolean) {
    try {
      await cite.mutateAsync({
        source_id: sourceId,
        entity_type: entityType,
        entity_id: entityId,
        locator: locator.trim() || null,
        quote: quote.trim() || null,
        note: note.trim() || null,
        accessed_at: accessed || null,
      })
      toast.success(`Cited "${source?.title ?? 'source'}"`)
      onDone(again)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'citation_exists') {
        toast.info('Already cited here; edit that citation instead.')
        onDone(false)
      }
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-900/40 px-3 py-2">
        {source && <ReliabilityDot reliability={source.reliability} />}
        <span className="min-w-0 flex-1 truncate text-sm text-zinc-200">{source?.title ?? '…'}</span>
        <span className="shrink-0 text-xs text-zinc-500">{source?.domain}</span>
      </div>
      {alreadyCited && (
        <p className="text-xs text-amber-300">This record already cites this source.</p>
      )}
      <div className="space-y-1.5">
        <Label htmlFor="c-locator">{lookup ? `${LOOKUP_LABEL[lookup]} number` : 'Where in the source'}</Label>
        <Input
          id="c-locator"
          value={locator}
          onChange={(e) => setLocator(e.target.value)}
          placeholder={lookup === 'BOP' ? '12345-039' : lookup ? 'Record number' : 'p. 12, ¶ 4, 01:23, count 3…'}
          className={cn(lookup && 'font-mono')}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="c-quote">Quote</Label>
        <Textarea id="c-quote" rows={2} value={quote} onChange={(e) => setQuote(e.target.value)} placeholder="The words that carry the claim" />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="c-note">What it supports here</Label>
        <Textarea id="c-note" rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Names him in the set; dates the shooting…" />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="c-accessed">Read on</Label>
        <Input id="c-accessed" type="date" value={accessed} onChange={(e) => setAccessed(e.target.value)} />
      </div>
      <div className="flex items-center gap-2 pt-1">
        <Button type="button" variant="ghost" size="sm" onClick={onBack}><ArrowLeft className="mr-1 h-3.5 w-3.5" /> Back</Button>
        <div className="flex-1" />
        <Button type="button" variant="outline" disabled={cite.isPending || alreadyCited} onClick={() => submit(true)}>
          Cite and add another
        </Button>
        <Button type="button" disabled={cite.isPending || alreadyCited} onClick={() => submit(false)}>
          {cite.isPending ? 'Citing…' : 'Cite'}
        </Button>
      </div>
    </div>
  )
}
