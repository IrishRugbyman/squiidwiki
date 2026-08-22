import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Check, Copy, Crosshair, Layers, Loader2, MapPin, Pencil, Save, Search, Trash2, X } from 'lucide-react'
import { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { useDebounce } from '@/hooks/useDebounce'
import {
  useAllSets,
  useMappableIncidents,
  useMunicipalityGeoJSON,
  useSet,
  useSetTerritoryPolygons,
  useUpdateSet,
} from '@/lib/queries'
import type { SetListItem, SetTerritoryPolygon, UUID } from '@/lib/types'
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

type EditTab = 'draw' | 'address' | 'pin'

interface AddressVertex {
  query: string
  status: 'pending' | 'loading' | 'ok' | 'error'
  lng?: number
  lat?: number
  label?: string
  error?: string
}

const MAPBOX_TOKEN = (import.meta.env.VITE_MAPBOX_TOKEN ?? '') as string

// A polygon is "closed" when its outer ring has at least 4 coords (3 unique
// vertices + closing) and the first coord equals the last. Mirrors the
// backend validator so the Save button disables when invalid.
function isPolygonClosed(p: GeoJSON.Polygon | null): boolean {
  if (!p || p.type !== 'Polygon') return false
  const ring = p.coordinates[0]
  if (!ring || ring.length < 4) return false
  const a = ring[0], b = ring[ring.length - 1]
  return a[0] === b[0] && a[1] === b[1]
}

function buildPolygonFromVertices(vs: AddressVertex[]): GeoJSON.Polygon | null {
  const ok = vs.filter((v): v is AddressVertex & { lng: number; lat: number } =>
    v.status === 'ok' && typeof v.lng === 'number' && typeof v.lat === 'number',
  )
  if (ok.length < 3) return null
  const ring: number[][] = ok.map((v) => [v.lng, v.lat])
  // Close the ring.
  ring.push([ok[0].lng, ok[0].lat])
  return { type: 'Polygon', coordinates: [ring] }
}

async function geocodeOne(query: string, signal: AbortSignal): Promise<{ lng: number; lat: number; label: string }> {
  if (!MAPBOX_TOKEN) throw new Error('VITE_MAPBOX_TOKEN missing')
  const url = `https://api.mapbox.com/search/geocode/v6/forward?q=${encodeURIComponent(query)}&limit=1&country=us&access_token=${MAPBOX_TOKEN}`
  const r = await fetch(url, { signal })
  if (!r.ok) throw new Error(`Mapbox ${r.status}`)
  const data = (await r.json()) as { features?: Array<{ geometry: { coordinates: [number, number] }; properties: { full_address?: string; name?: string; place_formatted?: string } }> }
  const f = data.features?.[0]
  if (!f) throw new Error('No match')
  const [lng, lat] = f.geometry.coordinates
  const label = f.properties.full_address ?? f.properties.place_formatted ?? f.properties.name ?? query
  return { lng, lat, label }
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
  // The pin the user clicked in pin mode, awaiting save.
  const [pendingPoint, setPendingPoint] = useState<{ lng: number; lat: number } | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [candidates, setCandidates] = useState<OverlapCandidate[]>([])
  const [checkedIds, setCheckedIds] = useState<Set<UUID>>(new Set())

  // Address-mode state.
  const [editTab, setEditTab] = useState<EditTab>('draw')
  const [addressInput, setAddressInput] = useState('')
  const [vertices, setVertices] = useState<AddressVertex[]>([])
  const addressMarkers = useMemo(
    () => vertices.flatMap((v) => v.status === 'ok' && v.lng != null && v.lat != null ? [{ lng: v.lng, lat: v.lat }] : []),
    [vertices],
  )

  const { data: setsList, isLoading: setsLoading } = useAllSets(universeId)
  const { data: selectedSetData } = useSet((selected ?? '') as UUID, universeId, !!selected)
  const selectedSet = selectedSetData ?? null
  const selectedMuniId = selectedSet?.municipality_id ?? null

  // Polygons: when a set is selected, scope to its municipality (its neighbors).
  // Otherwise show every drawn polygon in the universe.
  const { data: setPolygons } = useSetTerritoryPolygons(universeId, selectedMuniId)
  // All polygons universe-wide — used for the "copy boundary from" picker.
  const { data: allPolygons } = useSetTerritoryPolygons(universeId, null)
  // Sub-districts of the selected set's primary municipality (only loaded when
  // outlines toggle is on, or when needed for auto-detect on save).
  const { data: subDistrictGeoJSON } = useMunicipalityGeoJSON(universeId, selectedMuniId ?? undefined)

  // Where to sit when the universe has nothing drawn yet. Without this the map
  // component falls back to a hardcoded Detroit centre, so Chicago and Corsica
  // both opened on the wrong city.
  const { data: universeGeo, isPending: universeGeoPending } = useMunicipalityGeoJSON(universeId)
  const fallbackCenter = useMemo(() => {
    const features = (universeGeo as { features?: { geometry?: unknown }[] } | undefined)?.features
    if (!features?.length) return undefined
    let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity
    const visit = (c: unknown): void => {
      if (Array.isArray(c) && typeof c[0] === 'number' && typeof c[1] === 'number') {
        const [lng, lat] = c as [number, number]
        if (lng < minLng) minLng = lng
        if (lat < minLat) minLat = lat
        if (lng > maxLng) maxLng = lng
        if (lat > maxLat) maxLat = lat
      } else if (Array.isArray(c)) c.forEach(visit)
    }
    for (const f of features) {
      const g = f.geometry as { coordinates?: unknown } | undefined
      if (g?.coordinates) visit(g.coordinates)
    }
    if (!Number.isFinite(minLng)) return undefined
    const span = Math.max(maxLng - minLng, maxLat - minLat)
    // Rough fit: a degree of span is about zoom 8, a tenth about zoom 11.
    const zoom = span > 0 ? Math.min(12, Math.max(7, Math.round(8 - Math.log2(span)))) : 10
    return { longitude: (minLng + maxLng) / 2, latitude: (minLat + maxLat) / 2, zoom }
  }, [universeGeo])

  const { data: incidentsData } = useMappableIncidents(showIncidents ? universeId : null)
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
    setEditTab('draw')
    navigate({ search: (prev) => ({ ...prev, edit: '1' as const }) })
  }
  function startPinEditing() {
    setEditTab('pin')
    navigate({ search: (prev) => ({ ...prev, edit: '1' as const }) })
  }
  function cancelEditing() {
    navigate({ search: (prev) => ({ ...prev, edit: undefined }) })
    setPendingPolygon(null)
    setPendingPoint(null)
    setVertices([])
    setAddressInput('')
    setEditTab('draw')
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

  function handleCopyFromSet(sourceId: UUID) {
    const source = (allPolygons ?? []).find((s) => s.id === sourceId)
    if (!source?.territory_polygon) return
    const poly = source.territory_polygon
    setPendingPolygon(poly)
    const cands = computeOverlapCandidates(poly)
    setCandidates(cands)
    setCheckedIds(new Set(cands.filter((c) => c.overlapPct >= 0.1).map((c) => c.id)))
    setConfirmOpen(true)
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

  async function savePinMarker() {
    if (!pendingPoint || !universeId || !selected) return
    try {
      await updateMutation.mutateAsync({
        universe_id: universeId,
        territory_point: { type: 'Point', coordinates: [pendingPoint.lng, pendingPoint.lat] },
      })
      toast.success('Location marker saved')
      setPendingPoint(null)
      cancelEditing()
    } catch { /* global toast handles error */ }
  }

  async function clearPinMarker() {
    if (!universeId || !selected) return
    try {
      await updateMutation.mutateAsync({
        universe_id: universeId,
        territory_point: null,
      })
      toast.success('Location marker removed')
    } catch { /* global toast handles error */ }
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
    <div className="flex flex-col gap-4 lg:h-[calc(100vh-3.5rem-3rem)] lg:flex-row">
      {/* Sidebar */}
      <aside className="flex max-h-[40vh] w-full shrink-0 flex-col gap-3 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950 p-3 lg:max-h-none lg:w-[280px]">
        {/* View toggle */}
        <div className="inline-flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="tablist">
          {(['sets', 'alliances'] as const).map((v) => (
            <button
              key={v}
              role="tab"
              aria-selected={view === v}
              onClick={() => setView(v)}
              className={`flex-1 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                view === v ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'
              }`}
            >
              {v === 'sets' ? 'Sets' : 'Alliances'}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            placeholder="Search sets…"
            className="pl-9 pr-9"
          />
          {searchQ && (
            <button
              onClick={() => setSearchQ('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto -mr-1 pr-1">
          {isLoadingShell ? (
            <p className="text-xs text-zinc-400">Loading…</p>
          ) : filteredSets.length === 0 ? (
            <p className="text-xs text-zinc-400">No sets match.</p>
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
                className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            {drawingFor ? (
              <EditorTabs
                tab={editTab}
                onTabChange={(t) => {
                  setEditTab(t)
                  // Switching tabs invalidates any in-progress state from the other mode.
                  setPendingPolygon(null)
                  setPendingPoint(null)
                }}
                addressInput={addressInput}
                onAddressInputChange={setAddressInput}
                vertices={vertices}
                onVerticesChange={setVertices}
                onBuildPolygon={() => {
                  const poly = buildPolygonFromVertices(vertices)
                  if (poly) setPendingPolygon(poly)
                }}
                existingPoint={selectedSet.territory_point ?? null}
                pendingPoint={pendingPoint}
                onClearPin={clearPinMarker}
                onClearPendingPin={() => setPendingPoint(null)}
                onPinPlaced={(lng, lat) => setPendingPoint({ lng, lat })}
              />
            ) : (
              <div className="space-y-1.5">
                {selectedSet.municipality_id ? (
                  <Button size="sm" variant="outline" className="w-full" onClick={startEditing}>
                    <Pencil className="mr-1.5 h-3.5 w-3.5" />
                    {selectedSet.territory_polygon ? 'Edit boundary' : 'Draw boundary'}
                  </Button>
                ) : (
                  <p className="text-xs text-zinc-400">Set a primary municipality to draw a polygon boundary.</p>
                )}
                <Button size="sm" variant="outline" className="w-full" onClick={startPinEditing}>
                  <MapPin className="mr-1.5 h-3.5 w-3.5" />
                  {selectedSet.territory_point ? 'Edit location pin' : 'Set location pin'}
                </Button>
                <CopyFromSelect
                  currentSetId={selected ?? null}
                  polygons={allPolygons ?? []}
                  onCopy={handleCopyFromSet}
                />
              </div>
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
              {(setPolygons?.length ?? 0)} set{(setPolygons?.length ?? 0) === 1 ? '' : 's'} with territory marked
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
                <Button
                  size="sm"
                  onClick={editTab === 'pin' ? savePinMarker : openConfirm}
                  disabled={
                    updateMutation.isPending ||
                    (editTab === 'pin' ? !pendingPoint : !isPolygonClosed(pendingPolygon))
                  }
                  title={
                    editTab === 'pin'
                      ? (!pendingPoint ? 'Click on the map to place a marker first' : undefined)
                      : (!isPolygonClosed(pendingPolygon) ? 'Polygon must be closed (≥3 vertices, first = last)' : undefined)
                  }
                >
                  <Save className="mr-1.5 h-3.5 w-3.5" />
                  {editTab === 'pin'
                    ? (updateMutation.isPending ? 'Saving…' : 'Save marker')
                    : 'Save boundary'}
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Map */}
        <div className="relative h-[55vh] overflow-hidden rounded-lg border border-zinc-800 lg:h-auto lg:flex-1">
          {/* Hold the map back until the universe's geometry has landed. maplibre
              reads initialViewState once, at mount, so a fallback centre that
              arrives a tick later is simply ignored - which is how every universe
              ended up opening over Detroit. */}
          <Suspense fallback={<MapPlaceholder />}>
            {universeGeoPending ? <MapPlaceholder /> : <TerritoryMap
              setPolygons={setPolygons ?? []}
              selectedSetId={selected ?? null}
              drawingFor={editTab === 'draw' ? drawingFor : null}
              initialPolygon={selectedSet?.territory_polygon ?? null}
              subDistrictGeoJSON={showSubDistricts ? (subDistrictGeoJSON ?? null) : null}
              showSubDistrictOutlines={showSubDistricts}
              incidentPoints={incidentPoints}
              addressMarkers={editTab === 'address' ? addressMarkers : []}
              viewMode={view}
              onPolygonComplete={handlePolygonComplete}
              onSelectSet={selectSet}
              fitSignal={fitSignal}
              fallbackCenter={fallbackCenter}
              pinMode={editTab === 'pin' && !!drawingFor}
              pendingPoint={editTab === 'pin' ? pendingPoint : null}
              pendingPointColor={selectedSet?.gang_color ?? null}
              onPinPlaced={(lng, lat) => setPendingPoint({ lng, lat })}
            />}
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
                  <span className="font-mono text-xs tabular-nums text-zinc-400">
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

function EditorTabs({
  tab, onTabChange, addressInput, onAddressInputChange, vertices, onVerticesChange, onBuildPolygon,
  existingPoint, pendingPoint, onClearPin, onClearPendingPin, onPinPlaced,
}: {
  tab: EditTab
  onTabChange: (t: EditTab) => void
  addressInput: string
  onAddressInputChange: (v: string) => void
  vertices: AddressVertex[]
  onVerticesChange: (v: AddressVertex[]) => void
  onBuildPolygon: () => void
  existingPoint: { type: 'Point'; coordinates: [number, number] } | null
  pendingPoint: { lng: number; lat: number } | null
  onClearPin: () => void
  onClearPendingPin: () => void
  onPinPlaced: (lng: number, lat: number) => void
}) {
  const okCount = vertices.filter((v) => v.status === 'ok').length
  const anyLoading = vertices.some((v) => v.status === 'loading')

  const [pinAddressInput, setPinAddressInput] = useState('')
  const [pinGeocodeState, setPinGeocodeState] = useState<'idle' | 'loading' | 'error'>('idle')
  const [pinGeocodeError, setPinGeocodeError] = useState('')
  const [pinGeocodeLabel, setPinGeocodeLabel] = useState('')

  async function geocodePin() {
    const q = pinAddressInput.trim()
    if (!q) return
    setPinGeocodeState('loading')
    setPinGeocodeError('')
    setPinGeocodeLabel('')
    try {
      const { lng, lat, label } = await geocodeOne(q, new AbortController().signal)
      setPinGeocodeLabel(label)
      setPinGeocodeState('idle')
      onPinPlaced(lng, lat)
    } catch (e) {
      setPinGeocodeState('error')
      setPinGeocodeError(e instanceof Error ? e.message : 'Geocode failed')
    }
  }

  async function geocodeAll() {
    const lines = addressInput
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    if (lines.length === 0) return
    // Seed all rows immediately so the user sees progress.
    const seeded: AddressVertex[] = lines.map((q) => ({ query: q, status: 'loading' }))
    onVerticesChange(seeded)
    const ctrl = new AbortController()
    // Run sequentially — Mapbox is fast enough and this preserves order/UI clarity.
    const next: AddressVertex[] = []
    for (let i = 0; i < lines.length; i++) {
      const q = lines[i]
      try {
        const { lng, lat, label } = await geocodeOne(q, ctrl.signal)
        next.push({ query: q, status: 'ok', lng, lat, label })
      } catch (e) {
        next.push({ query: q, status: 'error', error: e instanceof Error ? e.message : 'Failed' })
      }
      // Push partial state so the UI updates as each line resolves.
      onVerticesChange([...next, ...seeded.slice(next.length)])
    }
  }

  function clearAll() {
    onVerticesChange([])
    onAddressInputChange('')
  }

  return (
    <div className="space-y-2">
      <div className="inline-flex w-full items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="tablist">
        {(['draw', 'address', 'pin'] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => onTabChange(t)}
            className={`flex-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
              tab === t ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'
            }`}
          >
            {t === 'draw' ? 'Draw' : t === 'address' ? 'Address' : 'Pin'}
          </button>
        ))}
      </div>

      {tab === 'pin' ? (
        <div className="space-y-2">
          {/* Address geocoder */}
          <p className="text-[11px] text-zinc-400">Search an address or intersection (US only).</p>
          <div className="flex items-center gap-1.5">
            <input
              value={pinAddressInput}
              onChange={(e) => { setPinAddressInput(e.target.value); setPinGeocodeState('idle') }}
              onKeyDown={(e) => e.key === 'Enter' && geocodePin()}
              placeholder="E. Seven Mile & Hayes, Detroit"
              className="flex-1 min-w-0 rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 text-[11px] text-zinc-200 placeholder:text-zinc-400 focus-visible:border-violet-700 focus-visible:outline-none"
            />
            <Button size="sm" variant="outline" onClick={geocodePin} disabled={!pinAddressInput.trim() || pinGeocodeState === 'loading'} className="shrink-0 px-2">
              {pinGeocodeState === 'loading' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <MapPin className="h-3.5 w-3.5" />}
            </Button>
          </div>
          {pinGeocodeState === 'error' && (
            <p className="text-[10px] text-rose-400">{pinGeocodeError}</p>
          )}
          {pinGeocodeLabel && pinGeocodeState === 'idle' && (
            <p className="truncate text-[10px] text-emerald-400">{pinGeocodeLabel}</p>
          )}

          <p className="text-[10px] text-zinc-400">or click anywhere on the map</p>

          {existingPoint && !pendingPoint && (
            <div className="rounded-md border border-zinc-800 bg-zinc-950/50 px-2 py-1.5 text-[11px]">
              <p className="text-zinc-400">Current marker:</p>
              <p className="font-mono text-zinc-300">
                {existingPoint.coordinates[1].toFixed(5)}, {existingPoint.coordinates[0].toFixed(5)}
              </p>
              <Button size="sm" variant="destructive" className="mt-2 w-full text-[11px]" onClick={onClearPin}>
                <Trash2 className="mr-1.5 h-3 w-3" />Remove marker
              </Button>
            </div>
          )}
          {pendingPoint && (
            <div className="rounded-md border border-violet-800/50 bg-violet-950/30 px-2 py-1.5 text-[11px]">
              <p className="text-violet-400">New marker position:</p>
              <p className="font-mono text-violet-200">
                {pendingPoint.lat.toFixed(5)}, {pendingPoint.lng.toFixed(5)}
              </p>
              <Button size="sm" variant="outline" className="mt-2 w-full text-[11px]" onClick={onClearPendingPin}>
                <X className="mr-1.5 h-3 w-3" />Cancel placement
              </Button>
            </div>
          )}
        </div>
      ) : tab === 'draw' ? (
        <p className="text-xs text-zinc-400">
          Click on the map to drop polygon vertices, double-click the last point to finish.
        </p>
      ) : (
        <div className="space-y-2">
          <p className="text-[11px] text-zinc-400">
            One address or intersection per line (US only). Mapbox geocoder.
          </p>
          <textarea
            value={addressInput}
            onChange={(e) => onAddressInputChange(e.target.value)}
            placeholder={'Mack Ave & Van Dyke St, Detroit\nGratiot Ave & Conner St, Detroit\n…'}
            className="h-24 w-full resize-y rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-200 placeholder:text-zinc-400 focus-visible:border-violet-700 focus-visible:outline-none"
          />
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" className="flex-1" onClick={geocodeAll} disabled={!addressInput.trim() || anyLoading}>
              {anyLoading ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <MapPin className="mr-1.5 h-3.5 w-3.5" />}
              Geocode
            </Button>
            {vertices.length > 0 && (
              <Button size="sm" variant="outline" onClick={clearAll} aria-label="Clear">
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>

          {vertices.length > 0 && (
            <ul className="max-h-40 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950/50 divide-y divide-zinc-800">
              {vertices.map((v, i) => (
                <li key={i} className="flex items-start gap-2 px-2 py-1.5 text-[11px]">
                  <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-[10px] font-medium text-zinc-300">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className={`truncate ${v.status === 'error' ? 'text-rose-400' : 'text-zinc-200'}`}>
                      {v.label ?? v.query}
                    </p>
                    {v.status === 'error' && <p className="truncate text-[10px] text-rose-500">{v.error}</p>}
                  </div>
                  {v.status === 'loading' && <Loader2 className="h-3 w-3 shrink-0 animate-spin text-zinc-400" />}
                  {v.status === 'ok' && <Check className="h-3 w-3 shrink-0 text-emerald-500" />}
                  {v.status === 'error' && <X className="h-3 w-3 shrink-0 text-rose-500" />}
                </li>
              ))}
            </ul>
          )}

          <Button
            size="sm"
            className="w-full"
            onClick={onBuildPolygon}
            disabled={okCount < 3}
            title={okCount < 3 ? 'Need at least 3 successfully geocoded points to close a polygon' : undefined}
          >
            Build polygon ({okCount} pt{okCount === 1 ? '' : 's'})
          </Button>
        </div>
      )}
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
          <h3 className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wider text-zinc-400">{g.name}</h3>
          <ul className="space-y-0.5">
            {g.sets.map((s) => (
              <SetRow key={s.id} set={s} selected={selected === s.id} hasPolygon={polygonSetIds.has(s.id)} onClick={() => onSelect(s.id)} />
            ))}
          </ul>
        </div>
      ))}
      {unaffiliated.length > 0 && (
        <div>
          <h3 className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wider text-zinc-400">Unaffiliated</h3>
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

function CopyFromSelect({
  currentSetId,
  polygons,
  onCopy,
}: {
  currentSetId: UUID | null
  polygons: SetTerritoryPolygon[]
  onCopy: (id: UUID) => void
}) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  const polyPolygons = useMemo(
    () => polygons.filter((p) => p.territory_polygon != null),
    [polygons],
  )

  const choices = useMemo(
    () => polyPolygons
      .filter((p) => p.id !== currentSetId)
      .filter((p) => !q || p.name.toLowerCase().includes(q.toLowerCase()))
      .sort((a, b) => a.name.localeCompare(b.name)),
    [polyPolygons, currentSetId, q],
  )

  // Close on outside click.
  useEffect(() => {
    if (!open) return
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  if (polyPolygons.filter((p) => p.id !== currentSetId).length === 0) return null

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => { setOpen((v) => !v); setQ('') }}
        className="flex w-full items-center justify-center gap-1.5 rounded-md border border-zinc-700 bg-transparent px-2 py-1 text-xs text-zinc-400 hover:border-zinc-500 hover:text-zinc-200 transition-colors"
      >
        <Copy className="h-3 w-3" />
        Copy boundary from…
      </button>
      {open && (
        <div className="absolute bottom-full left-0 right-0 mb-1 z-50 rounded-md border border-zinc-700 bg-zinc-900 shadow-xl">
          <div className="p-1.5 border-b border-zinc-800">
            <input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search sets…"
              className="w-full rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-200 placeholder:text-zinc-400 outline-none"
            />
          </div>
          <ul className="max-h-48 overflow-y-auto py-1">
            {choices.length === 0 ? (
              <li className="px-3 py-2 text-xs text-zinc-400">No sets found.</li>
            ) : choices.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => { onCopy(p.id); setOpen(false) }}
                  className="w-full px-3 py-1.5 text-left text-xs text-zinc-300 hover:bg-zinc-800 transition-colors truncate"
                >
                  {p.name}
                </button>
              </li>
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
        active ? activeClasses : 'border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-300'
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
      <div className="flex flex-col items-center gap-2 text-zinc-400">
        <MapPin className="h-8 w-8 animate-pulse" />
        <span className="text-sm">Loading map…</span>
      </div>
    </div>
  )
}
