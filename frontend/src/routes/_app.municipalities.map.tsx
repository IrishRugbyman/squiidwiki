import { createFileRoute, Link } from '@tanstack/react-router'
import { MapPin, AlertTriangle, ChevronRight, ListFilter, X, Crosshair, Users } from 'lucide-react'
import { Suspense, lazy, useMemo, useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { useUniverseStore } from '@/stores/universe'
import { useMunicipalities, useMunicipalityGeoJSON, useAllIncidents, useAllSets } from '@/lib/queries'
import type { MunicipalityListItem, UUID } from '@/lib/types'
import type { MapMetric, IncidentPoint, SetPoint } from '@/components/maps/MunicipalityMap'

const MunicipalityMap = lazy(() => import('@/components/maps/MunicipalityMap'))

function MetricToggle({ value, onChange }: { value: MapMetric; onChange: (v: MapMetric) => void }) {
  const tabs: { key: MapMetric; label: string }[] = [
    { key: 'sets', label: 'Sets' },
    { key: 'incidents', label: 'Incidents' },
  ]
  return (
    <div className="inline-flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1" role="tablist" aria-label="Choropleth metric">
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          role="tab"
          aria-selected={value === key}
          onClick={() => onChange(key)}
          className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
            value === key ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

export const Route = createFileRoute('/_app/municipalities/map')({
  validateSearch: (s: Record<string, unknown>) => ({
    focus: typeof s.focus === 'string' ? (s.focus as UUID) : undefined,
  }),
  component: MapPage,
})

function MapPage() {
  const { focus } = Route.useSearch()
  const universeId = useUniverseStore((s) => s.activeUniverse?.id ?? null)
  const [metric, setMetric] = useState<MapMetric>('sets')
  const [showIncidents, setShowIncidents] = useState(false)
  const [showSets, setShowSets] = useState(false)
  const [previewId, setPreviewId] = useState<UUID | null>(null)
  const { data: listData, isLoading: listLoading } = useMunicipalities(universeId)
  const { data: geojson, isLoading: geoLoading } = useMunicipalityGeoJSON(universeId, 'top')
  const { data: incidentsData } = useAllIncidents(showIncidents ? universeId : null)
  const { data: setsData } = useAllSets(showSets ? universeId : null)

  const incidentPoints: IncidentPoint[] = showIncidents
    ? (incidentsData?.items ?? []).flatMap((inc) =>
        inc.lat != null && inc.lng != null
          ? [{ id: inc.id, type: inc.type, lat: inc.lat, lng: inc.lng }]
          : [],
      )
    : []

  // Compute per-municipality bounding-box centroids from the GeoJSON so sets
  // (which have municipality_id but no coordinates) can be plotted on the map.
  const municipalityCentroids = useMemo<Record<string, [number, number]>>(() => {
    if (!geojson) return {}
    const result: Record<string, [number, number]> = {}
    for (const f of geojson.features) {
      if (!f.geometry) continue
      let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity
      const walk = (coords: number[] | number[][] | number[][][] | number[][][][]) => {
        if (typeof coords[0] === 'number') {
          const [lng, lat] = coords as number[]
          if (lng < minLng) minLng = lng
          if (lat < minLat) minLat = lat
          if (lng > maxLng) maxLng = lng
          if (lat > maxLat) maxLat = lat
        } else {
          for (const c of coords as number[][]) walk(c)
        }
      }
      walk(f.geometry.coordinates as unknown as number[][])
      if (minLng !== Infinity) {
        result[f.id as string] = [(minLng + maxLng) / 2, (minLat + maxLat) / 2]
      }
    }
    return result
  }, [geojson])

  const setPoints: SetPoint[] = useMemo(() => {
    if (!showSets) return []
    return (setsData?.items ?? []).flatMap((s) => {
      if (!s.municipality_id) return []
      const center = municipalityCentroids[s.municipality_id]
      if (!center) return []
      return [{ id: s.id, status: s.status, lng: center[0], lat: center[1] }]
    })
  }, [showSets, setsData, municipalityCentroids])

  if (!universeId) return <NoUniverse />

  const isLoading = listLoading || geoLoading
  // Main map shows top-level municipalities only (drill into one to see its
  // sub-districts on the detail page). All counts here are over top-level.
  const allItems = listData?.items ?? []
  const topLevel = allItems.filter((m) => !m.parent_id)
  const withoutGeometry = topLevel.filter((m) => !m.has_geometry)
  const featureCount = geojson?.features.length ?? 0
  const preview = previewId ? allItems.find((m) => m.id === previewId) ?? null : null
  const previewParent = preview?.parent_id ? allItems.find((m) => m.id === preview.parent_id) ?? null : null
  const previewChildCount = preview ? allItems.filter((m) => m.parent_id === preview.id).length : 0

  return (
    <div className="flex h-[calc(100vh-3.5rem-3rem)] flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-white">Map</h1>
          <p className="text-sm text-zinc-400">
            {featureCount} of {topLevel.length} municipalities mapped
          </p>
        </div>
        <div className="flex items-center gap-2">
          <MetricToggle value={metric} onChange={setMetric} />
          <button
            type="button"
            onClick={() => setShowSets((v) => !v)}
            aria-pressed={showSets}
            title="Toggle set markers"
            className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              showSets
                ? 'border-violet-700 bg-violet-950/60 text-violet-300 hover:bg-violet-900/60'
                : 'border-zinc-700 text-zinc-500 hover:border-zinc-500 hover:text-zinc-300'
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            Sets
          </button>
          <button
            type="button"
            onClick={() => setShowIncidents((v) => !v)}
            aria-pressed={showIncidents}
            title="Toggle incident points"
            className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              showIncidents
                ? 'border-rose-700 bg-rose-950/60 text-rose-300 hover:bg-rose-900/60'
                : 'border-zinc-700 text-zinc-500 hover:border-zinc-500 hover:text-zinc-300'
            }`}
          >
            <Crosshair className="h-3.5 w-3.5" />
            Incidents
          </button>
          {withoutGeometry.length > 0 && (
            <Link
              to="/municipalities"
              className="flex items-center gap-1.5 rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:border-zinc-500 hover:text-white transition-colors"
            >
              <MapPin className="h-3.5 w-3.5" />
              Add boundaries to {withoutGeometry.length} more
            </Link>
          )}
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden rounded-xl border border-zinc-800">
        {isLoading ? (
          <MapPlaceholder label="Loading map…" />
        ) : featureCount === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 bg-zinc-900 text-center">
            <MapPin className="h-10 w-10 text-zinc-600" />
            <div>
              <p className="font-medium text-white">No boundaries yet</p>
              <p className="mt-1 text-sm text-zinc-500 max-w-xs">
                Edit a municipality and paste its GeoJSON polygon boundary to show it on the map.
              </p>
            </div>
            <Link
              to="/municipalities"
              className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Go to Municipalities
            </Link>
          </div>
        ) : (
          <Suspense fallback={<MapPlaceholder label="Loading map…" />}>
            <MunicipalityMap geojson={geojson!} focusId={focus} metric={metric} onPreview={setPreviewId} incidentPoints={incidentPoints} setPoints={setPoints} />
          </Suspense>
        )}

        {preview && <PreviewCard preview={preview} parent={previewParent} childCount={previewChildCount} onClose={() => setPreviewId(null)} />}
      </div>

      {withoutGeometry.length > 0 && featureCount > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-xs text-amber-400">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            {withoutGeometry.length} municipality{withoutGeometry.length !== 1 ? 'ies have' : 'y has'} no boundary:{' '}
            {withoutGeometry.slice(0, 5).map((m, i) => (
              <span key={m.id}>
                <Link to="/municipalities/$id" params={{ id: m.id }} className="underline hover:text-amber-200">
                  {m.name}
                </Link>
                {i < Math.min(withoutGeometry.length, 5) - 1 && ', '}
              </span>
            ))}
            {withoutGeometry.length > 5 && ` and ${withoutGeometry.length - 5} more`}
          </span>
        </div>
      )}
    </div>
  )
}

function MapPlaceholder({ label }: { label: string }) {
  return (
    <div className="flex h-full items-center justify-center bg-zinc-900">
      <div className="flex flex-col items-center gap-2 text-zinc-500">
        <MapPin className="h-8 w-8 animate-pulse" />
        <span className="text-sm">{label}</span>
      </div>
    </div>
  )
}

function PreviewCard({
  preview, parent, childCount, onClose,
}: {
  preview: MunicipalityListItem
  parent: MunicipalityListItem | null
  childCount: number
  onClose: () => void
}) {
  return (
    <div className="absolute bottom-3 right-3 z-10 w-72 rounded-xl border border-zinc-700 bg-zinc-900/95 p-4 shadow-xl backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 shrink-0 text-zinc-400" />
            <h3 className="truncate text-base font-semibold text-white">{preview.name}</h3>
          </div>
          {parent && (
            <p className="mt-0.5 text-xs text-zinc-500">
              District of <span className="text-zinc-400">{parent.name}</span>
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close preview"
          className="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-2 text-center">
          <div className={`text-lg font-bold tabular-nums ${preview.incident_count > 0 ? 'text-amber-400' : 'text-zinc-500'}`}>
            {preview.incident_count}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-500">Incidents</div>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-2 text-center">
          <div className={`text-lg font-bold tabular-nums ${childCount > 0 ? 'text-white' : 'text-zinc-500'}`}>
            {childCount}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-500">Sub-districts</div>
        </div>
      </div>

      <div className="mt-3 space-y-1.5">
        <Link
          to="/municipalities/$id"
          params={{ id: preview.id }}
          className="flex w-full items-center justify-between rounded-md border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:border-zinc-500 hover:text-white"
        >
          Open detail page
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
        {preview.incident_count > 0 && (
          <Link
            to="/incidents"
            search={{ municipality_id: preview.id }}
            className="flex w-full items-center justify-between rounded-md border border-violet-700/60 bg-violet-950/40 px-3 py-1.5 text-xs font-medium text-violet-300 hover:bg-violet-900/40"
          >
            <span className="inline-flex items-center gap-1.5">
              <ListFilter className="h-3.5 w-3.5" />
              Filter incidents here
            </span>
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        )}
      </div>
    </div>
  )
}
