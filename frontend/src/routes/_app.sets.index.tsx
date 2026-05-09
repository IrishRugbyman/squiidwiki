import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Copy, Download, LayoutGrid, MapPin, MoreVertical, Pencil, Plus, Rows3, Search, Shield, Trash2, User, Users, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { SetStatusBadge } from '@/components/StatusBadge'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useAlliances, useCreateSet, useDeleteSet, useGangs, useMunicipalities, useSet, useSets, useUpdateSet, type SetsListParams } from '@/lib/queries'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import { useDebounce } from '@/hooks/useDebounce'
import { EmptyState } from '@/components/EmptyState'
import { TableRowSkeleton } from '@/components/skeletons'
import type { NameVariant, SetListItem, SetReadDetail, SetStatus, UUID } from '@/lib/types'

function emptyVariant(isPrimary = false): NameVariant {
  return { name: '', initials: '', number: '', is_primary: isPrimary, lead: null }
}

// Pick which slot leads display for this variant. Honors v.lead when it
// points to a populated slot; otherwise falls back to name → initials → number.
function variantLead(v: NameVariant): 'name' | 'initials' | 'number' | null {
  if (v.lead && v[v.lead]?.trim()) return v.lead
  if (v.name?.trim()) return 'name'
  if (v.initials?.trim()) return 'initials'
  if (v.number?.trim()) return 'number'
  return null
}

function variantDisplay(v: NameVariant): string {
  const lead = variantLead(v)
  return lead ? (v[lead] ?? '').trim() : ''
}

function variantsToDisplayName(variants: NameVariant[]): string {
  const primary = variants.find((v) => v.is_primary) ?? variants[0]
  return primary ? variantDisplay(primary) : ''
}

// Render one variant compactly using its lead slot first, e.g.
// "5674 (JeffMobb ReubGang · JMRB)" or "Across The Ave (ATA · 282)".
function formatVariant(v: NameVariant): string {
  const lead = variantLead(v)
  if (!lead) return ''
  const head = (v[lead] ?? '').trim()
  const extras: string[] = []
  for (const slot of ['name', 'initials', 'number'] as const) {
    if (slot === lead) continue
    const val = v[slot]?.trim()
    if (val) extras.push(val)
  }
  return extras.length > 0 ? `${head} (${extras.join(' · ')})` : head
}

function nonPrimaryVariantsText(variants?: NameVariant[] | null, sep = ' · '): string {
  if (!variants) return ''
  return variants.filter((v) => !v.is_primary).map(formatVariant).filter(Boolean).join(sep)
}

function initialVariants(initial?: SetReadDetail | null, copyFrom?: SetReadDetail | null): NameVariant[] {
  const src = initial?.name_variants ?? copyFrom?.name_variants
  if (src && src.length > 0) {
    return src.map((v) => ({
      name: v.name ?? '',
      initials: v.initials ?? '',
      number: v.number ?? '',
      is_primary: !!v.is_primary,
      lead: v.lead ?? null,
    }))
  }
  const seedName = initial?.name ?? copyFrom?.name ?? ''
  return [{ name: seedName, initials: '', number: '', is_primary: true, lead: null }]
}

// ─── URL search params ────────────────────────────────────────────────────────

type SortKey = 'name' | 'status' | 'member_count' | 'updated_at' | 'created_at'
type ViewMode = 'table' | 'cards'
type Density = 'compact' | 'comfortable'

interface SetsSearch {
  q?: string
  status?: SetStatus
  alliance?: string  // UUID, 'none', or undefined
  gang?: string
  muni?: string
  sort?: SortKey
  order?: 'asc' | 'desc'
  view?: ViewMode
  density?: Density
  page?: number
  size?: number
}

const SORT_KEYS: SortKey[] = ['name', 'status', 'member_count', 'updated_at', 'created_at']

export const Route = createFileRoute('/_app/sets/')({
  validateSearch: (s: Record<string, unknown>): SetsSearch => ({
    q: typeof s.q === 'string' && s.q ? s.q : undefined,
    status: s.status === 'ACTIVE' || s.status === 'EXTINCT' ? s.status : undefined,
    alliance: typeof s.alliance === 'string' && s.alliance ? s.alliance : undefined,
    gang: typeof s.gang === 'string' && s.gang ? s.gang : undefined,
    muni: typeof s.muni === 'string' && s.muni ? s.muni : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as SortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
    view: s.view === 'cards' ? 'cards' : s.view === 'table' ? 'table' : undefined,
    density: s.density === 'comfortable' ? 'comfortable' : s.density === 'compact' ? 'compact' : undefined,
    page: typeof s.page === 'number' && s.page > 0 ? Math.floor(s.page) : undefined,
    size: typeof s.size === 'number' && [20, 50, 100].includes(s.size) ? s.size : undefined,
  }),
  component: SetsPage,
})

// ─── Set avatar ───────────────────────────────────────────────────────────────

// Perceptually uniform palette: HSL with fixed saturation + lightness so every
// avatar has the same brightness regardless of the hashed hue.
function setColorStyle(name: string): React.CSSProperties {
  let h = 0
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) & 0xffff
  const hue = h % 360
  return {
    backgroundColor: `hsl(${hue} 45% 26% / 0.75)`,
    color: `hsl(${hue} 60% 78%)`,
    borderColor: `hsl(${hue} 40% 36% / 0.45)`,
  }
}

export function SetAvatar({ name, thumbUrl, size = 'md', isReserved = false }: { name: string; thumbUrl?: string | null; size?: 'sm' | 'md'; isReserved?: boolean }) {
  const [imgError, setImgError] = useState(false)
  const sz = size === 'sm' ? 'h-7 w-7 text-xs' : 'h-8 w-8 text-sm'
  const iconSz = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'
  if (isReserved) {
    const Icon = name === 'Police' ? Shield : User
    return (
      <div
        className={`${sz} shrink-0 rounded-md border border-zinc-700 bg-zinc-800/60 flex items-center justify-center`}
        aria-hidden
      >
        <Icon className={`${iconSz} text-zinc-400`} />
      </div>
    )
  }
  if (thumbUrl && !imgError) {
    return (
      <img
        src={thumbUrl}
        alt={name}
        loading="lazy"
        decoding="async"
        className={`${sz} shrink-0 rounded-md object-cover ring-1 ring-zinc-700`}
        onError={() => setImgError(true)}
      />
    )
  }
  return (
    <div
      className={`${sz} shrink-0 rounded-md border flex items-center justify-center font-bold`}
      style={setColorStyle(name)}
      aria-hidden
    >
      {name.slice(0, 2).toUpperCase()}
    </div>
  )
}

// ─── Form sheet ───────────────────────────────────────────────────────────────

interface SetFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: SetReadDetail
  onSaved?: (data: SetReadDetail) => void
  defaultAllianceId?: string
  defaultMunicipalityId?: string
  copyFrom?: SetReadDetail
}

const ALLIANCE_NONE = '__none__'
const MUNI_NONE = '__none__'
const GANG_NONE = '__none__'

export function SetFormSheet({ universeId, open, onClose, initial, onSaved, defaultAllianceId, defaultMunicipalityId, copyFrom }: SetFormProps) {
  const create = useCreateSet()
  const update = useUpdateSet(initial?.id ?? '')
  const { data: alliancesData } = useAlliances(universeId)
  const { data: munisData } = useMunicipalities(universeId)
  const { data: gangsData } = useGangs(universeId)
  const isEdit = !!initial

  const [variants, setVariants] = useState<NameVariant[]>(() => initialVariants(initial, copyFrom))
  const name = variantsToDisplayName(variants)
  const [bio, setBio] = useState(initial?.bio ?? copyFrom?.bio ?? '')
  const [status, setStatus] = useState<SetStatus>(initial?.status ?? copyFrom?.status ?? 'ACTIVE')
  const [allianceId, setAllianceId] = useState<string>(initial?.alliance_id ?? copyFrom?.alliance_id ?? defaultAllianceId ?? ALLIANCE_NONE)
  const [gangId, setGangId] = useState<string>(initial?.gang_id ?? copyFrom?.gang_id ?? GANG_NONE)
  const [municipalityId, setMunicipalityId] = useState<string>(initial?.municipality_id ?? copyFrom?.municipality_id ?? defaultMunicipalityId ?? MUNI_NONE)
  const [territoryIds, setTerritoryIds] = useState<string[]>(initial?.territory_ids ?? copyFrom?.territory_ids ?? [])
  const [error, setError] = useState<string | null>(null)

  // Top-level municipalities only — these are the choices for the primary anchor.
  const allMunis = munisData?.items ?? []
  const topLevelMunis = useMemo(
    () => allMunis.filter((m) => !m.parent_id).sort((a, b) => a.name.localeCompare(b.name)),
    [allMunis],
  )
  // Sub-districts available for the chosen municipality.
  const subDistricts = useMemo(
    () => allMunis
      .filter((m) => m.parent_id === municipalityId)
      .sort((a, b) => a.name.localeCompare(b.name)),
    [allMunis, municipalityId],
  )

  // When the primary municipality changes, drop any territory selections that
  // are no longer children of the new parent (or all of them, if user picked
  // "no municipality").
  function handleMunicipalityChange(v: string) {
    setMunicipalityId(v)
    setTerritoryIds((prev) => {
      if (v === MUNI_NONE) return []
      const validChildIds = new Set(allMunis.filter((m) => m.parent_id === v).map((m) => m.id))
      return prev.filter((id) => validChildIds.has(id))
    })
  }

  function toggleTerritory(id: string) {
    setTerritoryIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const alliance_id = allianceId === ALLIANCE_NONE ? null : allianceId
    const gang_id = gangId === GANG_NONE ? null : gangId
    const municipality_id = municipalityId === MUNI_NONE ? null : municipalityId
    const cleanedVariants = variants
      .map((v) => {
        const cleanName = (v.name ?? '').trim() || null
        const cleanInitials = (v.initials ?? '').trim() || null
        const cleanNumber = (v.number ?? '').trim() || null
        let lead = v.lead ?? null
        // Drop lead if the slot it points at is empty.
        if (lead === 'name' && !cleanName) lead = null
        if (lead === 'initials' && !cleanInitials) lead = null
        if (lead === 'number' && !cleanNumber) lead = null
        return {
          name: cleanName,
          initials: cleanInitials,
          number: cleanNumber,
          is_primary: v.is_primary,
          lead,
        }
      })
      .filter((v) => v.name || v.initials || v.number)
    if (cleanedVariants.length === 0) {
      setError('At least one name variant is required')
      return
    }
    if (!cleanedVariants.some((v) => v.is_primary)) {
      cleanedVariants[0].is_primary = true
    }
    const primary = cleanedVariants.find((v) => v.is_primary)!
    const primaryLead = primary.lead ?? (primary.name ? 'name' : primary.initials ? 'initials' : 'number')
    const submitName = ((primary as Record<string, unknown>)[primaryLead] as string | null ?? '').trim()
    if (!submitName) {
      setError('The primary variant must have a name, initials, or number')
      return
    }
    const payload = {
      universe_id: universeId,
      name: submitName,
      name_variants: cleanedVariants,
      bio: bio || null,
      status,
      alliance_id,
      gang_id,
      municipality_id,
      territory_ids: territoryIds,
    }
    try {
      if (isEdit) {
        const updated = await update.mutateAsync(payload)
        onSaved?.(updated as SetReadDetail)
        toast.success(`Updated "${name}"`)
      } else {
        await create.mutateAsync(payload)
        setVariants([emptyVariant(true)]); setBio(''); setStatus('ACTIVE')
        setAllianceId(ALLIANCE_NONE); setGangId(GANG_NONE); setMunicipalityId(MUNI_NONE); setTerritoryIds([])
        toast.success(`Created "${name}"`)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} set`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending
  const isReserved = !!initial?.is_reserved

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Set' : 'Add Set'}
        description={isEdit ? 'Update this gang set' : 'Create a new gang set in this universe'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {isReserved && (
            <div className="rounded border border-zinc-700 bg-zinc-900/50 px-3 py-2 text-xs text-zinc-400">
              System set — only the bio is editable. All other fields are locked.
            </div>
          )}
          {isReserved ? (
            <div className="space-y-1.5">
              <Label htmlFor="set-name">Name</Label>
              <Input id="set-name" value={name} readOnly disabled />
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Names *</Label>
                <span className="text-[11px] text-zinc-500">Primary is shown as the set's display name</span>
              </div>
              <div className="space-y-2">
                {variants.map((v, idx) => (
                  <div
                    key={idx}
                    className={`rounded-md border p-2 ${v.is_primary ? 'border-violet-700/60 bg-violet-950/20' : 'border-zinc-800 bg-zinc-950/40'}`}
                  >
                    <div className="grid grid-cols-3 gap-2">
                      <div className="space-y-1">
                        <Label className="text-[11px] text-zinc-500">Name</Label>
                        <Input
                          value={v.name ?? ''}
                          onChange={(e) =>
                            setVariants((prev) => prev.map((x, i) => (i === idx ? { ...x, name: e.target.value } : x)))
                          }
                          placeholder="Across The Ave"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px] text-zinc-500">Initials</Label>
                        <Input
                          value={v.initials ?? ''}
                          onChange={(e) =>
                            setVariants((prev) => prev.map((x, i) => (i === idx ? { ...x, initials: e.target.value } : x)))
                          }
                          placeholder="ATA"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px] text-zinc-500">Number</Label>
                        <Input
                          value={v.number ?? ''}
                          onChange={(e) =>
                            setVariants((prev) => prev.map((x, i) => (i === idx ? { ...x, number: e.target.value } : x)))
                          }
                          placeholder="282"
                        />
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between gap-3">
                      <label className="flex cursor-pointer items-center gap-1.5 text-xs text-zinc-400">
                        <input
                          type="radio"
                          name="set-variant-primary"
                          checked={v.is_primary}
                          onChange={() =>
                            setVariants((prev) => prev.map((x, i) => ({ ...x, is_primary: i === idx })))
                          }
                          className="h-3 w-3 accent-violet-500"
                        />
                        Primary
                      </label>
                      <div className="flex items-center gap-1.5 text-[11px] text-zinc-500">
                        <span>Show as</span>
                        {(['name', 'initials', 'number'] as const).map((slot) => {
                          const filled = !!v[slot]?.trim()
                          const active = (v.lead ?? (v.name?.trim() ? 'name' : v.initials?.trim() ? 'initials' : 'number')) === slot
                          return (
                            <button
                              key={slot}
                              type="button"
                              disabled={!filled}
                              onClick={() => setVariants((prev) => prev.map((x, i) => (i === idx ? { ...x, lead: slot } : x)))}
                              className={`rounded px-1.5 py-0.5 capitalize transition-colors ${
                                active && filled
                                  ? 'bg-violet-700/40 text-violet-200 ring-1 ring-violet-600/50'
                                  : filled
                                  ? 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                                  : 'cursor-not-allowed opacity-30'
                              }`}
                            >
                              {slot}
                            </button>
                          )
                        })}
                      </div>
                      {variants.length > 1 && (
                        <button
                          type="button"
                          onClick={() =>
                            setVariants((prev) => {
                              const next = prev.filter((_, i) => i !== idx)
                              if (!next.some((x) => x.is_primary) && next.length > 0) next[0].is_primary = true
                              return next
                            })
                          }
                          className="text-xs text-zinc-500 hover:text-red-400"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setVariants((prev) => [...prev, emptyVariant(false)])}
              >
                <Plus className="mr-1 h-3.5 w-3.5" />
                Add variant
              </Button>
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Status</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as SetStatus)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="EXTINCT">Extinct</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Gang</Label>
              <Select value={gangId} onValueChange={setGangId}>
                <SelectTrigger><SelectValue placeholder="No gang" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={GANG_NONE}>No gang</SelectItem>
                  {(gangsData?.items ?? []).map((g) => (
                    <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Alliance</Label>
              <Select value={allianceId} onValueChange={setAllianceId}>
                <SelectTrigger><SelectValue placeholder="No alliance" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALLIANCE_NONE}>No alliance</SelectItem>
                  {(alliancesData?.items ?? []).map((a) => (
                    <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Municipality</Label>
              <Select value={municipalityId} onValueChange={handleMunicipalityChange}>
                <SelectTrigger><SelectValue placeholder="No municipality" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={MUNI_NONE}>— None —</SelectItem>
                  {topLevelMunis.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {municipalityId !== MUNI_NONE && subDistricts.length === 0 && (
                <p className="text-[11px] text-zinc-600">
                  This municipality has no sub-districts.
                </p>
              )}
            </div>
          )}
          {!isReserved && municipalityId !== MUNI_NONE && subDistricts.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label>Sub-districts</Label>
                <span className="text-xs text-zinc-500 tabular-nums">
                  {territoryIds.length} of {subDistricts.length} selected
                </span>
              </div>
              <div className="max-h-48 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950/50">
                {subDistricts.map((m) => {
                  const checked = territoryIds.includes(m.id)
                  return (
                    <label
                      key={m.id}
                      className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-zinc-900"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleTerritory(m.id)}
                        className="h-3.5 w-3.5 accent-violet-500"
                      />
                      <span className={checked ? 'text-white' : 'text-zinc-400'}>
                        {m.name}
                      </span>
                    </label>
                  )
                })}
              </div>
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="set-bio">Bio</Label>
            <Textarea id="set-bio" value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Background info…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Set'}
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

// ─── Lazy edit sheet (fetches full set on open) ───────────────────────────────

function EditSetSheet({ setId, universeId, open, onClose }: {
  setId: string; universeId: string; open: boolean; onClose: () => void
}) {
  const { data: set } = useSet(setId, universeId)
  if (!set) {
    return (
      <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
        <SheetContent title="Edit Set" description="Loading…">
          <div className="space-y-3 pt-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        </SheetContent>
      </Sheet>
    )
  }
  return <SetFormSheet universeId={universeId} open={open} onClose={onClose} initial={set} />
}

// ─── Small UI bits ────────────────────────────────────────────────────────────

type StatusFilter = 'ALL' | 'ACTIVE' | 'EXTINCT'

function StatusTabs({ value, onChange, counts }: {
  value: StatusFilter
  onChange: (v: StatusFilter) => void
  counts: Record<StatusFilter, number>
}) {
  const tabs: { key: StatusFilter; label: string }[] = [
    { key: 'ALL', label: 'All' },
    { key: 'ACTIVE', label: 'Active' },
    { key: 'EXTINCT', label: 'Extinct' },
  ]
  return (
    <div className="flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1">
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          aria-pressed={value === key}
          className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
            value === key ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {label}
          <span className={`tabular-nums ${value === key ? 'text-zinc-300' : 'text-zinc-600'}`}>
            {counts[key]}
          </span>
        </button>
      ))}
    </div>
  )
}

function SortHeader({ label, col, sort, order, onSort, align = 'left' }: {
  label: string; col: SortKey; sort: SortKey; order: 'asc' | 'desc'
  onSort: (k: SortKey) => void; align?: 'left' | 'right'
}) {
  const sorted = sort === col
  return (
    <th
      className={`px-4 py-2.5 ${align === 'right' ? 'text-right' : 'text-left'}`}
      scope="col"
      aria-sort={sorted ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <button
        onClick={() => onSort(col)}
        className={`inline-flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white ${
          align === 'right' ? 'ml-auto' : ''
        }`}
      >
        {label}
        <span className="text-zinc-600" aria-hidden>{sorted ? (order === 'asc' ? '↑' : '↓') : '↕'}</span>
      </button>
    </th>
  )
}

function StatTile({ label, value, active, onClick, accent }: {
  label: string
  value: string | number
  active?: boolean
  onClick?: () => void
  accent?: 'green' | 'zinc' | 'blue' | 'violet'
}) {
  const ring = active
    ? 'ring-1 ring-violet-600/60 bg-violet-950/30'
    : 'hover:bg-zinc-900/70'
  const accentColor =
    accent === 'green' ? 'text-emerald-400'
      : accent === 'blue' ? 'text-blue-400'
      : accent === 'violet' ? 'text-violet-400'
      : 'text-zinc-200'
  const Comp = onClick ? 'button' : 'div'
  return (
    <Comp
      onClick={onClick}
      className={`flex flex-1 min-w-0 flex-col items-start rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2 text-left transition-colors ${ring}`}
    >
      <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">{label}</span>
      <span className={`mt-0.5 text-lg font-bold tabular-nums ${accentColor}`}>{value}</span>
    </Comp>
  )
}

function GangPill({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-emerald-950/50 px-2 py-0.5 text-[11px] font-medium text-emerald-300 ring-1 ring-emerald-800/50">
      {name}
    </span>
  )
}

function AlliancePill({ name, slug, id }: { name: string; slug: string | null; id: string }) {
  return (
    <Link
      to="/alliances/$id"
      params={{ id: slug ?? id }}
      onClick={(e) => e.stopPropagation()}
      className="inline-flex items-center rounded-full bg-blue-950/60 px-2 py-0.5 text-[11px] font-medium text-blue-300 ring-1 ring-blue-800/50 hover:ring-blue-600 transition-colors"
    >
      {name}
    </Link>
  )
}

function MunicipalityPill({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-zinc-800/80 px-2 py-0.5 text-[11px] font-medium text-zinc-300 ring-1 ring-zinc-700">
      <MapPin className="h-2.5 w-2.5" aria-hidden />
      {name}
    </span>
  )
}

function MemberCount({ n, large = false }: { n: number; large?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 tabular-nums ${large ? 'text-sm text-zinc-200' : 'text-xs text-zinc-400'}`}>
      <Users className={large ? 'h-3.5 w-3.5' : 'h-3 w-3'} aria-hidden />
      {n}
    </span>
  )
}

// ─── Row actions ──────────────────────────────────────────────────────────────

function RowActions({ set, onEdit, onDuplicate, onDelete }: {
  set: SetListItem
  onEdit: () => void
  onDuplicate: () => void
  onDelete: () => void
}) {
  if (set.is_reserved) {
    return (
      <button
        onClick={onEdit}
        aria-label={`Edit ${set.name}`}
        className="rounded p-1.5 text-zinc-600 hover:bg-zinc-800 hover:text-zinc-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
      >
        <Pencil className="h-3.5 w-3.5" />
      </button>
    )
  }
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label={`Actions for ${set.name}`}
          onClick={(e) => e.stopPropagation()}
          className="rounded p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
        >
          <MoreVertical className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onSelect={onEdit}>
          <Pencil className="mr-2 h-3.5 w-3.5" />Edit
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={onDuplicate}>
          <Copy className="mr-2 h-3.5 w-3.5" />Duplicate
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onDelete} className="text-red-400 focus:bg-red-950/40 focus:text-red-300">
          <Trash2 className="mr-2 h-3.5 w-3.5" />Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ─── Card view ────────────────────────────────────────────────────────────────

function SetCard({ set, isSelected, onToggleSelect, onEdit, onDuplicate, onDelete }: {
  set: SetListItem
  isSelected: boolean
  onToggleSelect: () => void
  onEdit: () => void
  onDuplicate: () => void
  onDelete: () => void
}) {
  const linkId = set.slug ?? set.id
  const aka = nonPrimaryVariantsText(set.name_variants)
  return (
    <div className={`group relative flex flex-col overflow-hidden rounded-lg border bg-zinc-900/40 transition-colors ${
      isSelected ? 'border-violet-700/70 bg-violet-950/20' : 'border-zinc-800 hover:border-zinc-700'
    }`}>
      <Link to="/sets/$id" params={{ id: linkId }} className="flex flex-col">
        {/* Header band: photo or color block */}
        <div className="relative h-24 w-full overflow-hidden bg-zinc-950">
          {set.primary_photo_thumb_url ? (
            <img src={set.primary_photo_thumb_url} alt="" className="h-full w-full object-cover opacity-70" loading="lazy" />
          ) : (
            <div className="h-full w-full" style={setColorStyle(set.name)} aria-hidden />
          )}
          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-zinc-950 to-transparent p-3">
            <div className="flex items-center gap-2">
              <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} isReserved={set.is_reserved} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">
                  {set.name}
                </p>
                {aka && <p className="truncate text-[11px] text-zinc-400">{aka}</p>}
              </div>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5 p-3">
          {set.gang_name && <GangPill name={set.gang_name} />}
          {set.alliance_id && set.alliance_name && (
            <AlliancePill name={set.alliance_name} slug={null} id={set.alliance_id} />
          )}
          {set.municipality_name && <MunicipalityPill name={set.municipality_name} />}
          {!set.gang_name && !set.alliance_name && !set.municipality_name && (
            <span className="text-[11px] text-zinc-600">No affiliations</span>
          )}
        </div>
        <div className="flex items-center justify-between border-t border-zinc-800/80 px-3 py-2">
          <MemberCount n={set.member_count} large />
          <SetStatusBadge status={set.status} />
        </div>
      </Link>
      {!set.is_reserved && (
        <div className="absolute right-2 top-2 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
          <button
            onClick={(e) => { e.stopPropagation(); onToggleSelect() }}
            aria-label={`Select ${set.name}`}
            className={`rounded border px-1.5 py-1 text-[10px] font-medium uppercase tracking-wide transition-colors ${
              isSelected
                ? 'border-violet-500 bg-violet-700 text-white'
                : 'border-zinc-700 bg-zinc-900/80 text-zinc-300 hover:bg-zinc-800'
            }`}
          >
            {isSelected ? 'Selected' : 'Select'}
          </button>
          <div onClick={(e) => e.stopPropagation()}>
            <RowActions set={set} onEdit={onEdit} onDuplicate={onDuplicate} onDelete={onDelete} />
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

// ─── Page ─────────────────────────────────────────────────────────────────────

const ALL_SENTINEL = '__all__'
const NONE_SENTINEL = 'none'

function SetsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const search = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })

  // Local input state (debounced into the URL)
  const [qInput, setQInput] = useState(search.q ?? '')
  const debouncedQ = useDebounce(qInput, 250)

  // Push debounced search into URL once it stabilizes (and reset to page 1).
  useEffect(() => {
    const next = debouncedQ.trim() ? debouncedQ.trim() : undefined
    if (next === (search.q ?? undefined)) return
    navigate({ search: (prev) => ({ ...prev, q: next, page: undefined }) })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ])

  // Keep the input in sync if the URL changes externally (back/forward).
  useEffect(() => {
    if ((search.q ?? '') !== qInput) setQInput(search.q ?? '')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search.q])

  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null)
  const [deletingSet, setDeletingSet] = useState<SetListItem | null>(null)
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [selected, setSelected] = useState<Set<UUID>>(new Set())

  // Settings — persisted defaults via URL (sharable). Effective values:
  const view: ViewMode = search.view ?? 'table'
  const density: Density = search.density ?? 'compact'
  const sort: SortKey = search.sort ?? 'name'
  const order: 'asc' | 'desc' = search.order ?? 'asc'
  const pageSize = search.size ?? 20
  const page = search.page ?? 1
  const offset = (page - 1) * pageSize

  const statusFilter: StatusFilter = (search.status as StatusFilter | undefined) ?? 'ALL'
  const allianceFilter = search.alliance ?? ALL_SENTINEL
  const gangFilter = search.gang ?? ALL_SENTINEL
  const muniFilter = search.muni ?? ALL_SENTINEL
  const hasFilters = !!(search.status || search.alliance || search.gang || search.muni || search.q)

  // Mobile-only forces card view; we just compute it for layout decisions.
  const [isMobile, setIsMobile] = useState(() => typeof window !== 'undefined' && window.innerWidth < 640)
  useEffect(() => {
    if (typeof window === 'undefined') return
    const onResize = () => setIsMobile(window.innerWidth < 640)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])
  const effectiveView: ViewMode = isMobile ? 'cards' : view

  // Build list params for the server.
  const listParams: SetsListParams = {
    offset,
    limit: pageSize,
    q: debouncedQ.trim() || undefined,
    status: search.status,
    alliance_id: allianceFilter !== ALL_SENTINEL ? allianceFilter : undefined,
    gang_id: gangFilter !== ALL_SENTINEL ? gangFilter : undefined,
    municipality_id: muniFilter !== ALL_SENTINEL ? muniFilter : undefined,
    sort,
    order,
  }

  const { data, isLoading } = useSets(universe?.id ?? null, listParams)
  const { data: alliancesData } = useAlliances(universe?.id ?? null)
  const { data: gangsData } = useGangs(universe?.id ?? null)
  const { data: munisData } = useMunicipalities(universe?.id ?? null)
  const deleteSet = useDeleteSet(universe?.id ?? '')

  // Unfiltered totals for the KPI strip — separate query, cached, light.
  // Fetched without any filters so the KPIs reflect the whole universe.
  const { data: kpiData } = useSets(universe?.id ?? null, { limit: 200 })

  if (!universe) return <NoUniverse />

  const rawItems = data?.items ?? []
  const reservedSets = rawItems.filter((s) => s.is_reserved)
  const items = rawItems.filter((s) => !s.is_reserved)
  const total = data?.total ?? 0
  const selectableIds = items.filter((s) => !s.is_reserved).map((s) => s.id)
  const allSelected = selectableIds.length > 0 && selectableIds.every((id) => selected.has(id))

  // KPI stats over the universe (excluding reserved sets).
  const allKpiSets = (kpiData?.items ?? []).filter((s) => !s.is_reserved)
  const kpiActive = allKpiSets.filter((s) => s.status === 'ACTIVE').length
  const kpiExtinct = allKpiSets.filter((s) => s.status === 'EXTINCT').length
  const kpiInAlliance = allKpiSets.filter((s) => !!s.alliance_id).length
  const totalMembers = allKpiSets.reduce((sum, s) => sum + (s.member_count ?? 0), 0)
  const avgCrew = allKpiSets.length ? Math.round(totalMembers / allKpiSets.length) : 0

  function patchSearch(patch: Partial<SetsSearch>) {
    navigate({ search: (prev) => {
      const next: SetsSearch = { ...prev, ...patch }
      // Reset to page 1 when filters or sort change (but NOT for view/density/page/size itself).
      const filterKeys: (keyof SetsSearch)[] = ['q', 'status', 'alliance', 'gang', 'muni', 'sort', 'order', 'size']
      if (filterKeys.some((k) => k in patch)) next.page = undefined
      // Strip undefineds to keep URLs clean.
      for (const k of Object.keys(next) as (keyof SetsSearch)[]) {
        if (next[k] === undefined || next[k] === ALL_SENTINEL) delete next[k]
      }
      return next
    } })
  }

  function setStatusFilter(v: StatusFilter) {
    patchSearch({ status: v === 'ALL' ? undefined : v })
  }
  function toggleSort(key: SortKey) {
    if (sort === key) patchSearch({ order: order === 'asc' ? 'desc' : 'asc' })
    else patchSearch({ sort: key, order: 'asc' })
  }
  function clearAllFilters() {
    setQInput('')
    navigate({ search: (prev) => ({ view: prev.view, density: prev.density, size: prev.size }) })
  }

  function toggleSelectSet(id: UUID) {
    setSelected((prev) => {
      const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next
    })
  }

  async function bulkDeleteSets() {
    if (selected.size === 0) return
    const ids = Array.from(selected)
    setBulkDeleting(true)
    try {
      await Promise.all(ids.map((id) => deleteSet.mutateAsync(id)))
      toast.success(`Deleted ${ids.length} set${ids.length === 1 ? '' : 's'}`)
      setSelected(new Set())
      setConfirmingBulkDelete(false)
    } finally {
      setBulkDeleting(false)
    }
  }

  async function deleteSingleSet(s: SetListItem) {
    try {
      await deleteSet.mutateAsync(s.id)
      toast.success(`Deleted "${s.name}"`)
    } finally {
      setDeletingSet(null)
    }
  }

  const allianceOptions = alliancesData?.items ?? []
  const gangOptions = gangsData?.items ?? []
  const muniOptions = (munisData?.items ?? []).filter((m) => !m.parent_id)
  const allianceLabel = (id: string) =>
    id === NONE_SENTINEL ? 'No alliance' : allianceOptions.find((a) => a.id === id)?.name ?? '?'
  const gangLabel = (id: string) =>
    id === NONE_SENTINEL ? 'No gang' : gangOptions.find((g) => g.id === id)?.name ?? '?'
  const muniLabel = (id: string) =>
    id === NONE_SENTINEL ? 'No municipality' : muniOptions.find((m) => m.id === id)?.name ?? '?'

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const editingSetForDuplication = duplicatingId
    ? rawItems.find((s) => s.id === duplicatingId) ?? null
    : null

  return (
    <div>
      <PageHeader
        title="Sets"
        description={
          isLoading ? undefined :
          total === 0 ? 'No sets yet' :
          hasFilters
            ? `${total} match${total === 1 ? '' : 'es'}`
            : `${kpiActive} active · ${kpiExtinct} extinct`
        }
        action={
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus className="mr-1.5 h-4 w-4" />Add Set
          </Button>
        }
      />

      {/* KPI strip */}
      {allKpiSets.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          <StatTile
            label="Active"
            value={kpiActive}
            accent="green"
            active={statusFilter === 'ACTIVE'}
            onClick={() => setStatusFilter(statusFilter === 'ACTIVE' ? 'ALL' : 'ACTIVE')}
          />
          <StatTile
            label="Extinct"
            value={kpiExtinct}
            accent="zinc"
            active={statusFilter === 'EXTINCT'}
            onClick={() => setStatusFilter(statusFilter === 'EXTINCT' ? 'ALL' : 'EXTINCT')}
          />
          <StatTile
            label="In an alliance"
            value={kpiInAlliance}
            accent="blue"
          />
          <StatTile
            label="Avg crew size"
            value={avgCrew}
            accent="violet"
          />
        </div>
      )}

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative min-w-48 flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input
            className="pl-8"
            placeholder="Search sets…"
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
          />
        </div>

        <StatusTabs
          value={statusFilter}
          onChange={setStatusFilter}
          counts={{ ALL: allKpiSets.length, ACTIVE: kpiActive, EXTINCT: kpiExtinct }}
        />

        {/* Alliance */}
        <Select
          value={allianceFilter}
          onValueChange={(v) => patchSearch({ alliance: v === ALL_SENTINEL ? undefined : v })}
        >
          <SelectTrigger className="h-8 w-auto min-w-32 text-xs">
            <SelectValue placeholder="Alliance" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_SENTINEL}>All alliances</SelectItem>
            <SelectItem value={NONE_SENTINEL}>No alliance</SelectItem>
            {allianceOptions.map((a) => (
              <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Gang */}
        <Select
          value={gangFilter}
          onValueChange={(v) => patchSearch({ gang: v === ALL_SENTINEL ? undefined : v })}
        >
          <SelectTrigger className="h-8 w-auto min-w-28 text-xs">
            <SelectValue placeholder="Gang" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_SENTINEL}>All gangs</SelectItem>
            <SelectItem value={NONE_SENTINEL}>No gang</SelectItem>
            {gangOptions.map((g) => (
              <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Municipality */}
        <Select
          value={muniFilter}
          onValueChange={(v) => patchSearch({ muni: v === ALL_SENTINEL ? undefined : v })}
        >
          <SelectTrigger className="h-8 w-auto min-w-32 text-xs">
            <SelectValue placeholder="Municipality" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_SENTINEL}>All municipalities</SelectItem>
            <SelectItem value={NONE_SENTINEL}>No municipality</SelectItem>
            {muniOptions.map((m) => (
              <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="ml-auto flex items-center gap-2">
          {/* Sort (cards mode only — table has sortable headers) */}
          {effectiveView === 'cards' && (
            <Select
              value={`${sort}:${order}`}
              onValueChange={(v) => {
                const [s, o] = v.split(':') as [SortKey, 'asc' | 'desc']
                patchSearch({ sort: s, order: o })
              }}
            >
              <SelectTrigger className="h-8 w-auto min-w-32 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name:asc">Name A→Z</SelectItem>
                <SelectItem value="name:desc">Name Z→A</SelectItem>
                <SelectItem value="member_count:desc">Members ↓</SelectItem>
                <SelectItem value="member_count:asc">Members ↑</SelectItem>
                <SelectItem value="updated_at:desc">Recently updated</SelectItem>
                <SelectItem value="created_at:desc">Recently created</SelectItem>
              </SelectContent>
            </Select>
          )}

          {/* View toggle (hidden on mobile — cards forced) */}
          {!isMobile && (
            <div className="flex items-center rounded-lg border border-zinc-800 bg-zinc-900/50 p-0.5">
              <button
                onClick={() => patchSearch({ view: 'table' })}
                aria-label="Table view"
                aria-pressed={view === 'table'}
                className={`rounded-md p-1.5 transition-colors ${view === 'table' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
              >
                <Rows3 className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => patchSearch({ view: 'cards' })}
                aria-label="Card view"
                aria-pressed={view === 'cards'}
                className={`rounded-md p-1.5 transition-colors ${view === 'cards' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
              </button>
            </div>
          )}

          {/* Density (table view only) */}
          {effectiveView === 'table' && (
            <Select
              value={density}
              onValueChange={(v) => patchSearch({ density: v as Density })}
            >
              <SelectTrigger className="h-8 w-auto min-w-24 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="comfortable">Comfortable</SelectItem>
                <SelectItem value="compact">Compact</SelectItem>
              </SelectContent>
            </Select>
          )}

          <Button
            variant="outline" size="sm"
            onClick={() => {
              const date = new Date().toISOString().slice(0, 10)
              const url = `/sets/?${new URLSearchParams({ universe_id: universe.id, format: 'csv' }).toString()}`
              downloadCsv(url, `sets-${universe.slug}-${date}.csv`)
            }}
          >
            <Download className="mr-1.5 h-3.5 w-3.5" />Export
          </Button>
        </div>
      </div>

      {/* Active filter chips */}
      {hasFilters && (
        <div className="mb-3 flex flex-wrap items-center gap-1.5" aria-live="polite">
          {search.q && (
            <FilterChip label={`Search: "${search.q}"`} onClear={() => { setQInput(''); patchSearch({ q: undefined }) }} />
          )}
          {search.status && (
            <FilterChip label={`Status: ${search.status === 'ACTIVE' ? 'Active' : 'Extinct'}`} onClear={() => patchSearch({ status: undefined })} />
          )}
          {search.alliance && (
            <FilterChip label={`Alliance: ${allianceLabel(search.alliance)}`} onClear={() => patchSearch({ alliance: undefined })} />
          )}
          {search.gang && (
            <FilterChip label={`Gang: ${gangLabel(search.gang)}`} onClear={() => patchSearch({ gang: undefined })} />
          )}
          {search.muni && (
            <FilterChip label={`Municipality: ${muniLabel(search.muni)}`} onClear={() => patchSearch({ muni: undefined })} />
          )}
          <button
            onClick={clearAllFilters}
            className="text-xs text-zinc-500 hover:text-zinc-200 underline-offset-4 hover:underline"
          >
            Clear all
          </button>
        </div>
      )}

      {/* System sets row (reserved) */}
      {reservedSets.length > 0 && !hasFilters && (
        <div className="mb-4 flex items-center gap-2">
          <span className="text-[11px] font-medium uppercase tracking-wider text-zinc-600">System</span>
          {reservedSets.map((s) => (
            <Link
              key={s.id}
              to="/sets/$id"
              params={{ id: s.slug ?? s.id }}
              className="inline-flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-900/50 px-3 py-1 text-xs text-zinc-400 hover:border-zinc-500 hover:text-zinc-200 transition-colors"
            >
              <SetAvatar name={s.name} thumbUrl={s.primary_photo_thumb_url} size="sm" isReserved={s.is_reserved} />
              {s.name}
            </Link>
          ))}
        </div>
      )}

      {/* List body */}
      {effectiveView === 'cards' ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {isLoading
            ? Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/40">
                  <Skeleton className="h-24 w-full rounded-none" />
                  <div className="space-y-2 p-3">
                    <Skeleton className="h-3 w-32" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                  <div className="border-t border-zinc-800 px-3 py-2">
                    <Skeleton className="h-4 w-16" />
                  </div>
                </div>
              ))
            : items.length === 0
              ? (
                <div className="col-span-full">
                  <EmptyState
                    icon={Shield}
                    title={hasFilters ? 'No sets match your filters' : 'No sets yet'}
                    description={hasFilters ? undefined : 'Create a set to start tracking a crew.'}
                    action={hasFilters
                      ? <Button size="sm" variant="outline" onClick={clearAllFilters}>Clear filters</Button>
                      : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Create the first set</Button>
                    }
                  />
                </div>
              )
              : items.map((set) => (
                <SetCard
                  key={set.id}
                  set={set}
                  isSelected={selected.has(set.id)}
                  onToggleSelect={() => toggleSelectSet(set.id)}
                  onEdit={() => setEditingId(set.id)}
                  onDuplicate={() => setDuplicatingId(set.id)}
                  onDelete={() => setDeletingSet(set)}
                />
              ))
          }
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-zinc-800">
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10 bg-zinc-900/90 backdrop-blur">
              <tr className="border-b border-zinc-800">
                <th className="w-10 px-3 py-2.5" scope="col">
                  <input
                    type="checkbox"
                    aria-label="Select all sets"
                    checked={allSelected}
                    onChange={() => setSelected(allSelected ? new Set() : new Set(selectableIds))}
                    className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                  />
                </th>
                <SortHeader label="Set" col="name" sort={sort} order={order} onSort={toggleSort} />
                <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Gang</th>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Alliance</th>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Municipality</th>
                <SortHeader label="Members" col="member_count" sort={sort} order={order} onSort={toggleSort} align="right" />
                <SortHeader label="Status" col="status" sort={sort} order={order} onSort={toggleSort} />
                <th className="w-8" aria-label="Actions" />
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={8} height={density === 'compact' ? 44 : 56} />)
                : items.map((set) => {
                    const linkId = set.slug ?? set.id
                    const isSelected = selected.has(set.id)
                    const padY = density === 'compact' ? 'py-1.5' : 'py-3'
                    return (
                      <tr key={set.id} className={`group hover:bg-zinc-900/50 transition-colors ${isSelected ? 'bg-violet-950/20' : ''}`}>
                        <td className={`px-3 ${padY}`}>
                          <input
                            type="checkbox"
                            aria-label={`Select ${set.name}`}
                            checked={isSelected}
                            disabled={set.is_reserved}
                            onChange={() => toggleSelectSet(set.id)}
                            className="rounded border-zinc-700 bg-zinc-900 accent-violet-600 disabled:cursor-not-allowed disabled:opacity-30"
                          />
                        </td>
                        <td className="p-0">
                          <Link to="/sets/$id" params={{ id: linkId }} className={`flex items-center gap-3 px-4 ${padY}`}>
                            <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} isReserved={set.is_reserved} />
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="truncate font-medium text-white group-hover:text-violet-400 transition-colors">{set.name}</p>
                                {set.is_reserved && (
                                  <span className="rounded border border-zinc-700 bg-zinc-800/60 px-1.5 py-px text-[9px] font-medium uppercase tracking-wider text-zinc-500">
                                    System
                                  </span>
                                )}
                              </div>
                              {density === 'comfortable' && (() => {
                                const aka = nonPrimaryVariantsText(set.name_variants)
                                return aka ? <p className="truncate text-xs text-zinc-500">{aka}</p> : null
                              })()}
                            </div>
                          </Link>
                        </td>
                        <td className={`px-4 ${padY}`}>
                          {set.gang_name ? <GangPill name={set.gang_name} /> : <span className="text-xs text-zinc-700">—</span>}
                        </td>
                        <td className={`px-4 ${padY}`}>
                          {set.alliance_id && set.alliance_name ? (
                            <AlliancePill name={set.alliance_name} slug={null} id={set.alliance_id} />
                          ) : <span className="text-xs text-zinc-700">—</span>}
                        </td>
                        <td className={`px-4 ${padY}`}>
                          {set.municipality_name ? <MunicipalityPill name={set.municipality_name} /> : <span className="text-xs text-zinc-700">—</span>}
                        </td>
                        <td className={`px-4 ${padY} text-right`}>
                          <MemberCount n={set.member_count} />
                        </td>
                        <td className={`px-4 ${padY}`}>
                          <SetStatusBadge status={set.status} />
                        </td>
                        <td className={`pr-3 ${padY}`}>
                          <RowActions
                            set={set}
                            onEdit={() => setEditingId(set.id)}
                            onDuplicate={() => setDuplicatingId(set.id)}
                            onDelete={() => setDeletingSet(set)}
                          />
                        </td>
                      </tr>
                    )
                  })}
              {!isLoading && items.length === 0 && (
                <tr>
                  <td colSpan={8}>
                    <EmptyState
                      icon={Shield}
                      title={hasFilters ? 'No sets match your filters' : 'No sets yet'}
                      description={hasFilters ? undefined : 'Create a set to start tracking a crew.'}
                      action={hasFilters
                        ? <Button size="sm" variant="outline" onClick={clearAllFilters}>Clear filters</Button>
                        : <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Create the first set</Button>
                      }
                    />
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > 0 && (
        <nav className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-zinc-400" aria-label="Pagination">
          <div className="flex items-center gap-3">
            <span aria-live="polite">
              Showing <span className="text-zinc-200 tabular-nums">{offset + 1}</span>–<span className="text-zinc-200 tabular-nums">{Math.min(offset + pageSize, total)}</span> of{' '}
              <span className="text-zinc-200 tabular-nums">{total}</span>
              {hasFilters && <span className="ml-1 text-zinc-500">(filtered)</span>}
            </span>
            <Select value={String(pageSize)} onValueChange={(v) => patchSearch({ size: Number(v) })}>
              <SelectTrigger className="h-7 w-auto text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="20">20 / page</SelectItem>
                <SelectItem value="50">50 / page</SelectItem>
                <SelectItem value="100">100 / page</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-500 tabular-nums">Page {page} of {totalPages}</span>
            <Button
              variant="outline" size="sm"
              aria-disabled={page === 1} disabled={page === 1}
              onClick={() => patchSearch({ page: page - 1 > 1 ? page - 1 : undefined })}
            >Prev</Button>
            <Button
              variant="outline" size="sm"
              aria-disabled={page >= totalPages} disabled={page >= totalPages}
              onClick={() => patchSearch({ page: page + 1 })}
            >Next</Button>
          </div>
        </nav>
      )}

      <SetFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingId && (
        <EditSetSheet
          setId={editingId}
          universeId={universe.id}
          open={!!editingId}
          onClose={() => setEditingId(null)}
        />
      )}
      {duplicatingId && (
        <DuplicateSetSheet
          key={`dup-${duplicatingId}`}
          setId={duplicatingId}
          universeId={universe.id}
          open={!!duplicatingId}
          onClose={() => setDuplicatingId(null)}
          fallback={editingSetForDuplication}
        />
      )}

      <BulkActionBar count={selected.size} label="set" onClear={() => setSelected(new Set())}>
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
        title={`Delete ${selected.size} set${selected.size === 1 ? '' : 's'}?`}
        description="This cannot be undone. Members in these sets will be unassigned, and friend/enemy edges will be removed."
        confirmLabel="Delete"
        destructive
        pending={bulkDeleting}
        onConfirm={bulkDeleteSets}
        onCancel={() => setConfirmingBulkDelete(false)}
      />

      <ConfirmDialog
        open={!!deletingSet}
        title={`Delete "${deletingSet?.name ?? ''}"?`}
        description="This cannot be undone. Members in this set will be unassigned, and friend/enemy edges will be removed."
        confirmLabel="Delete"
        destructive
        pending={deleteSet.isPending}
        onConfirm={() => deletingSet && deleteSingleSet(deletingSet)}
        onCancel={() => setDeletingSet(null)}
      />
    </div>
  )
}

// ─── Filter chip ──────────────────────────────────────────────────────────────

function FilterChip({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <button
      onClick={onClear}
      className="group inline-flex items-center gap-1 rounded-full border border-zinc-700 bg-zinc-900/60 px-2.5 py-1 text-xs text-zinc-300 transition-colors hover:border-zinc-500 hover:text-white"
    >
      <span>{label}</span>
      <X className="h-3 w-3 text-zinc-500 group-hover:text-zinc-200" aria-hidden />
    </button>
  )
}

// ─── Duplicate sheet (lazy-fetches full set and seeds copyFrom) ───────────────

function DuplicateSetSheet({ setId, universeId, open, onClose, fallback }: {
  setId: string; universeId: string; open: boolean; onClose: () => void; fallback: SetListItem | null
}) {
  const { data: set } = useSet(setId, universeId)
  if (!set) {
    if (fallback) {
      // Render with a minimal fallback so the sheet shows something instantly.
      return (
        <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
          <SheetContent title="Duplicate Set" description="Loading…">
            <div className="space-y-3 pt-2">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
            </div>
          </SheetContent>
        </Sheet>
      )
    }
    return null
  }
  return <SetFormSheet universeId={universeId} open={open} onClose={onClose} copyFrom={set} />
}
