import { createFileRoute, Link, useLocation, useNavigate } from '@tanstack/react-router'
import { Bookmark, BookmarkPlus, CheckCircle2, Download, Pencil, Plus, Search, ShieldAlert, Skull, Swords, Trash2, User, X } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { toast } from 'sonner'
import { FuzzyDate } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
  DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { UrlPasteBanner, useUrlPasteBanner } from '@/components/UrlPasteBanner'
import { SourceFormSheet } from './_app.sources.index'

const IncidentHeatmap = lazy(() =>
  import('@/components/charts/IncidentHeatmap').then((m) => ({ default: m.IncidentHeatmap })),
)
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import {
  useCreateIncident, useUpdateIncident, useIncident,
  useIncidents, useIncidentsByMunicipality, useMemberIncidents, useMemberSearch,
  useMunicipalities, useAllMembers, useSets, useDeleteIncident,
} from '@/lib/queries'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { downloadCsv } from '@/lib/download'
import { api } from '@/lib/api'
import { useDebounce } from '@/hooks/useDebounce'
import { EmptyState } from '@/components/EmptyState'
import { TableRowSkeleton } from '@/components/skeletons'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { IncidentListItem, IncidentReadDetail, IncidentType, MemberListItem, ParticipantOutcome, ParticipantRole, UUID } from '@/lib/types'
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

function ParticipantBuilder({ universeId, participants, onChange, onDeathDateNeeded, allMembers, setNameById }: {
  universeId: string
  participants: ParticipantDraft[]
  onChange: (p: ParticipantDraft[]) => void
  onDeathDateNeeded?: (prompt: DeathDatePrompt) => void
  allMembers: MemberListItem[]
  setNameById: Record<string, string>
}) {
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<ParticipantRole>('VICTIM')
  const [outcome, setOutcome] = useState<ParticipantOutcome>('UNKNOWN')
  const debouncedSearch = useDebounce(search, 200)
  const { data: results } = useMemberSearch(universeId, debouncedSearch)

  // Suggest members from the same set(s) as already-added participants.
  const suggestions = useMemo(() => {
    if (participants.length === 0 || allMembers.length === 0) return [] as MemberListItem[]
    const memberMap = Object.fromEntries(allMembers.map((m) => [m.id, m]))
    const addedIds = new Set(participants.map((p) => p.member_id))
    const setIds = new Set<string>()
    for (const p of participants) {
      const sid = memberMap[p.member_id]?.set_id
      if (sid) setIds.add(sid)
    }
    if (setIds.size === 0) return []
    return allMembers
      .filter((m) => m.set_id && setIds.has(m.set_id) && !addedIds.has(m.id))
      .slice(0, 8)
  }, [allMembers, participants])

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
      {search.length < 2 && suggestions.length > 0 && (
        <div className="space-y-1">
          <div className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Suggested from same set
          </div>
          <div className="max-h-40 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
            {suggestions.map((m) => (
              <button key={m.id} type="button" onClick={() => addParticipant(m.id, m.display_name)}
                className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors flex items-center justify-between gap-2">
                <span className="truncate">{m.display_name}</span>
                {m.set_id && setNameById[m.set_id] && (
                  <span className="text-[10px] text-zinc-500 shrink-0 truncate max-w-[40%]">{setNameById[m.set_id]}</span>
                )}
              </button>
            ))}
          </div>
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
  defaultMunicipalityId?: string
}

export function IncidentFormSheet({ universeId, open, onClose, initial, defaultParticipants, defaultMunicipalityId }: IncidentFormProps) {
  const create = useCreateIncident()
  const update = useUpdateIncident(initial?.id ?? '', universeId)
  const isEdit = !!initial
  const { data: munis } = useMunicipalities(universeId)
  const { data: allMembersData } = useAllMembers(universeId)
  const { data: allSetsData } = useSets(universeId)

  const allMembersList = useMemo(() => allMembersData?.items ?? [], [allMembersData])
  const memberNameMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const m of allMembersList) map[m.id] = m.display_name
    return map
  }, [allMembersList])

  const setNameById = useMemo(() => {
    const map: Record<string, string> = {}
    for (const s of allSetsData?.items ?? []) map[s.id] = s.name
    return map
  }, [allSetsData])

  const [type, setType] = useState<IncidentType>(initial?.type ?? 'SHOOTING')
  const [date, setDate] = useState<FuzzyDateValue | null>(initial?.date ?? null)
  const [locationText, setLocationText] = useState(initial?.location_text ?? '')
  const [municipalityId, setMunicipalityId] = useState<string>(initial?.municipality_id ?? defaultMunicipalityId ?? '')
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
  const urlPaste = useUrlPasteBanner()
  const [creatingSourceFromUrl, setCreatingSourceFromUrl] = useState<string | null>(null)

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
              onDeathDateNeeded={!isEdit ? (p) => setDeathPrompts((prev) => [...prev, p]) : undefined}
              allMembers={allMembersList} setNameById={setNameById} />
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
            <Textarea
              id="inc-narrative"
              rows={4}
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
              onPaste={urlPaste.onPaste}
              placeholder="What happened…"
            />
            <UrlPasteBanner
              url={urlPaste.pastedUrl}
              onSaveAsSource={() => {
                if (urlPaste.pastedUrl) setCreatingSourceFromUrl(urlPaste.pastedUrl)
                urlPaste.dismiss()
              }}
              onDismiss={urlPaste.dismiss}
            />
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
      {creatingSourceFromUrl && (
        <SourceFormSheet
          universeId={universeId}
          open
          onClose={() => setCreatingSourceFromUrl(null)}
          defaultUrl={creatingSourceFromUrl}
        />
      )}
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

// ─── Filter presets ───────────────────────────────────────────────────────────

interface FilterPreset {
  name: string
  type: TypeFilter
  verified: VerifiedFilter
  participantId: UUID | null
  participantName: string | null
  municipalityId: UUID | null
  municipalityName: string | null
}

function presetsKey(universeId: string): string {
  return `incidents-presets-${universeId}`
}

function loadPresets(universeId: string): FilterPreset[] {
  try {
    const raw = localStorage.getItem(presetsKey(universeId))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persistPresets(universeId: string, presets: FilterPreset[]) {
  try {
    localStorage.setItem(presetsKey(universeId), JSON.stringify(presets))
  } catch {
    // Storage might be unavailable (private mode); silently no-op.
  }
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function IncidentsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const navigate = useNavigate()
  const location = useLocation()
  const municipalityIdFromUrl = useMemo(() => {
    const params = new URLSearchParams(location.searchStr ?? '')
    const v = params.get('municipality_id')
    return v ? (v as UUID) : null
  }, [location.searchStr])
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('ALL')
  const [verifiedFilter, setVerifiedFilter] = useState<VerifiedFilter>('ALL')
  const [participantId, setParticipantId] = useState<UUID | null>(null)
  const [participantName, setParticipantName] = useState<string | null>(null)
  const [participantSearch, setParticipantSearch] = useState('')
  const debouncedParticipantSearch = useDebounce(participantSearch, 200)

  // Participant filter wins over municipality filter when both are present.
  const municipalityId = !participantId && municipalityIdFromUrl ? municipalityIdFromUrl : null

  const baseQuery = useIncidents(participantId || municipalityId ? null : universe?.id ?? null, cursor)
  const participantQuery = useMemberIncidents(participantId, universe?.id ?? null)
  const muniQuery = useIncidentsByMunicipality(municipalityId, universe?.id ?? null)
  const data = participantId ? participantQuery.data : municipalityId ? muniQuery.data : baseQuery.data
  const isLoading = participantId
    ? participantQuery.isLoading
    : municipalityId
      ? muniQuery.isLoading
      : baseQuery.isLoading

  const { data: munis } = useMunicipalities(universe?.id ?? null)
  const { data: participantResults } = useMemberSearch(universe?.id ?? null, debouncedParticipantSearch)
  const municipalityName = municipalityId
    ? (munis?.items ?? []).find((m) => m.id === municipalityId)?.name ?? null
    : null

  function clearMunicipalityFilter() {
    navigate({ to: '/incidents' })
    setCursor(undefined)
  }

  // ── Bulk delete ───────────────────────────────────────────────────────────
  const [selected, setSelected] = useState<Set<UUID>>(new Set())
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const deleteIncident = useDeleteIncident(universe?.id ?? '')

  function toggleSelectIncident(id: UUID) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function bulkDeleteIncidents() {
    if (selected.size === 0) return
    const ids = Array.from(selected)
    setBulkDeleting(true)
    try {
      await Promise.all(ids.map((id) => deleteIncident.mutateAsync(id)))
      toast.success(`Deleted ${ids.length} incident${ids.length === 1 ? '' : 's'}`)
      setSelected(new Set())
      setConfirmingBulkDelete(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Bulk delete failed')
    } finally {
      setBulkDeleting(false)
    }
  }

  // ── Filter presets ────────────────────────────────────────────────────────
  const [presets, setPresets] = useState<FilterPreset[]>([])
  useEffect(() => {
    if (universe?.id) setPresets(loadPresets(universe.id))
  }, [universe?.id])

  const hasActiveFilter =
    typeFilter !== 'ALL' || verifiedFilter !== 'ALL' || !!participantId || !!municipalityId

  function applyPreset(p: FilterPreset) {
    setTypeFilter(p.type)
    setVerifiedFilter(p.verified)
    setParticipantId(p.participantId)
    setParticipantName(p.participantName)
    setParticipantSearch('')
    setCursor(undefined)
    if (p.municipalityId) {
      navigate({ to: '/incidents', search: { municipality_id: p.municipalityId } })
    } else if (municipalityIdFromUrl) {
      navigate({ to: '/incidents' })
    }
  }

  function saveCurrentAsPreset() {
    if (!universe?.id || !hasActiveFilter) return
    const name = window.prompt('Name this filter preset:')?.trim()
    if (!name) return
    const next: FilterPreset = {
      name,
      type: typeFilter,
      verified: verifiedFilter,
      participantId,
      participantName,
      municipalityId,
      municipalityName,
    }
    const updated = [...presets.filter((p) => p.name !== name), next]
    setPresets(updated)
    persistPresets(universe.id, updated)
  }

  function deletePreset(name: string) {
    if (!universe?.id) return
    const updated = presets.filter((p) => p.name !== name)
    setPresets(updated)
    persistPresets(universe.id, updated)
  }

  const allItems: IncidentListItem[] = data?.items ?? []

  function clearParticipantFilter() {
    setParticipantId(null)
    setParticipantName(null)
    setParticipantSearch('')
    setCursor(undefined)
  }

  function selectParticipant(id: UUID, name: string) {
    setParticipantId(id)
    setParticipantName(name)
    setParticipantSearch('')
    setCursor(undefined)
  }

  const items = useMemo(() => {
    let filtered = allItems
    if (typeFilter !== 'ALL') filtered = filtered.filter((i) => i.type === typeFilter)
    if (verifiedFilter === 'VERIFIED') filtered = filtered.filter((i) => i.verified)
    if (verifiedFilter === 'UNVERIFIED') filtered = filtered.filter((i) => !i.verified)
    return filtered
  }, [allItems, typeFilter, verifiedFilter])

  // Virtualize the table tbody when the list grows past 50 rows.
  const tableScrollRef = useRef<HTMLDivElement | null>(null)
  const isVirtualized = items.length > 50
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 56,
    overscan: 8,
  })
  const virtualRows = isVirtualized ? rowVirtualizer.getVirtualItems() : []
  const virtualPaddingTop = virtualRows[0]?.start ?? 0
  const virtualPaddingBottom = isVirtualized
    ? rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)
    : 0

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

      {/* Calendar density */}
      {allItems.length > 0 && (
        <div className="mb-4">
          <Suspense fallback={<div className="h-40 rounded-xl border border-zinc-800 bg-zinc-900/30" />}>
            <IncidentHeatmap incidents={allItems} />
          </Suspense>
        </div>
      )}

      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-8 gap-1.5">
              <Bookmark className="h-3.5 w-3.5" />
              Presets
              {presets.length > 0 && (
                <span className="ml-0.5 rounded-md bg-zinc-800 px-1.5 py-0 text-[10px] tabular-nums text-zinc-400">
                  {presets.length}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-64">
            {presets.length === 0 ? (
              <DropdownMenuLabel className="text-xs font-normal text-zinc-500">
                No saved presets yet.
              </DropdownMenuLabel>
            ) : (
              <>
                <DropdownMenuLabel className="text-[10px] uppercase tracking-wider text-zinc-500">
                  Saved
                </DropdownMenuLabel>
                {presets.map((p) => (
                  <div key={p.name} className="flex items-center gap-1 px-1">
                    <button
                      type="button"
                      onClick={() => applyPreset(p)}
                      className="flex-1 truncate rounded px-2 py-1.5 text-left text-sm text-zinc-200 hover:bg-zinc-800"
                    >
                      {p.name}
                    </button>
                    <button
                      type="button"
                      onClick={() => deletePreset(p.name)}
                      aria-label={`Delete preset ${p.name}`}
                      className="rounded p-1 text-zinc-600 hover:bg-zinc-800 hover:text-red-400"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
                <DropdownMenuSeparator />
              </>
            )}
            <DropdownMenuItem
              disabled={!hasActiveFilter}
              onSelect={saveCurrentAsPreset}
              className="gap-2 text-sm"
            >
              <BookmarkPlus className="h-3.5 w-3.5" />
              {hasActiveFilter ? 'Save current as preset…' : 'Set a filter to save'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
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
        {municipalityId && (
          <button
            type="button"
            onClick={clearMunicipalityFilter}
            className="inline-flex items-center gap-1.5 rounded-md border border-violet-700/60 bg-violet-950/40 px-2.5 py-1 text-xs font-medium text-violet-300 hover:bg-violet-900/40 transition-colors"
          >
            <span>Zone: {municipalityName ?? 'unknown'}</span>
            <X className="h-3 w-3" />
          </button>
        )}
        {participantId ? (
          <button
            type="button"
            onClick={clearParticipantFilter}
            className="inline-flex items-center gap-1.5 rounded-md border border-violet-700/60 bg-violet-950/40 px-2.5 py-1 text-xs font-medium text-violet-300 hover:bg-violet-900/40 transition-colors"
          >
            <User className="h-3 w-3" />
            <span>Participant: {participantName}</span>
            <X className="h-3 w-3" />
          </button>
        ) : (
          <div className="relative min-w-[220px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
            <Input
              className="pl-8 h-8 text-sm"
              placeholder="Filter by participant…"
              value={participantSearch}
              onChange={(e) => setParticipantSearch(e.target.value)}
            />
            {debouncedParticipantSearch.length >= 2 && participantResults && (
              <div className="absolute z-20 mt-1 w-full max-h-48 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950 shadow-lg">
                {participantResults.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-zinc-500">No matching members.</div>
                ) : (
                  participantResults.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => selectParticipant(m.id, m.display_name)}
                      className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
                    >
                      {m.display_name}
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      <div
        ref={tableScrollRef}
        className="rounded-lg border border-zinc-800"
        style={isVirtualized
          ? { maxHeight: 'calc(100vh - 22rem)', overflowY: 'auto' }
          : { overflow: 'hidden' }}
      >
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-zinc-900/90 backdrop-blur">
            <tr className="border-b border-zinc-800">
              <th className="w-10 px-3 py-2.5" scope="col">
                <input
                  type="checkbox"
                  aria-label="Select all incidents"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={() => setSelected(selected.size === items.length ? new Set() : new Set(items.map((i) => i.id)))}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
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
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={7} height={56} />)
              : isVirtualized && virtualPaddingTop > 0
                ? <tr aria-hidden><td colSpan={7} style={{ height: virtualPaddingTop }} /></tr>
                : null}
            {!isLoading && (isVirtualized ? virtualRows.map((vRow) => items[vRow.index]) : items).map((incident, idx) => {
                  const cfg = TYPE_CONFIG[incident.type]
                  const Icon = cfg?.icon ?? ShieldAlert
                  const muniName = incident.municipality_id ? muniMap[incident.municipality_id] : null
                  const isSelected = selected.has(incident.id)
                  const measureRef = isVirtualized ? rowVirtualizer.measureElement : undefined
                  const dataIndex = isVirtualized ? virtualRows[idx]?.index : undefined
                  return (
                    <tr key={incident.id} ref={measureRef} data-index={dataIndex} className={`group hover:bg-zinc-900/50 transition-colors ${isSelected ? 'bg-violet-950/20' : ''}`}>
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          aria-label={`Select ${incident.type} incident`}
                          checked={isSelected}
                          onChange={() => toggleSelectIncident(incident.id)}
                          className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                        />
                      </td>
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
            {!isLoading && isVirtualized && virtualPaddingBottom > 0 && (
              <tr aria-hidden><td colSpan={7} style={{ height: virtualPaddingBottom }} /></tr>
            )}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={7}>
                  <EmptyState
                    icon={ShieldAlert}
                    title={
                      typeFilter !== 'ALL' || verifiedFilter !== 'ALL' || participantId || municipalityId
                        ? 'No incidents match the current filters'
                        : 'No incidents recorded yet'
                    }
                    description={typeFilter === 'ALL' && verifiedFilter === 'ALL' && !participantId && !municipalityId ? 'Record a shooting or murder to begin tracking.' : undefined}
                    action={
                      typeFilter === 'ALL' && verifiedFilter === 'ALL' && !participantId && !municipalityId ? (
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
      {!participantId && !municipalityId && data?.next_cursor && (
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

      <BulkActionBar count={selected.size} label="incident" onClear={() => setSelected(new Set())}>
        <Button
          size="sm"
          variant="destructive"
          className="h-7 text-xs"
          onClick={() => setConfirmingBulkDelete(true)}
          disabled={bulkDeleting}
        >
          <Trash2 className="mr-1 h-3 w-3" />
          Delete
        </Button>
      </BulkActionBar>

      <ConfirmDialog
        open={confirmingBulkDelete}
        title={`Delete ${selected.size} incident${selected.size === 1 ? '' : 's'}?`}
        description="This cannot be undone. Participants will lose these incidents from their timeline."
        confirmLabel="Delete"
        destructive
        pending={bulkDeleting}
        onConfirm={bulkDeleteIncidents}
        onCancel={() => setConfirmingBulkDelete(false)}
      />
    </div>
  )
}
