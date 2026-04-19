import { createFileRoute, Link } from '@tanstack/react-router'
import { Plus, ShieldAlert } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
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
import { useCreateIncident, useIncidents, useMemberSearch } from '@/lib/queries'
import type { IncidentType, ParticipantOutcome, ParticipantRole, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/incidents')({
  component: IncidentsPage,
})

interface ParticipantDraft {
  member_id: UUID
  member_name: string
  role: ParticipantRole
  outcome: ParticipantOutcome
}

function ParticipantBuilder({ universeId, participants, onChange }: {
  universeId: string
  participants: ParticipantDraft[]
  onChange: (p: ParticipantDraft[]) => void
}) {
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<ParticipantRole>('VICTIM')
  const [outcome, setOutcome] = useState<ParticipantOutcome>('UNKNOWN')
  const { data: results } = useMemberSearch(universeId, search)

  function addParticipant(memberId: UUID, memberName: string) {
    if (participants.some((p) => p.member_id === memberId)) return
    onChange([...participants, { member_id: memberId, member_name: memberName, role, outcome }])
    setSearch('')
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

function CreateIncidentSheet({ universeId, open, onClose }: { universeId: string; open: boolean; onClose: () => void }) {
  const create = useCreateIncident()
  const [type, setType] = useState<IncidentType>('SHOOTING')
  const [year, setYear] = useState('')
  const [locationText, setLocationText] = useState('')
  const [narrative, setNarrative] = useState('')
  const [participants, setParticipants] = useState<ParticipantDraft[]>([])
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      const date = year ? { year: parseInt(year), precision: 'Y' as const, approx: false } : null
      await create.mutateAsync({
        universe_id: universeId,
        type,
        date,
        location_text: locationText || null,
        narrative: narrative || null,
        participants: participants.map(({ member_id, role, outcome }) => ({ member_id, role, outcome })),
      })
      setType('SHOOTING'); setYear(''); setLocationText(''); setNarrative(''); setParticipants([])
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create incident')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title="Add Incident" description="Record a new incident">
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
          <div className="space-y-1.5">
            <Label htmlFor="inc-year">Year</Label>
            <Input id="inc-year" type="number" min="1900" max="2099" value={year} onChange={(e) => setYear(e.target.value)} placeholder="e.g. 2023" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="inc-loc">Location</Label>
            <Input id="inc-loc" value={locationText} onChange={(e) => setLocationText(e.target.value)} placeholder="Street address or area" />
          </div>
          <div className="space-y-1.5">
            <Label>Participants</Label>
            <ParticipantBuilder universeId={universeId} participants={participants} onChange={setParticipants} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="inc-narrative">Narrative</Label>
            <Textarea id="inc-narrative" value={narrative} onChange={(e) => setNarrative(e.target.value)} placeholder="What happened…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={create.isPending} className="flex-1">
              {create.isPending ? 'Saving…' : 'Create Incident'}
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
                    <td className="px-4 py-3">
                      <Link to="/incidents/$id" params={{ id: incident.id }} className="flex items-center gap-2 text-white hover:text-violet-400 transition-colors">
                        <ShieldAlert className="h-3.5 w-3.5 text-zinc-500" />
                        {incident.type}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-zinc-400">
                      <FuzzyDate value={incident.date} fallback="Unknown date" />
                    </td>
                    <td className="px-4 py-3">
                      {incident.verified
                        ? <Badge className="bg-emerald-900 text-emerald-300 border-transparent">Verified</Badge>
                        : <Badge variant="outline" className="text-zinc-500">Unverified</Badge>}
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

      <CreateIncidentSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
