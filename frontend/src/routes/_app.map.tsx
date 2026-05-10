import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Crosshair, Layers, MapPin, Pencil, Save, Search, X } from 'lucide-react'
import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { useDebounce } from '@/hooks/useDebounce'
import {
  useAllSets,
  useAllIncidents,
  useMunicipalityGeoJSON,
  useSet,
  useSetTerritoryPolygons,
  useUpdateSet,
} from '@/lib/queries'
import type { SetListItem, UUID } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import intersect from '@turf/intersect'
import area from '@turf/area'
import { featureCollection } from '@turf/helpers'
import type { Feature, MultiPolygon, Polygon } from 'geojson'
import type { IncidentPoint } from '@/components/maps/MunicipalityMap'

const TerritoryMap = lazy(() => import('@/components/maps/TerritoryMap'))

type ViewMode = 'sets' | 'alliances'

export const Route = createFileRoute('/_app/map')({
  validateSearch: (s: Record<string, unknown>) => ({
    selected: typeof s.selected === 'string' ? (s.selected as UUID) : undefined,
    edit: s.edit === '1' || s.edit === 1 ? '1' as const : undefined,
    view: s.view === 'alliances' ? 'alliances' as const : 'sets' as const,
  }),
  component: TerritoryMapPage,
})

function statusDot(status: 'ACTIVE' | 'EXTINCT'): string {
  return status === 'ACTIVE' ? 'bg-violet-500' : 'bg-zinc-600'
}

interface OverlapCandidate {
  id: UUID
  name: string
  overlapPct: number
}

function TerritoryMapPage() {
  const { selected, edit, view } = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })
  const universeId = useUniverseStore((s) => s.activeUniverse?.id ?? null)

  const [showSubDistricts, setShowSubDistricts] = useState(false)
  const [showIncidents, setShowIncidents] = useState(false)
  const [searchQ, setSearchQ] = useState('')
  const debouncedQ = useDebounce(searchQ, 150)
  const [fitSignal, setFitSignal] = useState(0)

  // The polygon the user just drew, awaiting confirmation.
  const [pendingPolygon, setPendingPolygon] = useState<GeoJSON.Polygon | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [candidates, setCandidates] = useState<OverlapCandidate[]>([])
  const [checkedIds, setCheckedIds] = useState<Set<UUID>>(new Set())

  const { data: setsList, isLoading: setsLoading } = useAllSets(universeId)
  const { data: selectedSetData } = useSet((selected ?? '') as UUID, universeId, !!selected)
  const selectedSet = selectedSetData ?? null
  const selectedMuniId = selectedSet?.municipality_id ?? null

  // Polygons: when a set is selected, scope to its municipality (its neighbors).
  // Otherwise show every drawn polygon in the universe.
  const { data: setPolygons } = useSetTerritoryPolygons(universeId, selectedMuniId)
  // Sub-districts of the selected set's primary municipality (only loaded when
  // outlines toggle is on, or when needed for auto-detect on save).
  const { data: subDistrictGeoJSON } = useMunicipalityGeoJSON(universeId, selectedMuniId ?? undefined)

  const { data: incidentsData } = useAllIncidents(showIncidents ? universeId : null)
  const incidentPoints: IncidentPoint[] = useMemo(() => {
    if (!showIncidents) return []
    return (incidentsData?.items ?? []).flatMap((inc) =>
      inc.lat != null && inc.lng != null
        ? [{ id: inc.id, type: inc.type, lat: inc.lat, lng: inc.lng }]
        : [],
    )
  }, [showIncidents, incidentsData])

  // Sidebar list — search-filtered. In alliances view we still list sets, but
  // group/sort by alliance name; selection is set-scoped (clicking an entry
  // selects that specific set, which is also what colors the alliance group).
  const filteredSets = useMemo<SetListItem[]>(() => {
    const items = setsList?.items ?? []
    const q = debouncedQ.trim().toLowerCase()
    const matched = q ? items.filter((s) => s.name.toLowerCase().includes(q)) : items
    if (view === 'alliances') {
      return [...matched].sort((a, b) => {
        const ka = a.alliance_name ?? '~zzz'
        const kb = b.alliance_name ?? '~zzz'
        if (ka !== kb) return ka.localeCompare(kb)
        return a.name.localeCompare(b.name)
      })
    }
    return matched
  }, [setsList, debouncedQ, view])

  const polygonByteSetIds = useMemo(
    () => new Set((setPolygons ?? []).map((p) => p.id)),
    [setPolygons],
  )

  // ─── update mutation ────────────────────────────────────────────────────

  const updateMutation = useUpdateSet(selected ?? ('' as UUID))

  function selectSet(id: UUID) {
    navigate({ search: (prev) => ({ ...prev, selected: id, edit: undefined }) })
    setFitSignal((n) => n + 1)
  }
  function clearSelection() {
    navigate({ search: (prev) => ({ ...prev, selected: undefined, edit: undefined }) })
    setFitSignal((n) => n + 1)
  }
  function startEditing() {
    navigate({ search: (prev) => ({ ...prev, edit: '1' as const }) })
  }
  function cancelEditing() {
    navigate({ search: (prev) => ({ ...prev, edit: undefined }) })
    setPendingPolygon(null)
  }
  function setView(next: ViewMode) {
    navigate({ search: (prev) => ({ ...prev, view: next }) })
  }

  // Compute auto-detect candidates from the drawn polygon vs sub-district GeoJSON.
  function computeOverlapCandidates(poly: GeoJSON.Polygon): OverlapCandidate[] {
    if (!subDistrictGeoJSON) return []
    const drawnFeature: Feature<Polygon> = {
      type: 'Feature',
      properties: {},
      geometry: poly,
    }
    const out: OverlapCandidate[] = []
    for (const f of subDistrictGeoJSON.features) {
      // Skip the parent municipality itself (it's in the same FC for some queries).
      if (!f.geometry || f.geometry.type !== 'Polygon' && f.geometry.type !== 'MultiPolygon') continue
      const subFeature: Feature<Polygon | MultiPolygon> = {
        type: 'Feature',
        properties: {},
        geometry: f.geometry as unknown as Polygon | MultiPolygon,
      }
      let inter: Feature<Polygon | MultiPolygon> | null = null
      try {
        inter = intersect(featureCollection([drawnFeature, subFeature])) as
          Feature<Polygon | MultiPolygon> | null
      } catch {
        inter = null
      }
      if (!inter || !inter.geometry) continue
      const interArea = area(inter)
      const subArea = area(subFeature)
      if (subArea <= 0) continue
      const pct = interArea / subArea
      if (pct >= 0.01) {
        out.push({ id: f.id as UUID, name: f.properties.name, overlapPct: pct })
      }
    }
    out.sort((a, b) => b.overlapPct - a.overlapPct)
    return out
  }

  function handlePolygonComplete(poly: GeoJSON.Polygon) {
    setPendingPolygon(poly)
  }

  function openConfirm() {
    if (!pendingPolygon || !universeId || !selected) return
    const cands = computeOverlapCandidates(pendingPolygon)
    setCandidates(cands)
    // Pre-check anything with ≥10% overlap.
    setCheckedIds(new Set(cands.filter((c) => c.overlapPct >= 0.1).map((c) => c.id)))
    setConfirmOpen(true)
  }

  function toggleCandidate(id: UUID) {
    setCheckedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function confirmSave() {
    if (!pendingPolygon || !universeId || !selected) return
    try {
      await updateMutation.mutateAsync({
        universe_id: universeId,
        territory_polygon: pendingPolygon,
        territory_ids: Array.from(checkedIds),
      })
      toast.success('Boundary saved')
      setConfirmOpen(false)
      setPendingPolygon(null)
      cancelEditing()
    } catch {
      // Global mutation onError already toasts the error.
    }
  }

  // Auto-open the editor if URL says so (deep-link).
  useEffect(() => {
    if (edit === '1' && selected && !selectedSet?.territory_polygon) {
      // Nothing to seed; user will draw fresh.
    }
  }, [edit, selected, selectedSet])

  if (!universeId) return <NoUniverse />

  const drawingFor = edit === '1' ? selected ?? null : null
  const isLoadingShell = setsLoading

  return (
    <div className="flex h-[calc(100vh-3.5rem-3rem)] gap-4">
      {/* Sidebar */}
      <aside className="flex w-[280px] shrink-0 flex-col gap-3 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 p-3">
        {/* View toggle */}
        <div className="inline-flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="tablist">
          {(['sets', 'alliances'] as const).map((v) => (
            <button
              key={v}
              role="tab"
              aria-selected={view === v}
              onClick={() => setView(v)}
              className={`flex-1 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                view === v ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {v === 'sets' ? 'Sets' : 'Alliances'}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <Input
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            placeholder="Search sets…"
            className="pl-9 pr-9"
          />
          {searchQ && (
            <button
              onClick={() => setSearchQ('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto -mr-1 pr-1">
          {isLoadingShell ? (
            <p className="text-xs text-zinc-500">Loading…</p>
          ) : filteredSets.length === 0 ? (
            <p className="text-xs text-zinc-500">No sets match.</p>
          ) : view === 'alliances' ? (
            renderGroupedByAlliance(filteredSets, selected, selectSet, polygonByteSetIds)
          ) : (
            <ul className="space-y-0.5">
              {filteredSets.map((s) => (
                <SetRow key={s.id} set={s} selected={selected === s.id} hasPolygon={polygonByteSetIds.has(s.id)} onClick={() => selectSet(s.id)} />
              ))}
            </ul>
          )}
        </div>

        {/* Selected-set details + edit button */}
        {selectedSet && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
            <div className="mb-2 flex items-center justify-between">
              <Link
                to="/sets/$id"
                params={{ id: selectedSet.slug ?? selectedSet.id }}
                className="text-sm font-semibold text-white hover:underline"
              >
                {selectedSet.name}
              </Link>
              <button
                onClick={clearSelection}
                aria-label="Clear selection"
                className="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            {!selectedSet.municipality_id ? (
              <p className="text-xs text-zinc-500">Set a primary municipality before drawing a boundary.</p>
            ) : drawingFor ? (
              <p className="text-xs text-zinc-400">Click on the map to drop polygon vertices, double-click the last point to finish.</p>
            ) : (
              <Button size="sm" variant="outline" className="w-full" onClick={startEditing}>
                <Pencil className="mr-1.5 h-3.5 w-3.5" />
                {selectedSet.territory_polygon ? 'Edit boundary' : 'Draw boundary'}
              </Button>
            )}
          </div>
        )}
      </aside>

      {/* Main map area */}
      <div className="flex flex-1 flex-col gap-3 overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-semibold text-white">Territory map</h1>
            <p className="text-sm text-zinc-400">
              {(setPolygons?.length ?? 0)} set{(setPolygons?.length ?? 0) === 1 ? '' : 's'} with a drawn boundary
              {selectedSet ? ` · viewing ${selectedSet.name}` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <ToolbarToggle
              active={showSubDistricts}
              onClick={() => setShowSubDistricts((v) => !v)}
              icon={<Layers className="h-3.5 w-3.5" />}
              label="Sub-districts"
              activeColor="zinc"
            />
            <ToolbarToggle
              active={showIncidents}
              onClick={() => setShowIncidents((v) => !v)}
              icon={<Crosshair className="h-3.5 w-3.5" />}
              label="Incidents"
              activeColor="rose"
            />
            {drawingFor && (
              <>
                <Button size="sm" variant="outline" onClick={cancelEditing}>
                  <X className="mr-1.5 h-3.5 w-3.5" />Cancel
                </Button>
                <Button size="sm" onClick={openConfirm} disabled={!pendingPolygon}>
                  <Save className="mr-1.5 h-3.5 w-3.5" />Save boundary
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Map */}
        <div className="relative flex-1 overflow-hidden rounded-xl border border-zinc-800">
          <Suspense fallback={<MapPlaceholder />}>
            <TerritoryMap
              setPolygons={setPolygons ?? []}
              selectedSetId={selected ?? null}
              drawingFor={drawingFor}
              initialPolygon={selectedSet?.territory_polygon ?? null}
              subDistrictGeoJSON={showSubDistricts ? (subDistrictGeoJSON ?? null) : null}
              showSubDistrictOutlines={showSubDistricts}
              incidentPoints={incidentPoints}
              viewMode={view}
              onPolygonComplete={handlePolygonComplete}
              onSelectSet={selectSet}
              fitSignal={fitSignal}
            />
          </Suspense>
        </div>
      </div>

      {/* Confirm dialog */}
      <Dialog open={confirmOpen} onOpenChange={(v) => !v && !updateMutation.isPending && setConfirmOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm sub-districts</DialogTitle>
            <DialogDescription>
              The drawn boundary overlaps these sub-districts. Pick which to record as this set's territory.
            </DialogDescription>
          </DialogHeader>
          {candidates.length === 0 ? (
            <p className="py-4 text-sm text-zinc-400">
              No sub-districts overlap this polygon. The boundary will still be saved.
            </p>
          ) : (
            <ul className="max-h-72 overflow-y-auto divide-y divide-zinc-800 rounded-md border border-zinc-800">
              {candidates.map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                  <label className="flex flex-1 items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checkedIds.has(c.id)}
                      onChange={() => toggleCandidate(c.id)}
                      className="h-4 w-4 accent-violet-600"
                    />
                    <span className="text-zinc-200">{c.name}</span>
                  </label>
                  <span className="font-mono text-xs tabular-nums text-zinc-500">
                    {Math.round(c.overlapPct * 100)}%
                  </span>
                </li>
              ))}
            </ul>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setConfirmOpen(false)} disabled={updateMutation.isPending}>
              Cancel
            </Button>
            <Button onClick={confirmSave} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving…' : 'Save'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function SetRow({
  set, selected, hasPolygon, onClick,
}: { set: SetListItem; selected: boolean; hasPolygon: boolean; onClick: () => void }) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
          selected ? 'bg-violet-950/60 text-white' : 'text-zinc-300 hover:bg-zinc-900'
        }`}
      >
        <span className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${statusDot(set.status)}`} aria-hidden />
        <span className="flex-1 truncate">{set.name}</span>
        {hasPolygon && (
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" title="Has territory boundary" aria-hidden />
        )}
      </button>
    </li>
  )
}

function renderGroupedByAlliance(
  sets: SetListItem[],
  selected: UUID | undefined,
  onSelect: (id: UUID) => void,
  polygonSetIds: Set<UUID>,
) {
  const byAlliance = new Map<string, { name: string; sets: SetListItem[] }>()
  const unaffiliated: SetListItem[] = []
  for (const s of sets) {
    if (s.alliance_id) {
      const k = s.alliance_id as string
      if (!byAlliance.has(k)) byAlliance.set(k, { name: s.alliance_name ?? '(unnamed alliance)', sets: [] })
      byAlliance.get(k)!.sets.push(s)
    } else {
      unaffiliated.push(s)
    }
  }
  const groups = Array.from(byAlliance.values())
  return (
    <div className="space-y-3">
      {groups.map((g) => (
        <div key={g.name}>
          <h3 className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wider text-zinc-500">{g.name}</h3>
          <ul className="space-y-0.5">
            {g.sets.map((s) => (
              <SetRow key={s.id} set={s} selected={selected === s.id} hasPolygon={polygonSetIds.has(s.id)} onClick={() => onSelect(s.id)} />
            ))}
          </ul>
        </div>
      ))}
      {unaffiliated.length > 0 && (
        <div>
          <h3 className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wider text-zinc-600">Unaffiliated</h3>
          <ul className="space-y-0.5">
            {unaffiliated.map((s) => (
              <SetRow key={s.id} set={s} selected={selected === s.id} hasPolygon={polygonSetIds.has(s.id)} onClick={() => onSelect(s.id)} />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function ToolbarToggle({
  active, onClick, icon, label, activeColor,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
  activeColor: 'zinc' | 'rose' | 'violet'
}) {
  const activeClasses = {
    zinc: 'border-zinc-500 bg-zinc-800 text-zinc-100',
    rose: 'border-rose-700 bg-rose-950/60 text-rose-300',
    violet: 'border-violet-700 bg-violet-950/60 text-violet-300',
  }[activeColor]
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
        active ? activeClasses : 'border-zinc-700 text-zinc-500 hover:border-zinc-500 hover:text-zinc-300'
      }`}
    >
      {icon}
      {label}
    </button>
  )
}

function MapPlaceholder() {
  return (
    <div className="flex h-full items-center justify-center bg-zinc-900">
      <div className="flex flex-col items-center gap-2 text-zinc-500">
        <MapPin className="h-8 w-8 animate-pulse" />
        <span className="text-sm">Loading map…</span>
      </div>
    </div>
  )
}
