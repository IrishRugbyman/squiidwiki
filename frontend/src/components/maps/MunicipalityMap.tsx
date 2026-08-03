import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Map, { Layer, Popup, Source, NavigationControl } from 'react-map-gl/maplibre'
import type { MapLayerMouseEvent, MapRef } from 'react-map-gl/maplibre'
import { useNavigate } from '@tanstack/react-router'
import { Home } from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'
import { BRAND } from '@/lib/brand'
import type { GeoJSONGeometry, MunicipalityGeoJSON } from '@/lib/types'

export interface IncidentPoint {
  id: string
  type: 'SHOOTING' | 'MURDER' | 'FIGHT'
  lat: number
  lng: number
}

export interface SetPoint {
  id: string
  status: 'ACTIVE' | 'EXTINCT'
  lat: number
  lng: number
}

const TILE_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

type LngLatBounds = [[number, number], [number, number]]
export type MapMetric = 'sets' | 'incidents'

interface Props {
  geojson: MunicipalityGeoJSON
  /** When set, the matching feature is rendered with the focus colour and the
   *  view fits to its bounds on initial render. */
  focusId?: string
  /** Padding (px) used when the map fits to the full feature collection. */
  fitPadding?: number
  /** Default zoom + center fallback if the geojson has no features. */
  fallbackCenter?: { longitude: number; latitude: number; zoom: number }
  /** Which property to colour by + show in the popup. Defaults to 'sets'. */
  metric?: MapMetric
  /** When provided, click emits the feature id instead of navigating to the
   *  detail page — used for in-place preview overlays. */
  onPreview?: (id: string) => void
  /** Incident points to overlay as coloured dots (MURDER = rose, SHOOTING = amber). */
  incidentPoints?: IncidentPoint[]
  /** Set points to overlay as coloured dots (ACTIVE = violet, EXTINCT = zinc). */
  setPoints?: SetPoint[]
}

interface PopupFeature {
  id: string
  name: string
  incidentCount: number
  setCount: number
  lng: number
  lat: number
}

// ─── geometry helpers ────────────────────────────────────────────────────────

function walkCoords(geom: GeoJSONGeometry, cb: (lng: number, lat: number) => void) {
  if (geom.type === 'Polygon') {
    for (const ring of geom.coordinates as number[][][]) {
      for (const [lng, lat] of ring) cb(lng, lat)
    }
  } else {
    for (const poly of geom.coordinates as number[][][][]) {
      for (const ring of poly) {
        for (const [lng, lat] of ring) cb(lng, lat)
      }
    }
  }
}

function geometryBounds(geom: GeoJSONGeometry): LngLatBounds | null {
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity
  let found = false
  walkCoords(geom, (lng, lat) => {
    if (lng < minLng) minLng = lng
    if (lat < minLat) minLat = lat
    if (lng > maxLng) maxLng = lng
    if (lat > maxLat) maxLat = lat
    found = true
  })
  return found ? [[minLng, minLat], [maxLng, maxLat]] : null
}

function collectionBounds(geojson: MunicipalityGeoJSON): LngLatBounds | null {
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity
  let found = false
  for (const f of geojson.features) {
    if (!f.geometry) continue
    walkCoords(f.geometry, (lng, lat) => {
      if (lng < minLng) minLng = lng
      if (lat < minLat) minLat = lat
      if (lng > maxLng) maxLng = lng
      if (lat > maxLat) maxLat = lat
      found = true
    })
  }
  return found ? [[minLng, minLat], [maxLng, maxLat]] : null
}

// ─── component ───────────────────────────────────────────────────────────────

export default function MunicipalityMap({
  geojson,
  focusId,
  fitPadding = 40,
  fallbackCenter = { longitude: -83.0458, latitude: 42.3314, zoom: 10 },
  metric = 'sets',
  onPreview,
  incidentPoints,
  setPoints,
}: Props) {
  const navigate = useNavigate()
  const mapRef = useRef<MapRef | null>(null)
  const [hovered, setHovered] = useState<PopupFeature | null>(null)

  const metricKey = metric === 'sets' ? 'set_count' : 'incident_count'
  const metricLabel = metric === 'sets' ? 'Sets' : 'Incidents'

  const incidentGeoJSON = useMemo(() => {
    if (!incidentPoints?.length) return null
    return {
      type: 'FeatureCollection' as const,
      features: incidentPoints.map((p) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [p.lng, p.lat] },
        properties: { id: p.id, incidentType: p.type },
      })),
    }
  }, [incidentPoints])

  const setGeoJSON = useMemo(() => {
    if (!setPoints?.length) return null
    return {
      type: 'FeatureCollection' as const,
      features: setPoints.map((p) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [p.lng, p.lat] },
        properties: { id: p.id, setStatus: p.status },
      })),
    }
  }, [setPoints])

  const maxCount = useMemo(
    () => Math.max(1, ...geojson.features.map((f) => f.properties[metricKey])),
    [geojson, metricKey],
  )

  const fullBounds = useMemo(() => collectionBounds(geojson), [geojson])

  // Initial view: fit to focused feature if any, else to whole collection, else fallback center.
  const initialViewState = useMemo(() => {
    if (focusId) {
      const focused = geojson.features.find((f) => f.id === focusId)
      if (focused?.geometry) {
        const b = geometryBounds(focused.geometry)
        if (b) return { bounds: b, fitBoundsOptions: { padding: fitPadding } }
      }
    }
    if (fullBounds) {
      return { bounds: fullBounds, fitBoundsOptions: { padding: fitPadding } }
    }
    return fallbackCenter
  }, [focusId, geojson, fullBounds, fitPadding, fallbackCenter])

  // Re-fit when the feature collection changes (e.g. universe switch).
  // Skip the very first run because initialViewState already handles it.
  const skipFirstFit = useRef(true)
  useEffect(() => {
    if (skipFirstFit.current) {
      skipFirstFit.current = false
      return
    }
    if (mapRef.current && fullBounds && !focusId) {
      mapRef.current.fitBounds(fullBounds, { padding: fitPadding, duration: 600 })
    }
  }, [fullBounds, fitPadding, focusId])

  // ─── layers ──────────────────────────────────────────────────────────────

  const fillLayer = useMemo(
    () => ({
      id: 'municipalities-fill',
      type: 'fill' as const,
      paint: {
        'fill-color': [
          'case',
          ['==', ['get', 'id'], focusId ?? ''],
          BRAND.strong,
          ['interpolate', ['linear'],
            ['get', metricKey],
            0, '#27272a',
            maxCount, '#5b21b6',
          ],
        ] as unknown as string,
        'fill-opacity': [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.75,
          ['==', ['get', 'id'], focusId ?? ''],
          0.6,
          0.45,
        ] as unknown as number,
      },
    }),
    [maxCount, focusId, metricKey],
  )

  const lineLayer = useMemo(
    () => ({
      id: 'municipalities-line',
      type: 'line' as const,
      paint: {
        'line-color': [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          BRAND.light,
          ['==', ['get', 'id'], focusId ?? ''],
          BRAND.light,
          '#52525b',
        ] as unknown as string,
        'line-width': [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          2.5,
          ['==', ['get', 'id'], focusId ?? ''],
          2,
          1,
        ] as unknown as number,
      },
    }),
    [focusId],
  )

  // ─── interaction ─────────────────────────────────────────────────────────

  const hoverFeatureId = useRef<string | null>(null)

  const setHoverState = useCallback((id: string | null) => {
    const map = mapRef.current?.getMap()
    if (!map) return
    if (hoverFeatureId.current && hoverFeatureId.current !== id) {
      map.setFeatureState({ source: 'municipalities', id: hoverFeatureId.current }, { hover: false })
    }
    if (id && hoverFeatureId.current !== id) {
      map.setFeatureState({ source: 'municipalities', id }, { hover: true })
    }
    hoverFeatureId.current = id
  }, [])

  const onMouseMove = useCallback((e: MapLayerMouseEvent) => {
    const f = e.features?.find((feat) => feat.layer?.id === 'municipalities-fill')
    if (f) {
      const id = f.properties.id as string
      setHoverState(id)
      setHovered({
        id,
        name: f.properties.name as string,
        incidentCount: f.properties.incident_count as number,
        setCount: f.properties.set_count as number,
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
      })
    } else {
      setHoverState(null)
      setHovered(null)
    }
  }, [setHoverState])

  const onMouseLeave = useCallback(() => {
    setHoverState(null)
    setHovered(null)
  }, [setHoverState])

  const onClick = useCallback((e: MapLayerMouseEvent) => {
    if (!e.features || e.features.length === 0) return
    const f = e.features[0]
    if (f.layer?.id === 'incident-clusters') {
      const map = mapRef.current?.getMap()
      const clusterId = (f.properties as { cluster_id?: number }).cluster_id
      if (!map || clusterId == null) return
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const src = map.getSource('incident-points') as any
      src?.getClusterExpansionZoom?.(clusterId, (err: unknown, zoom: number) => {
        if (err) return
        const [lng, lat] = (f.geometry as unknown as { coordinates: [number, number] }).coordinates
        map.easeTo({ center: [lng, lat], zoom: zoom + 0.2, duration: 500 })
      })
      return
    }
    if (f.layer?.id === 'municipalities-fill') {
      const id = f.properties.id as string
      if (onPreview) {
        onPreview(id)
      } else {
        navigate({ to: '/municipalities/$id', params: { id } })
      }
    }
  }, [navigate, onPreview])

  const resetView = useCallback(() => {
    if (mapRef.current && fullBounds) {
      mapRef.current.fitBounds(fullBounds, { padding: fitPadding, duration: 700 })
    }
  }, [fullBounds, fitPadding])

  // ─── render ──────────────────────────────────────────────────────────────

  return (
    <div className="relative h-full w-full">
      <Map
        ref={(r) => { mapRef.current = r }}
        initialViewState={initialViewState}
        style={{ width: '100%', height: '100%' }}
        mapStyle={TILE_STYLE}
        interactiveLayerIds={['municipalities-fill', 'incident-clusters']}
        onMouseMove={onMouseMove}
        onMouseLeave={onMouseLeave}
        onClick={onClick}
        cursor={hovered ? 'pointer' : 'grab'}
      >
        <NavigationControl position="top-right" />

        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        <Source id="municipalities" type="geojson" data={geojson as any} promoteId="id">
          <Layer {...fillLayer} />
          <Layer {...lineLayer} />
        </Source>

        {setGeoJSON && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="set-points" type="geojson" data={setGeoJSON as any}>
            <Layer
              id="set-points-layer"
              type="circle"
              paint={{
                'circle-radius': 5,
                'circle-color': [
                  'match', ['get', 'setStatus'],
                  'ACTIVE', BRAND.strong,
                  '#52525b',
                ] as unknown as string,
                'circle-stroke-width': 1.5,
                'circle-stroke-color': '#18181b',
                'circle-opacity': 0.9,
              }}
            />
          </Source>
        )}

        {incidentGeoJSON && (
          <Source
            id="incident-points"
            type="geojson"
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            data={incidentGeoJSON as any}
            cluster
            clusterMaxZoom={13}
            clusterRadius={45}
          >
            <Layer
              id="incident-clusters"
              type="circle"
              filter={['has', 'point_count']}
              paint={{
                'circle-color': [
                  'step', ['get', 'point_count'],
                  '#fbbf24', 10,
                  '#fb923c', 50,
                  '#fb7185',
                ] as unknown as string,
                'circle-radius': [
                  'step', ['get', 'point_count'],
                  14, 10,
                  18, 50,
                  24,
                ] as unknown as number,
                'circle-stroke-width': 1.5,
                'circle-stroke-color': '#18181b',
                'circle-opacity': 0.9,
              }}
            />
            <Layer
              id="incident-cluster-count"
              type="symbol"
              filter={['has', 'point_count']}
              layout={{
                'text-field': ['get', 'point_count_abbreviated'] as unknown as string,
                'text-font': ['Open Sans Semibold', 'Arial Unicode MS Bold'],
                'text-size': 12,
              }}
              paint={{
                'text-color': '#18181b',
              }}
            />
            <Layer
              id="incident-points-layer"
              type="circle"
              filter={['!', ['has', 'point_count']]}
              paint={{
                'circle-radius': 6,
                'circle-color': [
                  'match', ['get', 'incidentType'],
                  'MURDER', '#fb7185',
                  'FIGHT', BRAND.light,
                  '#fbbf24',
                ] as unknown as string,
                'circle-stroke-width': 1.5,
                'circle-stroke-color': '#18181b',
                'circle-opacity': 0.85,
              }}
            />
          </Source>
        )}

        {hovered && (
          <Popup
            latitude={hovered.lat}
            longitude={hovered.lng}
            closeButton={false}
            anchor="bottom"
            offset={8}
          >
            <div className="px-3 py-2 min-w-[140px]">
              <p className="font-medium text-sm text-white">{hovered.name}</p>
              <p className="text-xs text-zinc-400 mt-0.5 tabular-nums">
                <span className="text-zinc-200">{hovered.setCount}</span> set{hovered.setCount !== 1 ? 's' : ''}
                <span className="text-zinc-500"> · </span>
                <span className="text-zinc-200">{hovered.incidentCount}</span> incident{hovered.incidentCount !== 1 ? 's' : ''}
              </p>
            </div>
          </Popup>
        )}
      </Map>

      {/* reset view */}
      {fullBounds && (
        <button
          onClick={resetView}
          className="absolute left-3 top-3 z-10 inline-flex items-center gap-1.5 rounded-md border border-zinc-700 bg-zinc-900/80 px-2.5 py-1.5 text-xs font-medium text-zinc-300 backdrop-blur transition-colors hover:border-zinc-500 hover:text-white"
          aria-label="Reset view"
        >
          <Home className="h-3.5 w-3.5" />
          Reset view
        </button>
      )}

      {/* legend */}
      <div className="absolute bottom-3 left-3 z-10 rounded-md border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-[11px] text-zinc-300 backdrop-blur">
        <p className="mb-1 text-zinc-400">{metricLabel}</p>
        <div
          className="h-1.5 w-32 rounded-full"
          style={{ background: 'linear-gradient(to right, #27272a, #5b21b6)' }}
        />
        <div className="mt-1 flex justify-between text-zinc-400">
          <span>0</span>
          <span className="tabular-nums">{maxCount}</span>
        </div>
      </div>
    </div>
  )
}
