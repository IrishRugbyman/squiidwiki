import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Pencil, Plus, Search, Shield, Trash2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { SetStatusToggle } from '@/components/StatusToggle'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useAlliances, useCreateSet, useDeleteSet, useMunicipalities, useSet, useSets, useSetSearch, useUpdateSet, useUpdateSetStatus } from '@/lib/queries'
import { BulkActionBar } from '@/components/BulkActionBar'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import { useDebounce } from '@/hooks/useDebounce'
import { EmptyState } from '@/components/EmptyState'
import { TableRowSkeleton } from '@/components/skeletons'
import type { SetReadDetail, SetStatus, UUID } from '@/lib/types'

export const Route = createFileRoute('/_app/sets/')({
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

export function SetAvatar({ name, thumbUrl, size = 'md' }: { name: string; thumbUrl?: string | null; size?: 'sm' | 'md' }) {
  const [imgError, setImgError] = useState(false)
  const sz = size === 'sm' ? 'h-7 w-7 text-xs' : 'h-8 w-8 text-sm'
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

export function SetFormSheet({ universeId, open, onClose, initial, onSaved, defaultAllianceId, defaultMunicipalityId, copyFrom }: SetFormProps) {
  const create = useCreateSet()
  const update = useUpdateSet(initial?.id ?? '')
  const { data: alliancesData } = useAlliances(universeId)
  const { data: munisData } = useMunicipalities(universeId)
  const isEdit = !!initial

  const [name, setName] = useState(initial?.name ?? copyFrom?.name ?? '')
  const [aliases, setAliases] = useState(initial?.aliases?.join(', ') ?? copyFrom?.aliases?.join(', ') ?? '')
  const [bio, setBio] = useState(initial?.bio ?? copyFrom?.bio ?? '')
  const [status, setStatus] = useState<SetStatus>(initial?.status ?? copyFrom?.status ?? 'ACTIVE')
  const [allianceId, setAllianceId] = useState<string>(initial?.alliance_id ?? copyFrom?.alliance_id ?? defaultAllianceId ?? ALLIANCE_NONE)
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
    const municipality_id = municipalityId === MUNI_NONE ? null : municipalityId
    const aliasList = aliases.split(',').map((s) => s.trim()).filter(Boolean)
    const aliasesPayload = aliasList.length > 0 ? aliasList : null
    const payload = {
      universe_id: universeId,
      name,
      aliases: aliasesPayload,
      bio: bio || null,
      status,
      alliance_id,
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
        setName(''); setAliases(''); setBio(''); setStatus('ACTIVE')
        setAllianceId(ALLIANCE_NONE); setMunicipalityId(MUNI_NONE); setTerritoryIds([])
        toast.success(`Created "${name}"`)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} set`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Set' : 'Add Set'}
        description={isEdit ? 'Update this gang set' : 'Create a new gang set in this universe'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="set-name">Name *</Label>
            <Input id="set-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Terror Town" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="set-aliases">Aliases <span className="text-zinc-600">(comma-separated)</span></Label>
            <Input id="set-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. GG, Ghost" />
          </div>
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
          {municipalityId !== MUNI_NONE && subDistricts.length > 0 && (
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

// ─── Status filter ────────────────────────────────────────────────────────────

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
          className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
            value === key
              ? 'bg-zinc-700 text-white'
              : 'text-zinc-500 hover:text-zinc-300'
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

// ─── Sort header ──────────────────────────────────────────────────────────────

type SortKey = 'name' | 'status'

function SortHeader({ label, col, sortKey, sortDir, onSort }: {
  label: string; col: SortKey; sortKey: SortKey | null; sortDir: 'asc' | 'desc'; onSort: (k: SortKey) => void
}) {
  const sorted = sortKey === col
  return (
    <th
      className="px-4 py-2.5 text-left"
      scope="col"
      aria-sort={sorted ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <button
        onClick={() => onSort(col)}
        className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white"
      >
        {label}
        <span className="text-zinc-600" aria-hidden>
          {sorted ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
        </span>
      </button>
    </th>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function SetsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')
  const [allianceFilter, setAllianceFilter] = useState<string>('ALL')
  const [sortKey, setSortKey] = useState<SortKey | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [selected, setSelected] = useState<Set<UUID>>(new Set())
  const [confirmingBulkDelete, setConfirmingBulkDelete] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const PAGE = 20

  const debouncedQ = useDebounce(q, 250)
  const statusUpdate = useUpdateSetStatus(universe?.id ?? '')
  const deleteSet = useDeleteSet(universe?.id ?? '')
  const { data, isLoading } = useSets(universe?.id ?? null, offset)
  const { data: searchResults, isLoading: searchLoading } = useSetSearch(universe?.id ?? null, debouncedQ)
  const { data: alliancesData } = useAlliances(universe?.id ?? null)

  const isSearching = debouncedQ.length >= 2
  const rawItems = isSearching ? (searchResults ?? []) : (data?.items ?? [])

  const items = useMemo(() => {
    let filtered = rawItems
    if (statusFilter !== 'ALL') filtered = filtered.filter((s) => s.status === statusFilter)
    if (allianceFilter !== 'ALL') filtered = filtered.filter((s) =>
      allianceFilter === 'NONE' ? !s.alliance_id : s.alliance_id === allianceFilter
    )
    if (!sortKey) return filtered
    return [...filtered].sort((a, b) => {
      const av = String(a[sortKey] ?? '')
      const bv = String(b[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [rawItems, statusFilter, allianceFilter, sortKey, sortDir])

  if (!universe) return <NoUniverse />

  const allianceMap: Record<string, { name: string; slug: string | null }> = {}
  for (const a of alliancesData?.items ?? []) allianceMap[a.id] = { name: a.name, slug: a.slug }

  const total = data?.total ?? 0
  const listLoading = isSearching ? searchLoading : isLoading

  // Status counts over all loaded items (not filtered)
  const allItems = data?.items ?? []
  const statusCounts: Record<StatusFilter, number> = {
    ALL: allItems.length,
    ACTIVE: allItems.filter((s) => s.status === 'ACTIVE').length,
    EXTINCT: allItems.filter((s) => s.status === 'EXTINCT').length,
  }

  // Unique alliances present in the list
  const alliancesInList = Array.from(
    new Set(allItems.map((s) => s.alliance_id).filter(Boolean) as string[])
  )

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  function toggleSelectSet(id: UUID) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
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
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Bulk delete failed')
    } finally {
      setBulkDeleting(false)
    }
  }

  const activeCount = allItems.filter((s) => s.status === 'ACTIVE').length
  const extinctCount = allItems.filter((s) => s.status === 'EXTINCT').length

  return (
    <div>
      <PageHeader
        title="Sets"
        description={
          isLoading ? undefined :
          total === 0 ? 'No sets yet' :
          [activeCount > 0 && `${activeCount} active`, extinctCount > 0 && `${extinctCount} extinct`]
            .filter(Boolean).join(' · ') || `${total} total`
        }
        action={
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus className="mr-1.5 h-4 w-4" />Add Set
          </Button>
        }
      />

      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input
            className="pl-8"
            placeholder="Search sets…"
            value={q}
            onChange={(e) => { setQ(e.target.value); setOffset(0) }}
          />
        </div>

        {!q && <StatusTabs value={statusFilter} onChange={setStatusFilter} counts={statusCounts} />}

        {!q && alliancesInList.length > 0 && (
          <Select value={allianceFilter} onValueChange={setAllianceFilter}>
            <SelectTrigger className="h-8 w-auto min-w-32 text-xs">
              <SelectValue placeholder="Alliance" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All alliances</SelectItem>
              <SelectItem value="NONE">No alliance</SelectItem>
              {alliancesInList.map((id) => (
                <SelectItem key={id} value={id}>{allianceMap[id]?.name ?? id}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {allianceFilter !== 'ALL' && (
          <button
            onClick={() => setAllianceFilter('ALL')}
            className="flex items-center gap-1 rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-400 hover:text-white transition-colors"
          >
            <span>Alliance: {allianceFilter === 'NONE' ? 'None' : allianceMap[allianceFilter]?.name ?? '?'}</span>
            <span aria-hidden>×</span>
          </button>
        )}

        <Button
          variant="outline" size="sm" className="ml-auto"
          onClick={() => {
            const date = new Date().toISOString().slice(0, 10)
            downloadCsv(`/sets/?universe_id=${universe.id}&format=csv`, `sets-${universe.slug}-${date}.csv`)
          }}
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-zinc-900/90 backdrop-blur">
            <tr className="border-b border-zinc-800">
              <th className="w-10 px-3 py-2.5" scope="col">
                <input
                  type="checkbox"
                  aria-label="Select all sets"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={() => setSelected(selected.size === items.length ? new Set() : new Set(items.map((s) => s.id)))}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              <SortHeader label="Set" col="name" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
              <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Alliance</th>
              <SortHeader label="Status" col="status" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
              <th className="w-8" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {listLoading
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={5} height={56} />)
              : items.map((set) => {
                  const linkId = set.slug ?? set.id
                  const alliance = set.alliance_id ? allianceMap[set.alliance_id] : null
                  const isSelected = selected.has(set.id)
                  return (
                    <tr key={set.id} className={`group hover:bg-zinc-900/50 transition-colors ${isSelected ? 'bg-violet-950/20' : ''}`}>
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          aria-label={`Select ${set.name}`}
                          checked={isSelected}
                          onChange={() => toggleSelectSet(set.id)}
                          className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                        />
                      </td>
                      {/* Name + aliases */}
                      <td className="p-0">
                        <Link
                          to="/sets/$id"
                          params={{ id: linkId }}
                          className="flex items-center gap-3 px-4 py-3"
                        >
                          <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} />
                          <div>
                            <p className="font-medium text-white group-hover:text-violet-400 transition-colors">
                              {set.name}
                            </p>
                            {set.aliases && set.aliases.length > 0 && (
                              <p className="text-xs text-zinc-500">{set.aliases.join(' · ')}</p>
                            )}
                          </div>
                        </Link>
                      </td>

                      {/* Alliance */}
                      <td className="px-4 py-3">
                        {alliance ? (
                          <Link
                            to="/alliances/$id"
                            params={{ id: alliance.slug ?? set.alliance_id! }}
                            className="inline-flex items-center rounded-full bg-blue-950/60 px-2.5 py-0.5 text-xs font-medium text-blue-300 ring-1 ring-blue-800/50 hover:ring-blue-600 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {alliance.name}
                          </Link>
                        ) : (
                          <span className="text-xs text-zinc-700">—</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3">
                        <SetStatusToggle
                          value={set.status}
                          pending={statusUpdate.isPending && statusUpdate.variables?.id === set.id}
                          onChange={(s) => statusUpdate.mutate({ id: set.id, status: s })}
                        />
                      </td>

                      {/* Quick edit */}
                      <td className="pr-3 py-3">
                        <button
                          onClick={() => setEditingId(set.id)}
                          aria-label={`Edit ${set.name}`}
                          className="rounded p-1.5 text-zinc-600 hover:bg-zinc-800 hover:text-zinc-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
            {!listLoading && items.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <EmptyState
                    icon={Shield}
                    title={
                      q
                        ? `No sets match "${q}"`
                        : statusFilter !== 'ALL'
                        ? `No ${statusFilter === 'ACTIVE' ? 'active' : 'extinct'} sets`
                        : 'No sets yet'
                    }
                    description={
                      !q && statusFilter === 'ALL'
                        ? 'Create a set to start tracking a crew.'
                        : undefined
                    }
                    action={
                      !q && statusFilter === 'ALL' ? (
                        <Button size="sm" onClick={() => setCreating(true)}>
                          <Plus className="mr-1.5 h-4 w-4" /> Create the first set
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

      {/* Pagination */}
      {!isSearching && total > PAGE && (
        <nav className="mt-4 flex items-center justify-between text-sm text-zinc-400" aria-label="Pagination">
          <span>Showing {offset + 1}–{Math.min(offset + PAGE, total)} of {total}</span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              aria-disabled={offset === 0}
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE))}
            >Prev</Button>
            <Button
              variant="outline"
              size="sm"
              aria-disabled={offset + PAGE >= total}
              disabled={offset + PAGE >= total}
              onClick={() => setOffset(offset + PAGE)}
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
    </div>
  )
}
