import { createFileRoute, Link } from '@tanstack/react-router'
import { CheckCircle2, Download, Pencil, Plus, ShieldAlert, Skull, Swords } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
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
import {
  useCreateIncident, useUpdateIncident, useIncident,
  useIncidents, useMemberSearch, useMunicipalities, useAllMembers,
} from '@/lib/queries'
import { downloadCsv } from '@/lib/download'
import { api } from '@/lib/api'
import { useDebounce } from '@/hooks/useDebounce'
import { EmptyState } from '@/components/EmptyState'
import { TableRowSkeleton } from '@/components/skeletons'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { IncidentListItem, IncidentReadDetail, IncidentType, ParticipantOutcome, ParticipantRole, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/incidents/')({
  component: IncidentsPage,
})

// ─── Type config ──────────────────────────────────────────────────────────────

const TYPE_CONFIG: Record<IncidentType, { icon: typeof ShieldAlert; color: string; dot: string; label: string }> = {
  SHOOTING: { icon: Swords,     color: 'text-amber-400',  dot: 'bg-amber-500',  label: 'Shooting' },
  MURDER:   { icon: Skull,      color: 'text-rose-400',   dot: 'bg-rose-500',   label: 'Murder'   },
}

function TypeChip({ type }: { type: IncidentType }) {
  const cfg = TYPE_CONFIG[type] ?? { icon: ShieldAlert, color: 'text-zinc-400', dot: 'bg-zinc-500', label: type }
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${cfg.color}`}>
      <Icon className="h-3.5 w-3.5 shrink-0" />
      {cfg.label}
    </span>
  )
}

// ─── Participant builder ──────────────────────────────────────────────────────

export interface ParticipantDraft {
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
  const debouncedSearch = useDebounce(search, 200)
  const { data: results } = useMemberSearch(universeId, debouncedSearch)

  function addParticipant(memberId: UUID, memberName: string) {
    if (participants.some((p) => p.member_id === memberId)) return
    onChange([...participants, { member_id: memberId, member_name: memberName, role, outcome }])
    setSearch('')
    if (role === 'VICTIM' && outcome === 'KILLED' && onDeathDateNeeded)
      onDeathDateNeeded({ memberId, memberName, date: null })
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
      <Input placeholder="Search member to add…" value={search} onChange={(e) => setSearch(e.target.value)} />
      {results && results.length > 0 && search.length >= 2 && (
        <div className="max-h-32 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
          {results.map((m) => (
            <button key={m.id} type="button" onClick={() => addParticipant(m.id, m.display_name)}
              className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors">
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
                <button type="button" onClick={() => onChange(participants.filter((x) => x.member_id !== p.member_id))}
                  className="text-zinc-600 hover:text-red-400 transition-colors text-xs">✕</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Incident form sheet ──────────────────────────────────────────────────────

interface IncidentFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: IncidentReadDetail
  defaultParticipants?: ParticipantDraft[]
}

export function IncidentFormSheet({ universeId, open, onClose, initial, defaultParticipants }: IncidentFormProps) {
  const create = useCreateIncident()
  const update = useUpdateIncident(initial?.id ?? '', universeId)
  const isEdit = !!initial
  const { data: munis } = useMunicipalities(universeId)
  const { data: allMembersData } = useAllMembers(isEdit ? universeId : null)

  const memberNameMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const m of allMembersData?.items ?? []) map[m.id] = m.display_name
    return map
  }, [allMembersData])

  const [type, setType] = useState<IncidentType>(initial?.type ?? 'SHOOTING')
  const [date, setDate] = useState<FuzzyDateValue | null>(initial?.date ?? null)
  const [locationText, setLocationText] = useState(initial?.location_text ?? '')
  const [municipalityId, setMunicipalityId] = useState<string>(initial?.municipality_id ?? '')
  const [narrative, setNarrative] = useState(initial?.narrative ?? '')
  const [verified, setVerified] = useState(initial?.verified ?? false)
  const [participants, setParticipants] = useState<ParticipantDraft[]>(() =>
    initial?.participants?.map((p) => ({
      member_id: p.member_id,
      member_name: memberNameMap[p.member_id] ?? p.member_id,
      role: p.role,
      outcome: p.outcome,
    })) ?? defaultParticipants ?? []
  )
  const [deathPrompts, setDeathPrompts] = useState<DeathDatePrompt[]>([])
  const [error, setError] = useState<string | null>(null)

  // Re-resolve participant names once member map loads (edit mode only)
  useEffect(() => {
    if (!isEdit || Object.keys(memberNameMap).length === 0) return
    setParticipants((prev) =>
      prev.map((p) => ({
        ...p,
        member_name: memberNameMap[p.member_id] ?? p.member_name,
      }))
    )
  // Only re-run when the name map finishes loading
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [memberNameMap])

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      const body: Record<string, unknown> = {
        universe_id: universeId,
        type, date,
        location_text: locationText || null,
        municipality_id: municipalityId || null,
        narrative: narrative || null,
        verified,
        participants: participants.map(({ member_id, role, outcome }) => ({ member_id, role, outcome })),
      }
      if (isEdit) {
        await update.mutateAsync(body)
        toast.success(`Updated ${type.toLowerCase()} incident`)
      } else {
        await create.mutateAsync(body)
        // Apply death dates for KILLED participants
        for (const prompt of deathPrompts) {
          if (prompt.date) {
            await api.patch(`/members/${prompt.memberId}?universe_id=${universeId}`, { date_of_death: prompt.date })
          }
        }
        toast.success(`Recorded ${type.toLowerCase()} incident`)
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
      <SheetContent title={isEdit ? 'Edit Incident' : 'Add Incident'} description={isEdit ? 'Update this incident' : 'Record a new incident'}>
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
            <input id="inc-verified" type="checkbox" checked={verified} onChange={(e) => setVerified(e.target.checked)}
              className="rounded border-zinc-700 bg-zinc-900 accent-violet-600" />
            <label htmlFor="inc-verified" className="text-sm text-zinc-300">Verified</label>
          </div>
          <div className="space-y-1.5">
            <Label>Participants</Label>
            <ParticipantBuilder universeId={universeId} participants={participants} onChange={setParticipants}
              onDeathDateNeeded={!isEdit ? (p) => setDeathPrompts((prev) => [...prev, p]) : undefined} />
          </div>
          {deathPrompts.length > 0 && (
            <div className="space-y-3 rounded-lg border border-amber-800 bg-amber-950/30 p-3">
              <p className="text-xs font-semibold text-amber-400">Killed participant(s) — set date of death?</p>
              {deathPrompts.map((prompt) => (
                <div key={prompt.memberId}>
                  <p className="mb-1 text-xs text-zinc-300">{prompt.memberName}</p>
                  <FuzzyDateInput value={prompt.date}
                    onChange={(v) => setDeathPrompts((prev) => prev.map((p) => p.memberId === prompt.memberId ? { ...p, date: v } : p))}
                    idPrefix={`dod-${prompt.memberId}`} />
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

// ─── Lazy edit sheet ──────────────────────────────────────────────────────────

function EditIncidentSheet({ incidentId, universeId, open, onClose }: {
  incidentId: string; universeId: string; open: boolean; onClose: () => void
}) {
  const { data: incident } = useIncident(incidentId, universeId)
  if (!incident) {
    return (
      <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
        <SheetContent title="Edit Incident" description="Loading…">
          <div className="space-y-3 pt-2">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        </SheetContent>
      </Sheet>
    )
  }
  return <IncidentFormSheet universeId={universeId} open={open} onClose={onClose} initial={incident} />
}

// ─── Filter bar ───────────────────────────────────────────────────────────────

type TypeFilter = 'ALL' | IncidentType
type VerifiedFilter = 'ALL' | 'VERIFIED' | 'UNVERIFIED'

function FilterTabs<T extends string>({ options, value, onChange }: {
  options: { key: T; label: string; count?: number }[]
  value: T
  onChange: (v: T) => void
}) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1">
      {options.map(({ key, label, count }) => (
        <button key={key} onClick={() => onChange(key)}
          className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
            value === key ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'
          }`}>
          {label}
          {count !== undefined && (
            <span className={`tabular-nums ${value === key ? 'text-zinc-300' : 'text-zinc-600'}`}>{count}</span>
          )}
        </button>
      ))}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function IncidentsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('ALL')
  const [verifiedFilter, setVerifiedFilter] = useState<VerifiedFilter>('ALL')

  const { data, isLoading } = useIncidents(universe?.id ?? null, cursor)
  const { data: munis } = useMunicipalities(universe?.id ?? null)

  const allItems: IncidentListItem[] = data?.items ?? []

  const items = useMemo(() => {
    let filtered = allItems
    if (typeFilter !== 'ALL') filtered = filtered.filter((i) => i.type === typeFilter)
    if (verifiedFilter === 'VERIFIED') filtered = filtered.filter((i) => i.verified)
    if (verifiedFilter === 'UNVERIFIED') filtered = filtered.filter((i) => !i.verified)
    return filtered
  }, [allItems, typeFilter, verifiedFilter])

  if (!universe) return <NoUniverse />

  const muniMap: Record<string, string> = {}
  for (const m of munis?.items ?? []) muniMap[m.id] = m.name

  const shootingCount = allItems.filter((i) => i.type === 'SHOOTING').length
  const murderCount = allItems.filter((i) => i.type === 'MURDER').length
  const verifiedCount = allItems.filter((i) => i.verified).length

  const headerDesc = isLoading ? undefined
    : allItems.length === 0 ? 'No incidents yet'
    : [
        shootingCount > 0 && `${shootingCount} shooting${shootingCount !== 1 ? 's' : ''}`,
        murderCount > 0 && `${murderCount} murder${murderCount !== 1 ? 's' : ''}`,
        verifiedCount > 0 && `${verifiedCount} verified`,
      ].filter(Boolean).join(' · ')

  return (
    <div>
      <PageHeader
        title="Incidents"
        description={headerDesc || undefined}
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm"
              onClick={() => {
                const date = new Date().toISOString().slice(0, 10)
                downloadCsv(`/incidents/?universe_id=${universe.id}&format=csv`, `incidents-${universe.slug}-${date}.csv`)
              }}>
              <Download className="mr-1.5 h-3.5 w-3.5" />Export
            </Button>
            <Button size="sm" onClick={() => setCreating(true)}>
              <Plus className="mr-1.5 h-4 w-4" />Add Incident
            </Button>
          </div>
        }
      />

      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <FilterTabs<TypeFilter>
          value={typeFilter}
          onChange={setTypeFilter}
          options={[
            { key: 'ALL', label: 'All', count: allItems.length },
            { key: 'SHOOTING', label: 'Shootings', count: shootingCount },
            { key: 'MURDER', label: 'Murders', count: murderCount },
          ]}
        />
        <FilterTabs<VerifiedFilter>
          value={verifiedFilter}
          onChange={setVerifiedFilter}
          options={[
            { key: 'ALL', label: 'All' },
            { key: 'VERIFIED', label: 'Verified' },
            { key: 'UNVERIFIED', label: 'Unverified' },
          ]}
        />
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-zinc-900/90 backdrop-blur">
            <tr className="border-b border-zinc-800">
              <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400" scope="col">Type</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400" scope="col">Date</th>
              <th className="hidden px-4 py-2.5 text-left text-xs font-medium text-zinc-400 md:table-cell" scope="col">Location</th>
              <th className="hidden px-4 py-2.5 text-left text-xs font-medium text-zinc-400 lg:table-cell" scope="col">Victims</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400" scope="col">Status</th>
              <th className="w-8" scope="col" aria-label="Actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={6} height={56} />)
              : items.map((incident) => {
                  const cfg = TYPE_CONFIG[incident.type]
                  const Icon = cfg?.icon ?? ShieldAlert
                  const muniName = incident.municipality_id ? muniMap[incident.municipality_id] : null
                  return (
                    <tr key={incident.id} className="group hover:bg-zinc-900/50 transition-colors">
                      {/* Type */}
                      <td className="p-0">
                        <Link to="/incidents/$id" params={{ id: incident.id }}
                          className="flex items-center gap-3 px-4 py-3">
                          <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${
                            incident.type === 'MURDER'
                              ? 'bg-rose-950/60 text-rose-400'
                              : 'bg-amber-950/60 text-amber-400'
                          }`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <TypeChip type={incident.type} />
                        </Link>
                      </td>

                      {/* Date */}
                      <td className="p-0">
                        <Link to="/incidents/$id" params={{ id: incident.id }}
                          className="block px-4 py-3 font-mono text-xs text-zinc-400 tabular-nums" tabIndex={-1}>
                          {incident.date
                            ? <FuzzyDate value={incident.date} />
                            : <span className="text-zinc-700">Unknown date</span>}
                        </Link>
                      </td>

                      {/* Location */}
                      <td className="hidden p-0 md:table-cell">
                        <Link to="/incidents/$id" params={{ id: incident.id }}
                          className="block px-4 py-3 text-xs text-zinc-500" tabIndex={-1}>
                          {muniName ?? <span className="text-zinc-700">—</span>}
                        </Link>
                      </td>

                      {/* Victims */}
                      <td className="hidden p-0 lg:table-cell">
                        <Link to="/incidents/$id" params={{ id: incident.id }}
                          className="block px-4 py-3 text-xs text-zinc-400" tabIndex={-1}>
                          {incident.victim_names.length > 0 ? (
                            <span className="truncate max-w-xs inline-block align-bottom">
                              {incident.victim_names.slice(0, 3).join(', ')}
                              {incident.victim_names.length > 3 && ` +${incident.victim_names.length - 3}`}
                            </span>
                          ) : (
                            <span className="text-zinc-700">—</span>
                          )}
                        </Link>
                      </td>

                      {/* Verified */}
                      <td className="px-4 py-3">
                        {incident.verified ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Verified
                          </span>
                        ) : (
                          <span className="text-xs text-zinc-600">Unverified</span>
                        )}
                      </td>

                      {/* Quick edit */}
                      <td className="pr-3 py-3">
                        <button
                          onClick={() => setEditingId(incident.id)}
                          aria-label="Edit incident"
                          className="rounded p-1.5 text-zinc-600 hover:bg-zinc-800 hover:text-zinc-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <EmptyState
                    icon={ShieldAlert}
                    title={
                      typeFilter !== 'ALL' || verifiedFilter !== 'ALL'
                        ? 'No incidents match the current filters'
                        : 'No incidents recorded yet'
                    }
                    description={typeFilter === 'ALL' && verifiedFilter === 'ALL' ? 'Record a shooting or murder to begin tracking.' : undefined}
                    action={
                      typeFilter === 'ALL' && verifiedFilter === 'ALL' ? (
                        <Button size="sm" onClick={() => setCreating(true)}>
                          <Plus className="mr-1.5 h-4 w-4" /> Record the first incident
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

      {/* Load more */}
      {data?.next_cursor && (
        <div className="mt-4 flex justify-center">
          <Button variant="outline" size="sm" onClick={() => setCursor(data.next_cursor ?? undefined)}>
            Load more incidents
          </Button>
        </div>
      )}

      <IncidentFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingId && (
        <EditIncidentSheet
          incidentId={editingId}
          universeId={universe.id}
          open={!!editingId}
          onClose={() => setEditingId(null)}
        />
      )}
    </div>
  )
}
