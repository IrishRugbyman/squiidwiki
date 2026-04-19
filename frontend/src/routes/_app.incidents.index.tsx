import { createFileRoute, Link } from '@tanstack/react-router'
import { Plus, ShieldAlert } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useCreateIncident, useUpdateIncident, useIncidents, useMemberSearch, useMunicipalities } from '@/lib/queries'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { IncidentReadDetail, IncidentType, ParticipantOutcome, ParticipantRole, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/incidents/')({
  component: IncidentsPage,
})

interface ParticipantDraft {
  member_id: UUID
  member_name: string
  role: ParticipantRole
  outcome: ParticipantOutcome
}

interface DeathDatePrompt {
  memberId: UUID
  memberName: string
  date: FuzzyDateValue | null
}

function ParticipantBuilder({ universeId, participants, onChange, onDeathDateNeeded }: {
  universeId: string
  participants: ParticipantDraft[]
  onChange: (p: ParticipantDraft[]) => void
  onDeathDateNeeded?: (prompt: DeathDatePrompt) => void
}) {
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<ParticipantRole>('VICTIM')
  const [outcome, setOutcome] = useState<ParticipantOutcome>('UNKNOWN')
  const { data: results } = useMemberSearch(universeId, search)

  function addParticipant(memberId: UUID, memberName: string) {
    if (participants.some((p) => p.member_id === memberId)) return
    onChange([...participants, { member_id: memberId, member_name: memberName, role, outcome }])
    setSearch('')
    if (role === 'VICTIM' && outcome === 'KILLED' && onDeathDateNeeded) {
      onDeathDateNeeded({ memberId, memberName, date: null })
    }
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1">
          <Label>Role</Label>
          <Select value={role} onValueChange={(v) => setRole(v as ParticipantRole)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {(['SHOOTER', 'ASSISTED', 'BYSTANDER', 'VICTIM'] as ParticipantRole[]).map((r) => (
                <SelectItem key={r} value={r}>{r}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <Label>Outcome</Label>
          <Select value={outcome} onValueChange={(v) => setOutcome(v as ParticipantOutcome)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {(['KILLED', 'INJURED', 'UNHARMED', 'UNKNOWN'] as ParticipantOutcome[]).map((o) => (
                <SelectItem key={o} value={o}>{o}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <Input
        placeholder="Search member to add…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {results && results.length > 0 && search.length >= 2 && (
        <div className="max-h-32 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
          {results.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => addParticipant(m.id, m.display_name)}
              className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
            >
              {m.display_name}
            </button>
          ))}
        </div>
      )}
      {participants.length > 0 && (
        <div className="space-y-1.5">
          {participants.map((p) => (
            <div key={p.member_id} className="flex items-center justify-between rounded border border-zinc-800 px-3 py-1.5 text-sm">
              <span className="text-zinc-200">{p.member_name}</span>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">{p.role}</Badge>
                <Badge variant="outline" className="text-xs">{p.outcome}</Badge>
                <button
                  type="button"
                  onClick={() => onChange(participants.filter((x) => x.member_id !== p.member_id))}
                  className="text-zinc-600 hover:text-red-400 transition-colors text-xs"
                >✕</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface IncidentFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: IncidentReadDetail
  pendingDeathUpdates?: Map<UUID, FuzzyDateValue | null>
}

export function IncidentFormSheet({ universeId, open, onClose, initial }: IncidentFormProps) {
  const create = useCreateIncident()
  const update = useUpdateIncident(initial?.id ?? '', universeId)
  const isEdit = !!initial
  const { data: munis } = useMunicipalities(universeId)

  const [type, setType] = useState<IncidentType>(initial?.type ?? 'SHOOTING')
  const [date, setDate] = useState<FuzzyDateValue | null>(initial?.date ?? null)
  const [locationText, setLocationText] = useState(initial?.location_text ?? '')
  const [municipalityId, setMunicipalityId] = useState<string>(initial?.municipality_id ?? '')
  const [narrative, setNarrative] = useState(initial?.narrative ?? '')
  const [verified, setVerified] = useState(initial?.verified ?? false)
  const [participants, setParticipants] = useState<ParticipantDraft[]>(
    initial?.participants?.map((p) => ({ member_id: p.member_id, member_name: p.member_id, role: p.role, outcome: p.outcome })) ?? []
  )
  const [deathPrompts, setDeathPrompts] = useState<DeathDatePrompt[]>([])
  const [error, setError] = useState<string | null>(null)

  function handleDeathDateNeeded(prompt: DeathDatePrompt) {
    setDeathPrompts((prev) => [...prev, prompt])
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      const body: Record<string, unknown> = {
        universe_id: universeId,
        type,
        date,
        location_text: locationText || null,
        municipality_id: municipalityId || null,
        narrative: narrative || null,
        verified,
        participants: participants.map(({ member_id, role, outcome }) => ({ member_id, role, outcome })),
      }
      if (isEdit) await update.mutateAsync(body)
      else await create.mutateAsync(body)

      if (!isEdit) {
        setType('SHOOTING'); setDate(null); setLocationText(''); setMunicipalityId('')
        setNarrative(''); setVerified(false); setParticipants([]); setDeathPrompts([])
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} incident`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Incident' : 'Add Incident'}
        description={isEdit ? 'Update this incident' : 'Record a new incident'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Type</Label>
            <Select value={type} onValueChange={(v) => setType(v as IncidentType)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="SHOOTING">Shooting</SelectItem>
                <SelectItem value="MURDER">Murder</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <FuzzyDateInput value={date} onChange={setDate} label="Date" idPrefix="inc-date" />
          </div>

          <div className="space-y-1.5">
            <Label>Municipality</Label>
            <Select value={municipalityId || 'none'} onValueChange={(v) => setMunicipalityId(v === 'none' ? '' : v)}>
              <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">— None —</SelectItem>
                {(munis?.items ?? []).map((m) => (
                  <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="inc-loc">Location</Label>
            <Input id="inc-loc" value={locationText} onChange={(e) => setLocationText(e.target.value)} placeholder="Street address or area" />
          </div>

          <div className="flex items-center gap-2">
            <input
              id="inc-verified" type="checkbox"
              checked={verified}
              onChange={(e) => setVerified(e.target.checked)}
              className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
            />
            <label htmlFor="inc-verified" className="text-sm text-zinc-300">Verified</label>
          </div>

          {!isEdit && (
            <div className="space-y-1.5">
              <Label>Participants</Label>
              <ParticipantBuilder
                universeId={universeId}
                participants={participants}
                onChange={setParticipants}
                onDeathDateNeeded={handleDeathDateNeeded}
              />
            </div>
          )}

          {deathPrompts.length > 0 && (
            <div className="space-y-3 rounded-lg border border-amber-800 bg-amber-950/30 p-3">
              <p className="text-xs font-semibold text-amber-400">Killed participant(s) — set date of death?</p>
              {deathPrompts.map((prompt) => (
                <div key={prompt.memberId}>
                  <p className="mb-1 text-xs text-zinc-300">{prompt.memberName}</p>
                  <FuzzyDateInput
                    value={prompt.date}
                    onChange={(v) => setDeathPrompts((prev) =>
                      prev.map((p) => p.memberId === prompt.memberId ? { ...p, date: v } : p)
                    )}
                    idPrefix={`dod-${prompt.memberId}`}
                  />
                </div>
              ))}
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="inc-narrative">Narrative</Label>
            <Textarea id="inc-narrative" rows={4} value={narrative} onChange={(e) => setNarrative(e.target.value)} placeholder="What happened…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Incident'}
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

function IncidentsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)

  const { data, isLoading } = useIncidents(universe?.id ?? null, cursor)

  if (!universe) return <NoUniverse />

  const items = data?.items ?? []

  return (
    <div>
      <PageHeader
        title="Incidents"
        description={data?.total != null ? `${data.total} total` : undefined}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Incident</Button>}
      />

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Type</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Date</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Verified</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={3}><Skeleton className="h-4 w-48" /></td>
                  </tr>
                ))
              : items.map((incident) => (
                  <tr key={incident.id} className="hover:bg-zinc-900/50 transition-colors">
                    <td className="p-0">
                      <Link to="/incidents/$id" params={{ id: incident.id }} className="flex items-center gap-2 px-4 py-3 text-white hover:text-violet-400 transition-colors">
                        <ShieldAlert className="h-3.5 w-3.5 text-zinc-500" />
                        {incident.type}
                      </Link>
                    </td>
                    <td className="p-0">
                      <Link to="/incidents/$id" params={{ id: incident.id }} className="block px-4 py-3 text-zinc-400" tabIndex={-1}>
                        <FuzzyDate value={incident.date} fallback="Unknown date" />
                      </Link>
                    </td>
                    <td className="p-0">
                      <Link to="/incidents/$id" params={{ id: incident.id }} className="block px-4 py-3" tabIndex={-1}>
                        {incident.verified
                          ? <Badge className="bg-emerald-900 text-emerald-300 border-transparent">Verified</Badge>
                          : <Badge variant="outline" className="text-zinc-500">Unverified</Badge>}
                      </Link>
                    </td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-12 text-center text-sm text-zinc-500">No incidents found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {data?.next_cursor && (
        <div className="mt-4 flex justify-end">
          <Button variant="outline" size="sm" onClick={() => setCursor(data.next_cursor ?? undefined)}>Load more</Button>
        </div>
      )}

      <IncidentFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
