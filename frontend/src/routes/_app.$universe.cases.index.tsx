import { createFileRoute } from '@tanstack/react-router'
import { X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { Sheet, SheetClose, SheetContent } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useDebounce } from '@/hooks/useDebounce'
import { CASE_KIND_LABEL, CASE_KINDS, courtAndDocket, JURISDICTION_LABEL, JURISDICTIONS } from '@/lib/courtCases'
import { useAllSets, useCourtCaseSearch, useCreateCourtCase, useUpdateCourtCase } from '@/lib/queries'
import { textParam } from '@/lib/searchParams'
import type { CourtCaseKind, CourtCaseRead, CourtCaseReadDetail, CourtJurisdiction, UUID } from '@/lib/types'

export interface CasesSearch {
  q?: string
}

// The page is in _app.$universe.cases.index.lazy.tsx, its own chunk; this file
// keeps the URL schema and the form sheet, which the member, set, incident and
// alliance pages open too.
export const Route = createFileRoute('/_app/$universe/cases/')({
  validateSearch: (s: Record<string, unknown>): CasesSearch => ({ q: textParam(s.q) }),
})

/** Lines or commas to a clean list, blanks and repeats dropped. */
function splitList(raw: string): string[] {
  const out: string[] = []
  for (const part of raw.split(/[\n,]/)) {
    const v = part.trim()
    if (v && !out.includes(v)) out.push(v)
  }
  return out
}

interface CourtCaseFormProps {
  universeId: UUID
  open: boolean
  onClose: () => void
  initial?: CourtCaseReadDetail
  /** Prefills for a case started from a set or an incident page. */
  defaultSetIds?: UUID[]
  defaultIncidentIds?: UUID[]
  onSaved?: (c: CourtCaseRead) => void
}

/** Keyed on the case so a reused sheet never carries one case's values into another. */
export function CourtCaseFormSheet(props: CourtCaseFormProps) {
  return <CourtCaseFormSheetInner key={props.initial?.id ?? 'new'} {...props} />
}

function CourtCaseFormSheetInner({
  universeId, open, onClose, initial, defaultSetIds, defaultIncidentIds, onSaved,
}: CourtCaseFormProps) {
  const create = useCreateCourtCase()
  const update = useUpdateCourtCase(initial?.id ?? '', universeId)
  const isEdit = !!initial
  const { data: setsData } = useAllSets(universeId)
  const allSets = useMemo(() => (setsData?.items ?? []).filter((s) => !s.is_reserved), [setsData])

  const [name, setName] = useState(initial?.name ?? '')
  const [jurisdiction, setJurisdiction] = useState<CourtJurisdiction>(initial?.jurisdiction ?? 'US_FEDERAL')
  const [kind, setKind] = useState<CourtCaseKind>(initial?.kind ?? 'CRIMINAL')
  const [court, setCourt] = useState(initial?.court ?? '')
  const [docket, setDocket] = useState(initial?.docket ?? '')
  const [aliases, setAliases] = useState((initial?.docket_aliases ?? []).join('\n'))
  const [filedAt, setFiledAt] = useState<FuzzyDateValue | null>(initial?.filed_at ?? null)
  const [closedAt, setClosedAt] = useState<FuzzyDateValue | null>(initial?.closed_at ?? null)
  const [judge, setJudge] = useState(initial?.judge ?? '')
  const [summary, setSummary] = useState(initial?.summary ?? '')
  const [courtlistener, setCourtlistener] = useState((initial?.courtlistener_ids ?? []).join(', '))
  const [setIds, setSetIds] = useState<UUID[]>(initial?.sets.map((s) => s.id) ?? defaultSetIds ?? [])
  const [parent, setParent] = useState<{ id: UUID; label: string } | null>(
    initial?.parent ? { id: initial.parent.id, label: initial.parent.name } : null,
  )
  const [parentQuery, setParentQuery] = useState('')
  const debouncedParent = useDebounce(parentQuery, 200)
  const { data: parentHits = [] } = useCourtCaseSearch(universeId, debouncedParent)
  const [error, setError] = useState<string | null>(null)

  const setName_ = useMemo(() => new Map(allSets.map((s) => [s.id, s.name])), [allSets])
  const courtlistenerIds = courtlistener.split(/[\s,]+/).filter(Boolean)
  const badCourtlistener = courtlistenerIds.some((v) => !/^\d+$/.test(v))

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    if (badCourtlistener) {
      setError('CourtListener ids are numbers, separated by commas')
      return
    }
    const body: Record<string, unknown> = {
      name: name.trim(),
      jurisdiction,
      kind,
      court: court.trim(),
      docket: docket.trim() || null,
      docket_aliases: splitList(aliases),
      filed_at: filedAt,
      closed_at: closedAt,
      judge: judge.trim() || null,
      summary: summary.trim() || null,
      courtlistener_ids: courtlistenerIds.map(Number),
      parent_case_id: parent?.id ?? null,
      set_ids: setIds,
    }
    try {
      const saved = isEdit
        ? await update.mutateAsync(body)
        : await create.mutateAsync({ ...body, universe_id: universeId, incident_ids: defaultIncidentIds ?? [] })
      toast.success(isEdit ? `Updated ${saved.name}` : `Added ${saved.name}`)
      onSaved?.(saved)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} case`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending
  const parentChoices = parentHits.filter((c) => c.id !== initial?.id)

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit court case' : 'Add court case'}
        description={isEdit ? initial.name : 'A prosecution or suit, as the court filed it'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="cc-name">Name *</Label>
            <Input id="cc-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="United States v. Surname et al." />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Jurisdiction</Label>
              <Select value={jurisdiction} onValueChange={(v) => { if (v) setJurisdiction(v as CourtJurisdiction) }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {JURISDICTIONS.map((j) => <SelectItem key={j} value={j}>{JURISDICTION_LABEL[j]}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Kind</Label>
              <Select value={kind} onValueChange={(v) => { if (v) setKind(v as CourtCaseKind) }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {CASE_KINDS.map((k) => <SelectItem key={k} value={k}>{CASE_KIND_LABEL[k]}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="cc-court">Court *</Label>
              <Input id="cc-court" required value={court} onChange={(e) => setCourt(e.target.value)} placeholder="E.D. Mich." />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cc-docket">Docket</Label>
              <Input id="cc-docket" value={docket} onChange={(e) => setDocket(e.target.value)} placeholder="2:17-cr-20740" className="font-mono" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cc-aliases">Other spellings of the docket</Label>
            <Textarea id="cc-aliases" rows={2} value={aliases} onChange={(e) => setAliases(e.target.value)}
              placeholder="One per line, as OTIS or a case file wrote it" className="font-mono text-xs" />
          </div>
          <div className="grid gap-3 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 sm:grid-cols-2">
            <FuzzyDateInput value={filedAt} onChange={setFiledAt} label="Filed" idPrefix="cc-filed" />
            <FuzzyDateInput value={closedAt} onChange={setClosedAt} label="Closed" idPrefix="cc-closed" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cc-judge">Judge</Label>
            <Input id="cc-judge" value={judge} onChange={(e) => setJudge(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Sets the case is about</Label>
            {setIds.length > 0 && (
              <ul className="flex flex-wrap gap-1.5">
                {setIds.map((id) => (
                  <li key={id} className="flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800/60 py-0.5 pl-2 pr-1 text-xs text-zinc-200">
                    {setName_.get(id) ?? 'Unknown set'}
                    <button type="button" onClick={() => setSetIds(setIds.filter((x) => x !== id))} aria-label={`Remove ${setName_.get(id) ?? 'set'}`}
                      className="rounded p-0.5 text-zinc-500 hover:text-zinc-200"><X className="h-3 w-3" /></button>
                  </li>
                ))}
              </ul>
            )}
            <Select value="" onValueChange={(v) => { if (v && !setIds.includes(v)) setSetIds([...setIds, v]) }}>
              <SelectTrigger><SelectValue placeholder="Add a set…" /></SelectTrigger>
              <SelectContent>
                {allSets.filter((s) => !setIds.includes(s.id)).map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cc-parent">Grew out of, or appeals</Label>
            {parent ? (
              <div className="flex items-center justify-between rounded-md border border-zinc-800 px-2.5 py-1.5 text-sm text-zinc-200">
                <span className="truncate">{parent.label}</span>
                <button type="button" onClick={() => setParent(null)} aria-label="Clear the parent case" className="rounded p-0.5 text-zinc-500 hover:text-zinc-200"><X className="h-3.5 w-3.5" /></button>
              </div>
            ) : (
              <>
                <Input id="cc-parent" value={parentQuery} onChange={(e) => setParentQuery(e.target.value)} placeholder="Search a case by name or docket" />
                {parentQuery.length >= 2 && parentChoices.length > 0 && (
                  <ul className="max-h-40 overflow-y-auto rounded-md border border-zinc-800">
                    {parentChoices.map((c) => (
                      <li key={c.id}>
                        <button type="button" onClick={() => { setParent({ id: c.id, label: c.name }); setParentQuery('') }}
                          className="block w-full px-2.5 py-1.5 text-left text-sm text-zinc-200 hover:bg-zinc-800">
                          {c.name}<span className="ml-2 text-xs text-zinc-500">{courtAndDocket(c)}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cc-summary">Summary</Label>
            <Textarea id="cc-summary" rows={4} value={summary} onChange={(e) => setSummary(e.target.value)}
              placeholder="What no field holds: the enterprise the indictment describes, how the case was built" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cc-cl">CourtListener docket ids</Label>
            <Input id="cc-cl" value={courtlistener} onChange={(e) => setCourtlistener(e.target.value)} placeholder="6253865, 7648516" className="font-mono" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Add case'}
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
