import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Banknote, Bomb, Bookmark, BookmarkPlus, CarFront, CheckCircle2, Download, Flame, HandCoins, Pencil, Plus, Search, ShieldAlert, Skull, Swords, Trash2, User, UserX, X } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
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
import { SourceFormSheet } from './_app.$universe.sources.index'

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
  useAllIncidents, useIncidentsByMunicipality, useMember, useMemberIncidents, useMemberSearch,
  useMunicipalities, useAllMembers, useAllSets, useDeleteIncident,
} from '@/lib/queries'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { downloadCsv } from '@/lib/download'
import { currentAffiliations, primaryAffiliation } from '@/lib/utils'
import { useDebounce } from '@/hooks/useDebounce'
import { EmptyState } from '@/components/EmptyState'
import { TableRowSkeleton } from '@/components/skeletons'
import { textParam } from '@/lib/searchParams'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { IncidentListItem, IncidentReadDetail, IncidentType, MemberListItem, ParticipantOutcome, ParticipantRole, SetListItem, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'

type SortKey = 'date' | 'added'

interface IncidentsSearch {
  q?: string
  type?: IncidentType
  verified?: 'yes' | 'no'
  member?: string
  municipality_id?: string
  sort?: SortKey
  order?: 'asc' | 'desc'
}

export const Route = createFileRoute('/_app/$universe/incidents/')({
  validateSearch: (s: Record<string, unknown>): IncidentsSearch => ({
    q: textParam(s.q),
    type: typeof s.type === 'string' && s.type in TYPE_CONFIG ? (s.type as IncidentType) : undefined,
    verified: s.verified === 'yes' || s.verified === 'no' ? s.verified : undefined,
    member: typeof s.member === 'string' && s.member ? s.member : undefined,
    municipality_id: typeof s.municipality_id === 'string' && s.municipality_id ? s.municipality_id : undefined,
    sort: s.sort === 'added' ? 'added' : s.sort === 'date' ? 'date' : undefined,
    order: s.order === 'asc' ? 'asc' : s.order === 'desc' ? 'desc' : undefined,
  }),
  component: IncidentsPage,
})

// ─── Type config ──────────────────────────────────────────────────────────────

// `tile` is spelled out rather than derived from `color` because Tailwind v4
// only emits classes it can find as literals in the source.
const TYPE_CONFIG: Record<IncidentType, { icon: typeof ShieldAlert; color: string; dot: string; tile: string; label: string }> = {
  SHOOTING:   { icon: Swords,      color: 'text-amber-400',  dot: 'bg-amber-500',  tile: 'bg-amber-950/60 text-amber-400',   label: 'Shooting'   },
  MURDER:     { icon: Skull,       color: 'text-rose-400',   dot: 'bg-rose-500',   tile: 'bg-rose-950/60 text-rose-400',     label: 'Murder'     },
  FIGHT:      { icon: ShieldAlert, color: 'text-violet-400', dot: 'bg-violet-500', tile: 'bg-violet-950/60 text-violet-400', label: 'Fight'      },
  BOMBING:    { icon: Bomb,        color: 'text-yellow-400', dot: 'bg-yellow-500', tile: 'bg-yellow-950/60 text-yellow-400', label: 'Bombing'    },
  ARSON:      { icon: Flame,       color: 'text-pink-400',   dot: 'bg-pink-500',   tile: 'bg-pink-950/60 text-pink-400',     label: 'Arson'      },
  EXTORTION:  { icon: HandCoins,   color: 'text-teal-400',   dot: 'bg-teal-500',   tile: 'bg-teal-950/60 text-teal-400',     label: 'Extortion'  },
  KIDNAPPING: { icon: UserX,       color: 'text-blue-400',   dot: 'bg-blue-500',   tile: 'bg-blue-950/60 text-blue-400',     label: 'Kidnapping' },
  ROBBERY:    { icon: Banknote,    color: 'text-emerald-400',dot: 'bg-emerald-500',tile: 'bg-emerald-950/60 text-emerald-400', label: 'Robbery'  },
  CRASH:      { icon: CarFront,    color: 'text-sky-400',    dot: 'bg-sky-500',    tile: 'bg-sky-950/60 text-sky-400',       label: 'Crash'    },
}

const TYPE_ORDER = Object.keys(TYPE_CONFIG) as IncidentType[]

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

// ─── Participant types ────────────────────────────────────────────────────────

export interface ParticipantDraft {
  member_id: UUID
  member_name: string
  role: ParticipantRole
  outcome: ParticipantOutcome
  /** A court cleared them of this role. Excluded from kill/shooting counts. */
  acquitted: boolean
}

export interface SetParticipantDraft {
  set_id: UUID
  set_name: string
  role: ParticipantRole
  outcome: ParticipantOutcome
}

// ─── Unified participants section ─────────────────────────────────────────────

const ROLES: ParticipantRole[] = ['SHOOTER', 'ASSISTED', 'BYSTANDER', 'VICTIM']

/** Only an offender role is something a court can clear someone of. */
function isOffenderRole(r: ParticipantRole) {
  return r === 'SHOOTER' || r === 'ASSISTED'
}
const OUTCOMES: ParticipantOutcome[] = ['KILLED', 'INJURED', 'UNHARMED', 'UNKNOWN']

function ParticipantsSection({ universeId, participants, onChangeParticipants, setParticipants, onChangeSetParticipants, allMembers, allSets }: {
  universeId: string
  participants: ParticipantDraft[]
  onChangeParticipants: (p: ParticipantDraft[]) => void
  setParticipants: SetParticipantDraft[]
  onChangeSetParticipants: (p: SetParticipantDraft[]) => void
  allMembers: MemberListItem[]
  allSets: SetListItem[]
}) {
  const [mode, setMode] = useState<'member' | 'set'>('member')

  // Member add state
  const [memberSearch, setMemberSearch] = useState('')
  const [memberRole, setMemberRole] = useState<ParticipantRole>('VICTIM')
  const [memberOutcome, setMemberOutcome] = useState<ParticipantOutcome>('UNKNOWN')
  const [memberAcquitted, setMemberAcquitted] = useState(false)
  const debouncedMemberSearch = useDebounce(memberSearch, 200)
  const { data: memberResults } = useMemberSearch(universeId, debouncedMemberSearch)

  // Set add state
  const [setSearch, setSetSearch] = useState('')
  const [setRole, setSetRole] = useState<ParticipantRole>('SHOOTER')
  const [setOutcome, setSetOutcome] = useState<ParticipantOutcome>('UNKNOWN')

  // Memoised: a fresh Set every render made both memos below recompute on every keystroke.
  const addedMemberIds = useMemo(() => new Set(participants.map((p) => p.member_id)), [participants])
  const addedSetIds = useMemo(() => new Set(setParticipants.map((p) => p.set_id)), [setParticipants])

  const memberSetNameById = useMemo(() => {
    const out: Record<string, string> = {}
    for (const m of allMembers) {
      const primary = primaryAffiliation(m.affiliations)
      if (primary?.set_name) out[m.id] = primary.set_name
    }
    return out
  }, [allMembers])

  const suggestions = useMemo(() => {
    if (participants.length === 0 || allMembers.length === 0) return [] as MemberListItem[]
    const memberMap = Object.fromEntries(allMembers.map((m) => [m.id, m]))
    const setIds = new Set<string>()
    for (const p of participants) {
      for (const aff of currentAffiliations(memberMap[p.member_id]?.affiliations)) setIds.add(aff.set_id)
    }
    if (setIds.size === 0) return []
    return allMembers.filter((m) => currentAffiliations(m.affiliations).some((a) => setIds.has(a.set_id)) && !addedMemberIds.has(m.id)).slice(0, 8)
  }, [allMembers, participants, addedMemberIds])

  const filteredSets = useMemo(() => {
    const q = setSearch.toLowerCase()
    const available = allSets.filter((s) => !addedSetIds.has(s.id))
    if (q.length >= 1) {
      return available
        .filter((s) => s.name.toLowerCase().includes(q))
        .sort((a, b) => (a.is_reserved === b.is_reserved ? 0 : a.is_reserved ? -1 : 1))
        .slice(0, 8)
    }
    // No search — show reserved sets pinned so they're always one click away
    return available.filter((s) => s.is_reserved)
  }, [allSets, setSearch, addedSetIds])

  function addMember(id: UUID, name: string) {
    if (addedMemberIds.has(id)) return
    onChangeParticipants([
      ...participants,
      {
        member_id: id,
        member_name: name,
        role: memberRole,
        outcome: memberOutcome,
        acquitted: isOffenderRole(memberRole) && memberAcquitted,
      },
    ])
    setMemberSearch('')
  }

  function addSet(s: SetListItem) {
    if (addedSetIds.has(s.id)) return
    onChangeSetParticipants([...setParticipants, { set_id: s.id, set_name: s.name, role: setRole, outcome: setOutcome }])
    setSetSearch('')
  }

  const total = participants.length + setParticipants.length

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Participants{total > 0 && <span className="ml-1.5 text-zinc-400">({total})</span>}
        </span>
        <div className="flex rounded border border-zinc-700 overflow-hidden text-xs">
          <button type="button"
            onClick={() => setMode('member')}
            className={`px-2.5 py-1 transition-colors ${mode === 'member' ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:bg-zinc-800'}`}>
            Member
          </button>
          <button type="button"
            onClick={() => setMode('set')}
            className={`px-2.5 py-1 transition-colors ${mode === 'set' ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:bg-zinc-800'}`}>
            Set
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Select value={mode === 'member' ? memberRole : setRole} onValueChange={(v) => mode === 'member' ? setMemberRole(v as ParticipantRole) : setSetRole(v as ParticipantRole)}>
          <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Role" /></SelectTrigger>
          <SelectContent>
            {ROLES.map((r) => <SelectItem key={r} value={r} className="text-xs">{r}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={mode === 'member' ? memberOutcome : setOutcome} onValueChange={(v) => mode === 'member' ? setMemberOutcome(v as ParticipantOutcome) : setSetOutcome(v as ParticipantOutcome)}>
          <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Outcome" /></SelectTrigger>
          <SelectContent>
            {OUTCOMES.map((o) => <SelectItem key={o} value={o} className="text-xs">{o}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {mode === 'member' && isOffenderRole(memberRole) && (
        <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-400">
          <input
            type="checkbox"
            checked={memberAcquitted}
            onChange={(e) => setMemberAcquitted(e.target.checked)}
            className="h-3.5 w-3.5 accent-amber-500"
          />
          <span>
            <span className="text-amber-400">Acquitted</span> — cleared by a court, so kept on
            record but left out of their kill and shooting counts
          </span>
        </label>
      )}

      {mode === 'member' ? (
        <>
          <Input className="h-8 text-sm" placeholder="Search member…" value={memberSearch} onChange={(e) => setMemberSearch(e.target.value)} />
          {memberResults && memberResults.length > 0 && memberSearch.length >= 2 && (
            <div className="max-h-32 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
              {memberResults.map((m) => (
                <button key={m.id} type="button" onClick={() => addMember(m.id, m.display_name)}
                  className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors flex items-center justify-between gap-2">
                  <span className="truncate">{m.display_name}</span>
                  {memberSetNameById[m.id] && (
                    <span className="text-[10px] text-zinc-400 shrink-0 truncate max-w-[40%]">{memberSetNameById[m.id]}</span>
                  )}
                </button>
              ))}
            </div>
          )}
          {memberSearch.length < 2 && suggestions.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-400">Suggested · same set</p>
              <div className="max-h-32 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
                {suggestions.map((m) => (
                  <button key={m.id} type="button" onClick={() => addMember(m.id, m.display_name)}
                    className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors flex items-center justify-between gap-2">
                    <span className="truncate">{m.display_name}</span>
                    {memberSetNameById[m.id] && (
                      <span className="text-[10px] text-zinc-400 shrink-0 truncate max-w-[40%]">{memberSetNameById[m.id]}</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <>
          <Input className="h-8 text-sm" placeholder="Search set…" value={setSearch} onChange={(e) => setSetSearch(e.target.value)} />
          {filteredSets.length > 0 && (
            <div className="max-h-32 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
              {filteredSets.map((s) => (
                <button key={s.id} type="button" onClick={() => addSet(s)}
                  className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors flex items-center justify-between gap-2">
                  <span className="truncate">{s.name}</span>
                  {s.is_reserved && <span className="text-[10px] text-zinc-400 shrink-0">system</span>}
                </button>
              ))}
            </div>
          )}
          <p className="text-[11px] text-zinc-400">Use when the individual shooter is unknown.</p>
        </>
      )}

      {total > 0 && (
        <div className="space-y-1 pt-1 border-t border-zinc-800">
          {participants.map((p) => (
            <div key={p.member_id} className="flex items-center justify-between rounded border border-zinc-800 px-2.5 py-1.5 text-sm gap-2">
              <span className="min-w-0 flex items-baseline gap-1.5 truncate">
                <span className="text-zinc-200 truncate">{p.member_name}</span>
                {memberSetNameById[p.member_id] && (
                  <span className="text-[10px] text-zinc-400 truncate">· {memberSetNameById[p.member_id]}</span>
                )}
              </span>
              <div className="flex items-center gap-1.5 shrink-0">
                <Badge variant="secondary" className="text-[10px] px-1.5">{p.role}</Badge>
                <Badge variant="outline" className="text-[10px] px-1.5">{p.outcome}</Badge>
                {isOffenderRole(p.role) && (
                  <button
                    type="button"
                    title={p.acquitted ? 'Cleared by a court — click to unset' : 'Mark as cleared by a court'}
                    onClick={() => onChangeParticipants(participants.map((x) =>
                      x.member_id === p.member_id ? { ...x, acquitted: !x.acquitted } : x
                    ))}
                    className={`rounded border px-1.5 text-[10px] transition-colors ${
                      p.acquitted
                        ? 'border-amber-500/40 bg-amber-500/10 text-amber-400'
                        : 'border-zinc-700 text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    Acquitted
                  </button>
                )}
                <button type="button" onClick={() => onChangeParticipants(participants.filter((x) => x.member_id !== p.member_id))}
                  className="text-zinc-400 hover:text-red-400 transition-colors">✕</button>
              </div>
            </div>
          ))}
          {setParticipants.map((p) => (
            <div key={p.set_id} className="flex items-center justify-between rounded border border-zinc-800 px-2.5 py-1.5 text-sm">
              <span className="text-zinc-200 truncate">{p.set_name}</span>
              <div className="flex items-center gap-1.5 shrink-0">
                <Badge variant="outline" className="text-[10px] px-1.5 text-zinc-400 border-zinc-700">set</Badge>
                <Badge variant="secondary" className="text-[10px] px-1.5">{p.role}</Badge>
                <Badge variant="outline" className="text-[10px] px-1.5">{p.outcome}</Badge>
                <button type="button" onClick={() => onChangeSetParticipants(setParticipants.filter((x) => x.set_id !== p.set_id))}
                  className="text-zinc-400 hover:text-red-400 transition-colors">✕</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {participants.some((p) => p.outcome === 'KILLED') && (
        <p className="text-[11px] text-zinc-400">
          <span className="font-medium text-zinc-400">KILLED</span> participants will be marked DEAD on save.
        </p>
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

/**
 * Seeded from props at mount and never resynced, so one mounted sheet reused
 * for a second incident kept the first's values in any field the second leaves
 * empty - and saving wrote them. Keying on the target forces a fresh instance.
 * See SetFormSheet in routes/_app.$universe.sets.index.tsx for the full note.
 */
export function IncidentFormSheet(props: IncidentFormProps) {
  return <IncidentFormSheetInner key={props.initial?.id ?? 'new'} {...props} />
}

function IncidentFormSheetInner({ universeId, open, onClose, initial, defaultParticipants, defaultMunicipalityId }: IncidentFormProps) {
  const create = useCreateIncident()
  const update = useUpdateIncident(initial?.id ?? '', universeId)
  const isEdit = !!initial
  const { data: munis } = useMunicipalities(universeId)
  const { data: allMembersData } = useAllMembers(universeId)
  const { data: allSetsData } = useAllSets(universeId)

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

  const allMunis = useMemo(() => munis?.items ?? [], [munis])
  const topLevelMunis = useMemo(
    () => allMunis.filter((m) => !m.parent_id).sort((a, b) => a.name.localeCompare(b.name)),
    [allMunis],
  )

  const [type, setType] = useState<IncidentType>(initial?.type ?? 'SHOOTING')
  const [date, setDate] = useState<FuzzyDateValue | null>(initial?.date ?? null)
  const [locationText, setLocationText] = useState(initial?.location_text ?? '')
  const [lat, setLat] = useState<string>(initial?.lat != null ? String(initial.lat) : '')
  const [lng, setLng] = useState<string>(initial?.lng != null ? String(initial.lng) : '')
  // City and sub-district: what the user picked, else what the initial
  // municipality implies. An effect used to copy the initial municipality into
  // state once the list loaded, a render late; now it is read when needed.
  const [cityPick, setCityId] = useState<string | null>(null)
  const [subPick, setSubDistrictId] = useState<string | null>(null)
  const [narrative, setNarrative] = useState(initial?.narrative ?? '')
  const [verified, setVerified] = useState(initial?.verified ?? false)
  const [participants, setParticipants] = useState<ParticipantDraft[]>(() =>
    initial?.participants?.map((p) => ({
      member_id: p.member_id,
      member_name: memberNameMap[p.member_id] ?? p.member_id,
      role: p.role,
      outcome: p.outcome,
      acquitted: p.acquitted,
    })) ?? defaultParticipants ?? []
  )
  const [setLevelParticipants, updateSetLevelParticipants] = useState<SetParticipantDraft[]>(() =>
    initial?.set_participants?.map((p) => ({
      set_id: p.set_id,
      set_name: setNameById[p.set_id] ?? p.set_id,
      role: p.role,
      outcome: p.outcome,
    })) ?? []
  )
  const [error, setError] = useState<string | null>(null)
  const urlPaste = useUrlPasteBanner()
  const [creatingSourceFromUrl, setCreatingSourceFromUrl] = useState<string | null>(null)

  // Address geocode autocomplete (Mapbox v6 forward geocoding)
  type MapboxFeature = {
    id: string
    geometry: { coordinates: [number, number]; type: string }
    properties: {
      feature_type?: string
      full_address?: string
      name?: string
      place_formatted?: string
      context?: {
        address?: { address_number?: string; street_name?: string; name?: string }
        street?: { name?: string }
        neighborhood?: { name?: string }
        postcode?: { name?: string }
        place?: { name?: string }
        district?: { name?: string }
        region?: { name?: string; region_code?: string }
        country?: { name?: string }
      }
    }
  }
  const [geoSearchTerm, setGeoSearchTerm] = useState('')
  const debouncedGeo = useDebounce(geoSearchTerm, 300)
  const [showGeoDropdown, setShowGeoDropdown] = useState(false)
  const mapboxToken = (import.meta.env.VITE_MAPBOX_TOKEN ?? '') as string

  // Address autocomplete as a query: loading, error and results follow the
  // debounced term, and a superseded request is cancelled through `signal`.
  // It replaces an effect that reset six pieces of state by hand. `silent`
  // keeps the global error toast off; the dropdown shows the error inline.
  const geoTerm = debouncedGeo.trim()
  const geoActive = geoTerm.length >= 3
  const geoQuery = useQuery({
    queryKey: ['geocode', geoTerm],
    queryFn: async ({ signal }) => {
      const r = await fetch(
        `https://api.mapbox.com/search/geocode/v6/forward?q=${encodeURIComponent(geoTerm)}` +
        `&autocomplete=true&limit=6&country=us&access_token=${mapboxToken}`,
        { signal },
      )
      if (!r.ok) throw new Error(`Mapbox ${r.status}`)
      const data: { features?: MapboxFeature[] } = await r.json()
      return Array.isArray(data.features) ? data.features : []
    },
    enabled: geoActive && !!mapboxToken,
    staleTime: 5 * 60_000,
    retry: false,
    meta: { silent: true },
  })
  const geoResults = geoActive ? geoQuery.data ?? [] : []
  const geoLoading = geoActive && !!mapboxToken && geoQuery.isFetching
  const geoError = !geoActive ? null
    : !mapboxToken ? 'Address autocomplete unavailable (missing VITE_MAPBOX_TOKEN)'
    : geoQuery.isError ? 'Geocoder error. Check console'
    : null
  const geoSearched = geoActive && (!mapboxToken || geoQuery.isFetched)

  function selectGeoResult(f: MapboxFeature) {
    const ctx = f.properties.context ?? {}
    const num = ctx.address?.address_number
    const streetName = ctx.address?.street_name ?? ctx.street?.name ?? f.properties.name ?? ''
    const street = [num, streetName].filter(Boolean).join(' ').trim() || (f.properties.name ?? '')
    setLocationText(street)
    const [lon, lat] = f.geometry.coordinates
    setLat(lat.toFixed(6))
    setLng(lon.toFixed(6))

    // Auto-match city → sub-district from Mapbox context fields
    const cityCandidates = [ctx.place?.name, ctx.district?.name].filter(Boolean) as string[]
    const matchedCity = topLevelMunis.find((m) =>
      cityCandidates.some((n) => n.toLowerCase() === m.name.toLowerCase()),
    )
    if (matchedCity) {
      setCityId(matchedCity.id)
      const subCandidates = [ctx.neighborhood?.name, ctx.postcode?.name].filter(Boolean) as string[]
      const children = allMunis.filter((m) => m.parent_id === matchedCity.id)
      const matchedSub = children.find((m) =>
        subCandidates.some((n) => n.toLowerCase() === m.name.toLowerCase()),
      )
      setSubDistrictId(matchedSub?.id ?? '')
    }

    setGeoSearchTerm('')
    setShowGeoDropdown(false)
  }

  function useTypedAddress() {
    setLocationText(geoSearchTerm)
    setGeoSearchTerm('')
    setShowGeoDropdown(false)
  }

  function formatGeoLabel(f: MapboxFeature): string {
    return f.properties.full_address
      ?? [f.properties.name, f.properties.place_formatted].filter(Boolean).join(', ')
      ?? f.id
  }

  // Names shown for participants come from the member and set lists, which
  // load after the form opens in edit mode. They are read at render; effects
  // used to rewrite the participants state once each list arrived.
  const displayParticipants = useMemo(
    () => participants.map((p) => ({ ...p, member_name: memberNameMap[p.member_id] ?? p.member_name })),
    [participants, memberNameMap],
  )
  const displaySetParticipants = useMemo(
    () => setLevelParticipants.map((p) => ({ ...p, set_name: setNameById[p.set_id] ?? p.set_name })),
    [setLevelParticipants, setNameById],
  )

  const initialMuni = useMemo(() => {
    const initialId = initial?.municipality_id ?? defaultMunicipalityId ?? ''
    return initialId ? allMunis.find((m) => m.id === initialId) ?? null : null
  }, [allMunis, initial?.municipality_id, defaultMunicipalityId])
  const cityId = cityPick ?? (initialMuni ? initialMuni.parent_id ?? initialMuni.id : '')
  const subDistrictId = subPick ?? (initialMuni?.parent_id ? initialMuni.id : '')

  const subDistricts = useMemo(
    () => allMunis.filter((m) => m.parent_id === cityId).sort((a, b) => a.name.localeCompare(b.name)),
    [allMunis, cityId],
  )

  const effectiveMunicipalityId = subDistrictId || cityId || null

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      const body: Record<string, unknown> = {
        universe_id: universeId,
        type, date,
        location_text: locationText || null,
        lat: lat !== '' ? parseFloat(lat) : null,
        lng: lng !== '' ? parseFloat(lng) : null,
        municipality_id: effectiveMunicipalityId,
        narrative: narrative || null,
        verified,
        participants: participants.map(({ member_id, role, outcome, acquitted }) => ({
          member_id, role, outcome, acquitted,
        })),
        set_participants: setLevelParticipants.map(({ set_id, role, outcome }) => ({ set_id, role, outcome })),
      }
      if (isEdit) {
        await update.mutateAsync(body)
        toast.success(`Updated ${type.toLowerCase()} incident`)
      } else {
        await create.mutateAsync(body)
        toast.success(`Recorded ${type.toLowerCase()} incident`)
        setType('SHOOTING'); setDate(null); setLocationText(''); setLat(''); setLng(''); setCityId(''); setSubDistrictId('')
        setNarrative(''); setVerified(false); setParticipants([]); updateSetLevelParticipants([])
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
          <div className="flex items-end gap-3">
            <div className="flex-1 space-y-1.5">
              <Label>Type</Label>
              <Select value={type} onValueChange={(v) => setType(v as IncidentType)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TYPE_ORDER.map((t) => (
                    <SelectItem key={t} value={t}>{TYPE_CONFIG[t].label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2 pb-2">
              <input id="inc-verified" type="checkbox" checked={verified} onChange={(e) => setVerified(e.target.checked)}
                className="rounded border-zinc-700 bg-zinc-900 accent-violet-600" />
              <label htmlFor="inc-verified" className="text-sm text-zinc-300">Verified</label>
            </div>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <FuzzyDateInput value={date} onChange={setDate} label="Date" idPrefix="inc-date" />
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 space-y-3">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">Location</p>
            <div className="space-y-1.5">
              <Label className="text-zinc-300">City</Label>
              <Select value={cityId || 'none'} onValueChange={(v) => { setCityId(v === 'none' ? '' : v); setSubDistrictId('') }}>
                <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {topLevelMunis.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {cityId && subDistricts.length > 0 && (
              <div className="space-y-1.5">
                <Label className="text-zinc-300">Sub-district</Label>
                <Select value={subDistrictId || 'none'} onValueChange={(v) => setSubDistrictId(v === 'none' ? '' : v)}>
                  <SelectTrigger><SelectValue placeholder="City level" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">City level</SelectItem>
                    {subDistricts.map((m) => (
                      <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="inc-loc" className="text-zinc-300">Address / Area</Label>
              <div className="relative">
                <Input
                  id="inc-loc"
                  value={geoSearchTerm || locationText}
                  onChange={(e) => {
                    setLocationText(e.target.value)
                    setGeoSearchTerm(e.target.value)
                    setShowGeoDropdown(true)
                  }}
                  onBlur={() => setTimeout(() => setShowGeoDropdown(false), 150)}
                  onFocus={() => (geoResults.length > 0 || geoSearched) && setShowGeoDropdown(true)}
                  placeholder="Street address or intersection"
                  autoComplete="off"
                />
                {showGeoDropdown && (geoLoading || geoResults.length > 0 || (geoSearched && geoSearchTerm.length >= 3)) && (
                  <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-zinc-700 bg-zinc-950 shadow-xl">
                    {geoLoading && (
                      <div className="px-3 py-2 text-xs text-zinc-400">Searching…</div>
                    )}
                    {!geoLoading && geoError && (
                      <div className="px-3 py-2 text-xs text-amber-400">{geoError}</div>
                    )}
                    {!geoLoading && !geoError && geoResults.map((r, i) => (
                      <button
                        key={r.id ?? i}
                        type="button"
                        onMouseDown={() => selectGeoResult(r)}
                        className="block w-full px-3 py-2 text-left text-sm text-zinc-200 hover:bg-zinc-800 transition-colors"
                      >
                        {formatGeoLabel(r)}
                      </button>
                    ))}
                    {!geoLoading && geoSearchTerm.length >= 3 && (
                      <button
                        type="button"
                        onMouseDown={useTypedAddress}
                        className="block w-full border-t border-zinc-800 px-3 py-2 text-left text-xs text-zinc-400 hover:bg-zinc-800 transition-colors"
                      >
                        {geoResults.length === 0
                          ? <>No matches. <span className="text-violet-400">use “{geoSearchTerm}” as typed</span></>
                          : <>None of these. <span className="text-violet-400">use “{geoSearchTerm}” as typed</span></>}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1.5">
                <Label htmlFor="inc-lat" className="text-xs text-zinc-400">Latitude</Label>
                <Input id="inc-lat" type="number" step="any" value={lat} onChange={(e) => setLat(e.target.value)} placeholder="41.8781" className="h-8 text-sm" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="inc-lng" className="text-xs text-zinc-400">Longitude</Label>
                <Input id="inc-lng" type="number" step="any" value={lng} onChange={(e) => setLng(e.target.value)} placeholder="-87.6298" className="h-8 text-sm" />
              </div>
            </div>
          </div>
          <ParticipantsSection
            universeId={universeId}
            participants={displayParticipants}
            onChangeParticipants={setParticipants}
            setParticipants={displaySetParticipants}
            onChangeSetParticipants={updateSetLevelParticipants}
            allMembers={allMembersList}
            allSets={allSetsData?.items ?? []}
          />
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
            value === key ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'
          }`}>
          {label}
          {count !== undefined && (
            <span className={`tabular-nums ${value === key ? 'text-zinc-300' : 'text-zinc-400'}`}>{count}</span>
          )}
        </button>
      ))}
    </div>
  )
}

// ─── Filter presets ───────────────────────────────────────────────────────────

/**
 * A preset is a saved URL search. The filters used to live in component state,
 * so a preset had to copy each one by hand and a bookmark could not hold any;
 * now the URL is the filter, and a preset just names one.
 */
interface FilterPreset {
  name: string
  search: IncidentsSearch
}

function presetsKey(universeId: string): string {
  return `incidents-presets-${universeId}`
}

/** Reads presets, converting the pre-URL shape ({type, verified, participantId, municipalityId}). */
function loadPresets(universeId: string): FilterPreset[] {
  try {
    const raw = localStorage.getItem(presetsKey(universeId))
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.flatMap((p): FilterPreset[] => {
      if (!p || typeof p.name !== 'string') return []
      if (p.search && typeof p.search === 'object') return [{ name: p.name, search: p.search }]
      return [{
        name: p.name,
        search: {
          type: p.type && p.type !== 'ALL' ? p.type : undefined,
          verified: p.verified === 'VERIFIED' ? 'yes' : p.verified === 'UNVERIFIED' ? 'no' : undefined,
          member: p.participantId ?? undefined,
          municipality_id: p.municipalityId ?? undefined,
        },
      }]
    })
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

// ─── Sorting and search helpers ───────────────────────────────────────────────

/** Sortable number for a fuzzy date; missing parts sort to the start of their period. */
function dateKey(d: FuzzyDateValue | null): number | null {
  if (!d || !d.year || d.precision === 'UNKNOWN') return null
  return d.year * 10_000 + (d.month ?? 0) * 100 + (d.day ?? 0)
}

const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

function haystack(i: IncidentListItem): string {
  return fold([
    TYPE_CONFIG[i.type]?.label ?? i.type,
    i.location_text ?? '',
    i.municipality_name ?? '',
    ...(i.victim_names ?? []),
    ...(i.shooter_names ?? []),
  ].join(' '))
}

// ─── Page ─────────────────────────────────────────────────────────────────────

/* ────────────────────────────────────────────────────────────────────────────
   The list holds every incident of the universe, not a page of it.

   It used to hold one cursor page of 50, ordered by when a row was *entered*,
   and run the type and verified filters, the tab counts and the calendar
   heatmap over that page alone: in Illinois (3345 incidents) every number on
   the screen described 1.5% of the data. "Load more" swapped the page rather
   than extending it. Now useAllIncidents follows the cursor to the end, sorting
   is by when the incident happened, and every filter is in the URL, so Back
   from an incident lands on the same view and other pages can link to one.
   Participant and municipality stay server-side scopes (their endpoints return
   the full set for one member or one zone); everything else narrows in memory.
   ──────────────────────────────────────────────────────────────────────── */

function IncidentsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const search = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })

  const typeFilter: TypeFilter = search.type ?? 'ALL'
  const verifiedFilter: VerifiedFilter = search.verified === 'yes' ? 'VERIFIED' : search.verified === 'no' ? 'UNVERIFIED' : 'ALL'
  const participantId = (search.member ?? null) as UUID | null
  // Participant filter wins over municipality filter when both are present.
  const municipalityId = !participantId && search.municipality_id ? (search.municipality_id as UUID) : null
  const sortKey: SortKey = search.sort ?? 'date'
  const sortDir = search.order ?? 'desc'

  const [q, setQ] = useState(search.q ?? '')
  const debouncedQ = useDebounce(q.trim(), 150)
  useEffect(() => {
    if ((search.q ?? '') === debouncedQ) return
    navigate({ search: (prev) => ({ ...prev, q: debouncedQ || undefined }), replace: true })
  }, [debouncedQ, search.q, navigate])

  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [participantSearch, setParticipantSearch] = useState('')
  const debouncedParticipantSearch = useDebounce(participantSearch, 200)

  const allQuery = useAllIncidents(participantId || municipalityId ? null : universeId)
  const participantQuery = useMemberIncidents(participantId, universeId)
  const muniQuery = useIncidentsByMunicipality(municipalityId, universeId)
  const scopeQuery = participantId ? participantQuery : municipalityId ? muniQuery : allQuery
  const isLoading = scopeQuery.isLoading

  const { data: munis } = useMunicipalities(universeId)
  const { data: participantResults } = useMemberSearch(universeId, debouncedParticipantSearch)
  const { data: participant } = useMember(participantId ?? '', participantId ? universeId : null)
  const participantName = participant?.display_name ?? null
  const municipalityName = municipalityId
    ? (munis?.items ?? []).find((m) => m.id === municipalityId)?.name ?? null
    : null

  function patch(next: Partial<IncidentsSearch>) {
    navigate({ search: (prev) => ({ ...prev, ...next }), replace: true })
  }

  // ── Bulk delete ───────────────────────────────────────────────────────────
  const [selected, setSelected] = useState<Set<UUID>>(new Set())
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const deleteIncident = useDeleteIncident(universeId ?? '')

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
    if (universeId) setPresets(loadPresets(universeId))
  }, [universeId])

  const hasActiveFilter =
    typeFilter !== 'ALL' || verifiedFilter !== 'ALL' || !!participantId || !!municipalityId || !!debouncedQ

  function applyPreset(p: FilterPreset) {
    setQ(p.search.q ?? '')
    setParticipantSearch('')
    navigate({ search: p.search, replace: false })
  }

  function saveCurrentAsPreset() {
    if (!universeId || !hasActiveFilter) return
    const name = window.prompt('Name this filter preset:')?.trim()
    if (!name) return
    // A preset is the filters, not the ordering.
    const filters: IncidentsSearch = { ...search, sort: undefined, order: undefined }
    const updated = [...presets.filter((p) => p.name !== name), { name, search: filters }]
    setPresets(updated)
    persistPresets(universeId, updated)
  }

  function deletePreset(name: string) {
    if (!universeId) return
    const updated = presets.filter((p) => p.name !== name)
    setPresets(updated)
    persistPresets(universeId, updated)
  }

  function clearAll() {
    setQ('')
    setParticipantSearch('')
    navigate({ search: {}, replace: true })
  }

  // ── Derivation: scope → search → counts → type/verified → sort ────────────
  const scoped = useMemo(() => scopeQuery.data?.items ?? [], [scopeQuery.data])

  const searched = useMemo(() => {
    if (!debouncedQ) return scoped
    const terms = fold(debouncedQ).split(/\s+/).filter(Boolean)
    return scoped.filter((i) => {
      const h = haystack(i)
      return terms.every((t) => h.includes(t))
    })
  }, [scoped, debouncedQ])

  // Faceted counts: each group counts under the other group's filter, so every
  // number says what clicking it would show.
  const byVerified = useMemo(
    () => verifiedFilter === 'ALL' ? searched : searched.filter((i) => i.verified === (verifiedFilter === 'VERIFIED')),
    [searched, verifiedFilter],
  )
  const byType = useMemo(
    () => typeFilter === 'ALL' ? searched : searched.filter((i) => i.type === typeFilter),
    [searched, typeFilter],
  )
  const typeCounts = useMemo(() => {
    const counts = Object.fromEntries(TYPE_ORDER.map((t) => [t, 0])) as Record<IncidentType, number>
    for (const i of byVerified) if (i.type in counts) counts[i.type] += 1
    return counts
  }, [byVerified])
  const verifiedCount = useMemo(() => byType.filter((i) => i.verified).length, [byType])

  const items = useMemo(() => {
    let list = byType
    if (verifiedFilter !== 'ALL') list = list.filter((i) => i.verified === (verifiedFilter === 'VERIFIED'))
    if (sortKey === 'added') {
      // The API already returns newest-recorded first.
      return sortDir === 'desc' ? list : [...list].reverse()
    }
    const dir = sortDir === 'asc' ? 1 : -1
    return [...list].sort((a, b) => {
      const ka = dateKey(a.date)
      const kb = dateKey(b.date)
      // Undated incidents sink to the bottom in either direction.
      if (ka === null || kb === null) return ka === kb ? 0 : ka === null ? 1 : -1
      return (ka - kb) * dir
    })
  }, [byType, verifiedFilter, sortKey, sortDir])

  const undatedCount = useMemo(() => scoped.filter((i) => dateKey(i.date) === null).length, [scoped])

  // Drop selections the filters no longer show.
  useEffect(() => {
    setSelected((prev) => {
      if (prev.size === 0) return prev
      const visible = new Set(items.map((i) => i.id))
      const next = new Set([...prev].filter((id) => visible.has(id)))
      return next.size === prev.size ? prev : next
    })
  }, [items])

  const tableScrollRef = useRef<HTMLDivElement | null>(null)
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 64,
    overscan: 8,
  })
  const virtualRows = rowVirtualizer.getVirtualItems()
  const padTop = virtualRows[0]?.start ?? 0
  const padBottom = rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)

  if (!universe) return <NoUniverse />

  // Only surface the types this universe actually uses. The enum is global, so
  // Detroit would otherwise grow tabs for bombings and Corsica for shootings.
  // The active filter stays listed even at zero so it can be switched back off.
  const presentTypes = TYPE_ORDER.filter((t) => typeCounts[t] > 0 || typeFilter === t)

  const headerDesc = isLoading ? 'Loading…'
    : scoped.length === 0 ? 'No incidents yet'
    : [
        items.length === scoped.length
          ? `${scoped.length.toLocaleString()} incidents`
          : `${items.length.toLocaleString()} of ${scoped.length.toLocaleString()} incidents`,
        verifiedFilter === 'ALL' && verifiedCount > 0 && `${verifiedCount} verified`,
        undatedCount > 0 && `${undatedCount.toLocaleString()} undated`,
      ].filter(Boolean).join(' · ')

  const emptyTitle = hasActiveFilter ? 'No incidents match the current filters' : 'No incidents recorded yet'

  return (
    <div>
      <PageHeader
        title="Incidents"
        description={headerDesc}
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm"
              onClick={() => {
                const date = new Date().toISOString().slice(0, 10)
                downloadCsv(`/incidents/?universe_id=${universe.id}&format=csv`, `incidents-${universe.slug}-${date}.csv`)
              }}>
              <Download className="mr-1.5 h-3.5 w-3.5" />Export all
            </Button>
            <Button size="sm" onClick={() => setCreating(true)}>
              <Plus className="mr-1.5 h-4 w-4" />Add incident
            </Button>
          </div>
        }
      />

      {/* Calendar density, over what the filters show. Not on phones: there it
          filled the first screen and pushed every incident below the fold. */}
      {items.length > 0 && (
        <div className="mb-4 hidden sm:block">
          <Suspense fallback={<div className="h-40 rounded-lg border border-zinc-800 bg-zinc-900/30" />}>
            <IncidentHeatmap incidents={items} />
          </Suspense>
        </div>
      )}

      {/* Search + scopes */}
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[220px] max-w-md flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            className="h-9 pl-8 pr-8 text-sm"
            placeholder="Search victim, shooter, place…"
            aria-label="Search incidents"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape' && q) { e.stopPropagation(); setQ('') } }}
          />
          {q && (
            <button
              type="button"
              aria-label="Clear search"
              onClick={() => setQ('')}
              className="absolute right-1.5 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-white"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {participantId ? (
          <button
            type="button"
            onClick={() => patch({ member: undefined })}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-violet-700/60 bg-violet-950/40 px-2.5 text-xs font-medium text-violet-300 transition-colors hover:bg-violet-900/40"
          >
            <User className="h-3 w-3" />
            <span>Participant: {participantName ?? '…'}</span>
            <X className="h-3 w-3" />
          </button>
        ) : (
          <div className="relative min-w-[200px]">
            <User className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
            <Input
              className="h-9 pl-8 text-sm"
              placeholder="Filter by participant…"
              aria-label="Filter by participant"
              value={participantSearch}
              onChange={(e) => setParticipantSearch(e.target.value)}
            />
            {debouncedParticipantSearch.length >= 2 && participantResults && (
              <div className="absolute z-20 mt-1 max-h-60 w-full overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950 shadow-lg">
                {participantResults.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-zinc-400">No matching members.</div>
                ) : (
                  participantResults.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => { setParticipantSearch(''); patch({ member: m.id, municipality_id: undefined }) }}
                      className="w-full px-3 py-2 text-left text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
                    >
                      {m.display_name}
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        )}

        {municipalityId && (
          <button
            type="button"
            onClick={() => patch({ municipality_id: undefined })}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-violet-700/60 bg-violet-950/40 px-2.5 text-xs font-medium text-violet-300 transition-colors hover:bg-violet-900/40"
          >
            <span>Zone: {municipalityName ?? '…'}</span>
            <X className="h-3 w-3" />
          </button>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-9 gap-1.5">
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
              <DropdownMenuLabel className="text-xs font-normal text-zinc-400">
                No saved presets yet.
              </DropdownMenuLabel>
            ) : (
              <>
                <DropdownMenuLabel className="text-[10px] uppercase tracking-wider text-zinc-400">
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
                      className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-red-400"
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
      </div>

      {/* Facets + sort */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="-mx-1 flex max-w-full overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <FilterTabs<TypeFilter>
            value={typeFilter}
            onChange={(v) => patch({ type: v === 'ALL' ? undefined : v })}
            options={[
              { key: 'ALL', label: 'All', count: byVerified.length },
              ...presentTypes.map((t) => ({ key: t, label: `${TYPE_CONFIG[t].label}s`, count: typeCounts[t] })),
            ]}
          />
        </div>
        <FilterTabs<VerifiedFilter>
          value={verifiedFilter}
          onChange={(v) => patch({ verified: v === 'VERIFIED' ? 'yes' : v === 'UNVERIFIED' ? 'no' : undefined })}
          options={[
            { key: 'ALL', label: 'All' },
            { key: 'VERIFIED', label: 'Verified', count: verifiedCount },
            { key: 'UNVERIFIED', label: 'Unverified', count: byType.length - verifiedCount },
          ]}
        />
        <div className="ml-auto flex items-center gap-2">
          <Select
            value={`${sortKey}-${sortDir}`}
            onValueChange={(v) => {
              const [k, d] = v.split('-') as [SortKey, 'asc' | 'desc']
              patch({ sort: k === 'date' ? undefined : k, order: d === 'desc' ? undefined : d })
            }}
          >
            <SelectTrigger aria-label="Sort incidents" className="h-8 w-auto gap-2 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="date-desc">Newest first</SelectItem>
              <SelectItem value="date-asc">Oldest first</SelectItem>
              <SelectItem value="added-desc">Recently added</SelectItem>
            </SelectContent>
          </Select>
          {hasActiveFilter && (
            <button onClick={clearAll} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-white">
              <X className="h-3 w-3" /> Clear
            </button>
          )}
        </div>
      </div>

      {/* Table, always virtualised: it holds the whole universe */}
      <div
        ref={tableScrollRef}
        className="overflow-y-auto overflow-x-hidden rounded-lg border border-zinc-800"
        style={{ maxHeight: 'calc(100dvh - 14rem)' }}
      >
        <table className="w-full table-fixed text-sm">
          <colgroup>
            <col className="w-10" />
            <col className="w-12" />
            <col />
            <col className="w-10" />
          </colgroup>
          <thead className="sticky top-0 z-10 bg-zinc-900/95 backdrop-blur">
            <tr className="border-b border-zinc-800">
              <th className="px-3 py-2.5" scope="col">
                <input
                  type="checkbox"
                  aria-label="Select all shown incidents"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={() => setSelected(selected.size === items.length ? new Set() : new Set(items.map((i) => i.id)))}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              <th className="py-2.5" scope="col" aria-label="Type" />
              <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400" scope="col">Incident</th>
              <th scope="col" aria-label="Actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading && Array.from({ length: 6 }).map((_, i) => <TableRowSkeleton key={i} cols={4} height={64} />)}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <EmptyState
                    icon={ShieldAlert}
                    title={emptyTitle}
                    description={hasActiveFilter ? undefined : 'Record a shooting or murder to begin tracking.'}
                    action={
                      hasActiveFilter
                        ? <Button size="sm" variant="outline" onClick={clearAll}>Clear search and filters</Button>
                        : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" /> Record the first incident</Button>
                    }
                  />
                </td>
              </tr>
            )}
            {!isLoading && padTop > 0 && <tr aria-hidden><td colSpan={4} style={{ height: padTop }} /></tr>}
            {!isLoading && virtualRows.map((vRow) => {
              const incident = items[vRow.index]
              const cfg = TYPE_CONFIG[incident.type]
              const Icon = cfg?.icon ?? ShieldAlert
              const muniName = incident.municipality_name
              const locationLabel = incident.location_text
                ? muniName && !incident.location_text.includes(muniName) ? `${muniName} · ${incident.location_text}` : incident.location_text
                : muniName
              const isSelected = selected.has(incident.id)
              const victimNames = incident.victim_names ?? []
              const shooterNames = incident.shooter_names ?? []

              return (
                <tr
                  key={incident.id}
                  ref={rowVirtualizer.measureElement}
                  data-index={vRow.index}
                  className={`group transition-colors hover:bg-zinc-900/50 ${isSelected ? 'bg-violet-950/20' : ''}`}
                >
                  <td className="px-3">
                    <input
                      type="checkbox"
                      aria-label={`Select ${incident.type.toLowerCase()} incident`}
                      checked={isSelected}
                      onChange={() => toggleSelectIncident(incident.id)}
                      className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                    />
                  </td>
                  <td className="py-3 pl-1 pr-1">
                    <Link from="/$universe" to="/$universe/incidents/$id" params={{ id: incident.id }} tabIndex={-1} aria-hidden>
                      <div className={`flex h-9 w-9 items-center justify-center rounded-md ${cfg?.tile ?? 'bg-zinc-900 text-zinc-400'}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                    </Link>
                  </td>
                  <td className="min-w-0 p-0">
                    <Link
                      from="/$universe" to="/$universe/incidents/$id"
                      params={{ id: incident.id }}
                      className="block min-w-0 px-3 py-2.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500 sm:px-4"
                    >
                      <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5">
                        <TypeChip type={incident.type} />
                        <span className="font-mono text-xs tabular-nums text-zinc-400">
                          {incident.date ? <FuzzyDate value={incident.date} /> : 'Undated'}
                        </span>
                        {incident.verified && (
                          <span className="inline-flex items-center gap-0.5 text-xs font-medium text-emerald-400">
                            <CheckCircle2 className="h-3 w-3" />Verified
                          </span>
                        )}
                        {locationLabel && (
                          <span className="min-w-0 max-w-full truncate text-xs text-zinc-400">{locationLabel}</span>
                        )}
                      </div>
                      <div className="mt-1 flex min-h-[1.25rem] min-w-0 flex-wrap items-center gap-x-3 gap-y-0.5">
                        {victimNames.length > 0 && (
                          <span className="flex min-w-0 items-center gap-1.5">
                            <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                              {victimNames.length === 1 ? 'Victim' : 'Victims'}
                            </span>
                            <span className="truncate text-xs text-rose-300">
                              {victimNames.slice(0, 3).join(', ')}
                              {victimNames.length > 3 && <span className="text-zinc-400"> +{victimNames.length - 3}</span>}
                            </span>
                          </span>
                        )}
                        {shooterNames.length > 0 && (
                          <span className="flex min-w-0 items-center gap-1.5">
                            <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                              {shooterNames.length === 1 ? 'Shooter' : 'Shooters'}
                            </span>
                            <span className="truncate text-xs text-amber-300">
                              {shooterNames.slice(0, 3).join(', ')}
                              {shooterNames.length > 3 && <span className="text-zinc-400"> +{shooterNames.length - 3}</span>}
                            </span>
                          </span>
                        )}
                        {victimNames.length === 0 && shooterNames.length === 0 && (
                          <span className="text-xs text-zinc-500">No participants recorded</span>
                        )}
                      </div>
                    </Link>
                  </td>
                  <td className="pr-2">
                    {/* Always visible below lg: a hover-only control does not exist on a touch screen. */}
                    <button
                      onClick={() => setEditingId(incident.id)}
                      aria-label="Edit incident"
                      className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              )
            })}
            {!isLoading && padBottom > 0 && <tr aria-hidden><td colSpan={4} style={{ height: padBottom }} /></tr>}
          </tbody>
        </table>
      </div>

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
