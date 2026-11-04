import { Plus, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useDebounce } from '@/hooks/useDebounce'
import { DISPOSITION_LABEL, DISPOSITIONS } from '@/lib/courtCases'
import { useMemberSearch, useSaveDefendant, useUniverses } from '@/lib/queries'
import type { CaseDisposition, Charge, DefendantRead, UUID } from '@/lib/types'

interface DefendantDialogProps {
  caseId: UUID
  /** The case's universe, which is where its routes are addressed. */
  universeId: UUID
  open: boolean
  onClose: () => void
  initial?: DefendantRead
}

const blankCharge = (): Charge => ({ count: null, statute: null, offense: null, disposition: null })
const toInt = (v: string): number | null => (v.trim() === '' ? null : Number.parseInt(v, 10))

/** Years and months typed separately, stored as months. */
function MonthsInput({ id, label, months, onChange }: {
  id: string; label: string; months: number | null; onChange: (m: number | null) => void
}) {
  const years = months == null ? '' : String(Math.floor(months / 12))
  const rest = months == null ? '' : String(months % 12)
  const set = (y: string, m: string) => {
    if (y.trim() === '' && m.trim() === '') return onChange(null)
    onChange((toInt(y) ?? 0) * 12 + (toInt(m) ?? 0))
  }
  return (
    <div className="space-y-1.5">
      <Label htmlFor={`${id}-y`}>{label}</Label>
      <div className="flex items-center gap-1.5">
        <Input id={`${id}-y`} inputMode="numeric" value={years} onChange={(e) => set(e.target.value, rest)} className="w-16" aria-label={`${label}, years`} />
        <span className="text-xs text-zinc-500">yrs</span>
        <Input inputMode="numeric" value={rest} onChange={(e) => set(years, e.target.value)} className="w-16" aria-label={`${label}, months`} />
        <span className="text-xs text-zinc-500">mos</span>
      </div>
    </div>
  )
}

/** Add or edit one defendant. A member can come from any universe (the court
 *  sits in one place, the man lives in another), so the search runs in the
 *  universe picked here; someone the wiki has no member for gets a label. */
export function DefendantDialog(props: DefendantDialogProps) {
  return <DefendantDialogInner key={props.initial?.id ?? 'new'} {...props} />
}

function DefendantDialogInner({ caseId, universeId, open, onClose, initial }: DefendantDialogProps) {
  const save = useSaveDefendant(caseId, universeId)
  const { data: universes } = useUniverses()
  const [searchUniverse, setSearchUniverse] = useState<UUID>(universeId)
  const [member, setMember] = useState<{ id: UUID; name: string } | null>(
    initial?.member_id ? { id: initial.member_id, name: initial.member_name ?? 'Member' } : null,
  )
  const [query, setQuery] = useState('')
  const debounced = useDebounce(query, 200)
  const { data: hits = [] } = useMemberSearch(searchUniverse, debounced)
  const [label, setLabel] = useState(initial?.label ?? '')
  const [number, setNumber] = useState(initial?.defendant_number ?? '')
  const [disposition, setDisposition] = useState<CaseDisposition>(initial?.disposition ?? 'PENDING')
  const [charges, setCharges] = useState<Charge[]>(initial?.charges ?? [])
  const [sentence, setSentence] = useState<number | null>(initial?.sentence_months ?? null)
  const [life, setLife] = useState(initial?.life_sentence ?? false)
  const [supervised, setSupervised] = useState<number | null>(initial?.supervised_release_months ?? null)
  const [sentencedAt, setSentencedAt] = useState<FuzzyDateValue | null>(initial?.sentenced_at ?? null)
  const [cooperated, setCooperated] = useState(initial?.cooperated ?? false)
  const [notes, setNotes] = useState(initial?.notes ?? '')
  const [error, setError] = useState<string | null>(null)

  const editCharge = (i: number, patch: Partial<Charge>) =>
    setCharges(charges.map((c, j) => (j === i ? { ...c, ...patch } : c)))

  async function submit() {
    setError(null)
    if (!member && !label.trim()) {
      setError('Pick a member, or give a label such as "D-7" for someone not in the wiki')
      return
    }
    const body = {
      member_id: member?.id ?? null,
      label: label.trim() || null,
      defendant_number: number.trim() || null,
      disposition,
      charges: charges.filter((c) => c.statute || c.offense || c.count != null),
      sentence_months: life ? null : sentence,
      life_sentence: life,
      supervised_release_months: supervised,
      sentenced_at: sentencedAt,
      cooperated,
      notes: notes.trim() || null,
    }
    try {
      await save.mutateAsync({ id: initial?.id, body })
      toast.success(initial ? 'Defendant updated' : 'Defendant added')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save the defendant')
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{initial ? 'Edit defendant' : 'Add defendant'}</DialogTitle>
          <DialogDescription>Who was charged, with what, and how it ended.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="d-member">Member</Label>
            {member ? (
              <div className="flex items-center justify-between rounded-md border border-zinc-800 px-2.5 py-1.5 text-sm text-zinc-200">
                <span className="truncate">{member.name}</span>
                <button type="button" onClick={() => setMember(null)} aria-label="Clear the member" className="rounded p-0.5 text-zinc-500 hover:text-zinc-200"><X className="h-3.5 w-3.5" /></button>
              </div>
            ) : (
              <>
                <div className="flex gap-2">
                  <Select value={searchUniverse} onValueChange={(v) => { if (v) setSearchUniverse(v) }}>
                    <SelectTrigger className="w-36 shrink-0" aria-label="Universe to search"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {(universes?.items ?? []).map((u) => <SelectItem key={u.id} value={u.id}>{u.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                  <Input id="d-member" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search members" />
                </div>
                {query.length >= 2 && hits.length > 0 && (
                  <ul className="max-h-40 overflow-y-auto rounded-md border border-zinc-800">
                    {hits.map((m) => (
                      <li key={m.id}>
                        <button type="button" onClick={() => { setMember({ id: m.id, name: m.display_name }); setQuery('') }}
                          className="block w-full px-2.5 py-1.5 text-left text-sm text-zinc-200 hover:bg-zinc-800">
                          {m.display_name}
                          {m.primary_set_name && <span className="ml-2 text-xs text-zinc-500">{m.primary_set_name}</span>}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="d-label">{member ? 'Label (optional)' : 'Label'}</Label>
              <Input id="d-label" value={label} onChange={(e) => setLabel(e.target.value)} placeholder="As the indictment names them" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="d-number">Defendant number</Label>
              <Input id="d-number" value={number} onChange={(e) => setNumber(e.target.value)} placeholder="D-3" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>Disposition</Label>
            <Select value={disposition} onValueChange={(v) => { if (v) setDisposition(v as CaseDisposition) }}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {DISPOSITIONS.map((d) => <SelectItem key={d} value={d}>{DISPOSITION_LABEL[d]}</SelectItem>)}
              </SelectContent>
            </Select>
            {disposition === 'ACQUITTED' && (
              <p className="text-[11px] text-zinc-500">Marks them acquitted in every incident this case covers, unless another case convicted them of it.</p>
            )}
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Charges</Label>
              <button type="button" onClick={() => setCharges([...charges, blankCharge()])} className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-violet-400">
                <Plus className="h-3 w-3" />Add count
              </button>
            </div>
            {charges.map((c, i) => (
              <div key={i} className="grid grid-cols-[3.5rem_minmax(0,1fr)_minmax(0,1.4fr)_auto] gap-1.5">
                <Input inputMode="numeric" value={c.count ?? ''} onChange={(e) => editCharge(i, { count: toInt(e.target.value) })} placeholder="#" aria-label="Count number" />
                <Input value={c.statute ?? ''} onChange={(e) => editCharge(i, { statute: e.target.value || null })} placeholder="18 U.S.C. 1962(d)" className="font-mono text-xs" aria-label="Statute" />
                <Input value={c.offense ?? ''} onChange={(e) => editCharge(i, { offense: e.target.value || null })} placeholder="Offense" aria-label="Offense" />
                <button type="button" onClick={() => setCharges(charges.filter((_, j) => j !== i))} aria-label="Remove this count" className="rounded p-1.5 text-zinc-500 hover:text-zinc-200"><X className="h-3.5 w-3.5" /></button>
              </div>
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {!life && <MonthsInput id="d-sentence" label="Sentence" months={sentence} onChange={setSentence} />}
            <MonthsInput id="d-supervised" label="Supervised release" months={supervised} onChange={setSupervised} />
          </div>
          <div className="flex flex-wrap gap-4 text-sm text-zinc-300">
            <label className="flex items-center gap-2"><input type="checkbox" checked={life} onChange={(e) => setLife(e.target.checked)} className="accent-violet-600" />Life sentence</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={cooperated} onChange={(e) => setCooperated(e.target.checked)} className="accent-violet-600" />Cooperated</label>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <FuzzyDateInput value={sentencedAt} onChange={setSentencedAt} label="Sentenced" idPrefix="d-sentenced" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="d-notes">Notes</Label>
            <Textarea id="d-notes" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={submit} disabled={save.isPending}>{save.isPending ? 'Saving…' : initial ? 'Save' : 'Add defendant'}</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
