import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { default as MapGL, Layer, Popup, Source, NavigationControl } from 'react-map-gl/maplibre'
import type { MapLayerMouseEvent, MapRef } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import { TerraDraw, TerraDrawPolygonMode } from 'terra-draw'
import { TerraDrawMapLibreGLAdapter } from 'terra-draw-maplibre-gl-adapter'
import { Home } from 'lucide-react'
import unionFeatures from '@turf/union'
import { featureCollection } from '@turf/helpers'
import type { Feature, Polygon, MultiPolygon } from 'geojson'
import type { MunicipalityGeoJSON, SetTerritoryPolygon, UUID } from '@/lib/types'
import type { IncidentPoint } from './MunicipalityMap'

const TILE_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

type LngLatBounds = [[number, number], [number, number]]

export interface TerritoryMapProps {
  setPolygons: SetTerritoryPolygon[]
  selectedSetId: UUID | null
  /** When non-null, the user is editing this set's polygon. Activates terra-draw. */
  drawingFor: UUID | null
  /** Existing polygon to seed the draw layer with (edit mode). */
  initialPolygon: GeoJSON.Polygon | null
  /** Optional sub-district outlines for spatial reference. Toggle off → null. */
  subDistrictGeoJSON: MunicipalityGeoJSON | null
  showSubDistrictOutlines: boolean
  /** Optional incident points overlay. */
  incidentPoints: IncidentPoint[]
  /** Numbered markers for address-mode polygon construction. */
  addressMarkers?: { lng: number; lat: number }[]
  viewMode: 'sets' | 'alliances'
  onPolygonComplete: (poly: GeoJSON.Polygon) => void
  onSelectSet: (id: UUID) => void
  /** Reset/zoom signal — when this id changes, refit to the relevant bounds. */
  fitSignal: number
  fallbackCenter?: { longitude: number; latitude: number; zoom: number }
}

// ─── helpers ────────────────────────────────────────────────────────────────

function walkRings(coords: number[][][], cb: (lng: number, lat: number) => void) {
  for (const ring of coords) for (const [lng, lat] of ring) cb(lng, lat)
}

function polygonBounds(polys: GeoJSON.Polygon[]): LngLatBounds | null {
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity
  let found = false
  for (const p of polys) {
    walkRings(p.coordinates as number[][][], (lng, lat) => {
      if (lng < minLng) minLng = lng
      if (lat < minLat) minLat = lat
      if (lng > maxLng) maxLng = lng
      if (lat > maxLat) maxLat = lat
      found = true
    })
  }
  return found ? [[minLng, minLat], [maxLng, maxLat]] : null
}

// Stable color per alliance id (deterministic so the same alliance always
// gets the same hue across renders and reloads).
function hashHue(id: string): number {
  let h = 0
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0
  return Math.abs(h) % 360
}

function statusColor(status: 'ACTIVE' | 'EXTINCT'): string {
  return status === 'ACTIVE' ? '#7c3aed' : '#52525b'
}

// Pick the per-set color: gang nation color if set, else status fallback.
function setColorOf(s: SetTerritoryPolygon): string {
  return s.gang_color ?? statusColor(s.status)
}

// ─── component ───────────────────────────────────────────────────────────────

export default function TerritoryMap({
  setPolygons,
  selectedSetId,
  drawingFor,
  initialPolygon,
  subDistrictGeoJSON,
  showSubDistrictOutlines,
  incidentPoints,
  addressMarkers,
  viewMode,
  onPolygonComplete,
  onSelectSet,
  fitSignal,
  fallbackCenter = { longitude: -83.0458, latitude: 42.3314, zoom: 10 },
}: TerritoryMapProps) {
  const mapRef = useRef<MapRef | null>(null)
  const drawRef = useRef<TerraDraw | null>(null)
  const [hovered, setHovered] = useState<{ id: UUID; name: string; lng: number; lat: number } | null>(null)
  const [mapReady, setMapReady] = useState(false)

  // ─── set polygons FeatureCollection ──────────────────────────────────────
  // In alliance view, union polygons that share an alliance_id; ungrouped sets
  // (no alliance) keep their individual polygons.
  const setsFC = useMemo<GeoJSON.FeatureCollection>(() => {
    if (viewMode === 'alliances') {
      const byAlliance = new Map<string, SetTerritoryPolygon[]>()
      const ungrouped: SetTerritoryPolygon[] = []
      for (const s of setPolygons) {
        if (s.alliance_id) {
          const k = s.alliance_id
          if (!byAlliance.has(k)) byAlliance.set(k, [])
          byAlliance.get(k)!.push(s)
        } else {
          ungrouped.push(s)
        }
      }
      const features: Feature<Polygon | MultiPolygon>[] = []
      for (const [allianceId, members] of byAlliance) {
        const memberFeatures = members.map((m) => ({
          type: 'Feature' as const,
          properties: {},
          geometry: m.territory_polygon,
        }))
        let geom: Polygon | MultiPolygon = members[0].territory_polygon
        if (memberFeatures.length > 1) {
          // @turf/union takes a FeatureCollection in newer versions.
          const unioned = unionFeatures(featureCollection(memberFeatures as Feature<Polygon>[]))
          if (unioned) geom = unioned.geometry as Polygon | MultiPolygon
        }
        features.push({
          type: 'Feature',
          id: `alliance:${allianceId}`,
          properties: {
            id: `alliance:${allianceId}`,
            kind: 'alliance',
            allianceId,
            // For click → select first member set; sidebar handles alliance-level UI.
            firstSetId: members[0].id,
            name: members.map((m) => m.name).join(' / '),
            color: `hsl(${hashHue(allianceId)} 70% 55%)`,
            isSelected: members.some((m) => m.id === selectedSetId),
          },
          geometry: geom,
        })
      }
      for (const s of ungrouped) {
        features.push({
          type: 'Feature',
          id: s.id,
          properties: {
            id: s.id,
            kind: 'set',
            firstSetId: s.id,
            name: s.name,
            color: setColorOf(s),
            isSelected: s.id === selectedSetId,
          },
          geometry: s.territory_polygon,
        })
      }
      return { type: 'FeatureCollection', features }
    }
    // Sets view: one feature per set, gang-tinted (status fallback).
    return {
      type: 'FeatureCollection',
      features: setPolygons.map((s) => ({
        type: 'Feature',
        id: s.id,
        properties: {
          id: s.id,
          kind: 'set',
          firstSetId: s.id,
          name: s.name,
          color: setColorOf(s),
          isSelected: s.id === selectedSetId,
        },
        geometry: s.territory_polygon,
      })),
    }
  }, [setPolygons, viewMode, selectedSetId])

  const incidentFC = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (!incidentPoints.length) return null
    return {
      type: 'FeatureCollection',
      features: incidentPoints.map((p) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
        properties: { id: p.id, incidentType: p.type },
      })),
    }
  }, [incidentPoints])

  // Address-mode markers (and the open ring connecting them) — rendered as a
  // preview while the user is composing a polygon by address.
  const markerFC = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (!addressMarkers || addressMarkers.length === 0) return null
    return {
      type: 'FeatureCollection',
      features: addressMarkers.map((m, i) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [m.lng, m.lat] },
        properties: { idx: i + 1 },
      })),
    }
  }, [addressMarkers])

  const markerLineFC = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (!addressMarkers || addressMarkers.length < 2) return null
    const coords = addressMarkers.map((m) => [m.lng, m.lat])
    // If ≥3, close the ring visually as a polygon outline preview.
    if (addressMarkers.length >= 3) coords.push([addressMarkers[0].lng, addressMarkers[0].lat])
    return {
      type: 'FeatureCollection',
      features: [{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: coords } }],
    }
  }, [addressMarkers])

  // ─── bounds + initial view ───────────────────────────────────────────────

  const allBounds = useMemo<LngLatBounds | null>(() => {
    const polys: GeoJSON.Polygon[] = setPolygons.map((s) => s.territory_polygon)
    return polygonBounds(polys)
  }, [setPolygons])

  const initialViewState = useMemo(() => {
    if (allBounds) return { bounds: allBounds, fitBoundsOptions: { padding: 60 } }
    return fallbackCenter
  }, [allBounds, fallbackCenter])

  // Refit when `fitSignal` changes (sidebar select / reset button).
  useEffect(() => {
    if (!mapRef.current) return
    if (allBounds) {
      mapRef.current.fitBounds(allBounds, { padding: 60, duration: 600 })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fitSignal])

  // ─── terra-draw lifecycle ────────────────────────────────────────────────

  // Mount the draw instance once the map is ready; tear it down on unmount.
  useEffect(() => {
    if (!mapReady) return
    const map = mapRef.current?.getMap()
    if (!map) return

    const draw = new TerraDraw({
      adapter: new TerraDrawMapLibreGLAdapter({ map }),
      modes: [new TerraDrawPolygonMode()],
    })
    draw.on('finish', (id) => {
      const snap = draw.getSnapshotFeature(id)
      if (snap?.geometry?.type === 'Polygon') {
        onPolygonComplete(snap.geometry as GeoJSON.Polygon)
      }
    })
    drawRef.current = draw
    return () => {
      try { draw.stop() } catch { /* not started */ }
      drawRef.current = null
    }
    // onPolygonComplete deliberately omitted — we use the latest closure via ref.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapReady])

  // Toggle drawing on/off when `drawingFor` flips, and seed initial polygon.
  useEffect(() => {
    const draw = drawRef.current
    if (!draw) return
    if (drawingFor) {
      if (!draw.enabled) draw.start()
      draw.setMode('polygon')
      draw.clear()
      if (initialPolygon) {
        draw.addFeatures([
          { type: 'Feature', properties: { mode: 'polygon' }, geometry: initialPolygon },
        ])
      }
    } else {
      if (draw.enabled) {
        try { draw.clear() } catch { /* noop */ }
        try { draw.stop() } catch { /* noop */ }
      }
    }
  }, [drawingFor, initialPolygon])

  // ─── interaction ─────────────────────────────────────────────────────────

  const onMouseMove = useCallback((e: MapLayerMouseEvent) => {
    if (drawingFor) return
    const f = e.features?.[0]
    if (f && f.properties && f.properties.firstSetId) {
      setHovered({
        id: f.properties.firstSetId as UUID,
        name: f.properties.name as string,
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
      })
    } else {
      setHovered(null)
    }
  }, [drawingFor])

  const onMouseLeave = useCallback(() => setHovered(null), [])

  const onClick = useCallback((e: MapLayerMouseEvent) => {
    if (drawingFor) return
    const f = e.features?.[0]
    if (f?.properties?.firstSetId) {
      onSelectSet(f.properties.firstSetId as UUID)
    }
  }, [drawingFor, onSelectSet])

  const resetView = useCallback(() => {
    if (mapRef.current && allBounds) {
      mapRef.current.fitBounds(allBounds, { padding: 60, duration: 700 })
    }
  }, [allBounds])

  // ─── render ──────────────────────────────────────────────────────────────

  return (
    <div className="relative h-full w-full">
      <MapGL
        ref={(r) => { mapRef.current = r }}
        initialViewState={initialViewState}
        style={{ width: '100%', height: '100%' }}
        mapStyle={TILE_STYLE}
        interactiveLayerIds={drawingFor ? [] : ['set-polygons-fill']}
        onMouseMove={onMouseMove}
        onMouseLeave={onMouseLeave}
        onClick={onClick}
        onLoad={() => setMapReady(true)}
        cursor={drawingFor ? 'crosshair' : hovered ? 'pointer' : 'grab'}
      >
        <NavigationControl position="top-right" />

        {/* Sub-district outlines (off by default) */}
        {showSubDistrictOutlines && subDistrictGeoJSON && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="subdistricts" type="geojson" data={subDistrictGeoJSON as any}>
            <Layer
              id="subdistricts-line"
              type="line"
              paint={{
                'line-color': '#52525b',
                'line-width': 1,
                'line-opacity': 0.6,
              }}
            />
          </Source>
        )}

        {/* Set polygons */}
        <Source id="set-polygons" type="geojson" data={setsFC} promoteId="id">
          <Layer
            id="set-polygons-fill"
            type="fill"
            paint={{
              'fill-color': ['get', 'color'] as unknown as string,
              'fill-opacity': [
                'case',
                ['boolean', ['get', 'isSelected'], false], 0.5,
                0.2,
              ] as unknown as number,
            }}
          />
          <Layer
            id="set-polygons-line"
            type="line"
            paint={{
              'line-color': ['get', 'color'] as unknown as string,
              'line-width': [
                'case',
                ['boolean', ['get', 'isSelected'], false], 2.5,
                1,
              ] as unknown as number,
              'line-opacity': 0.9,
            }}
          />
        </Source>

        {/* Incident points (on top of polygons, below draw) */}
        {incidentFC && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="incident-points" type="geojson" data={incidentFC as any}>
            <Layer
              id="incident-points-layer"
              type="circle"
              paint={{
                'circle-radius': 5,
                'circle-color': [
                  'match', ['get', 'incidentType'],
                  'MURDER', '#fb7185',
                  'FIGHT', '#a78bfa',
                  '#fbbf24',
                ] as unknown as string,
                'circle-stroke-width': 1.25,
                'circle-stroke-color': '#18181b',
                'circle-opacity': 0.85,
              }}
            />
          </Source>
        )}

        {/* Address-mode preview: connecting line + numbered markers */}
        {markerLineFC && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="address-line" type="geojson" data={markerLineFC as any}>
            <Layer
              id="address-line-layer"
              type="line"
              paint={{
                'line-color': '#7c3aed',
                'line-width': 2,
                'line-dasharray': [2, 2],
                'line-opacity': 0.9,
              }}
            />
          </Source>
        )}
        {markerFC && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="address-markers" type="geojson" data={markerFC as any}>
            <Layer
              id="address-markers-circle"
              type="circle"
              paint={{
                'circle-radius': 10,
                'circle-color': '#7c3aed',
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff',
              }}
            />
            <Layer
              id="address-markers-label"
              type="symbol"
              layout={{
                'text-field': ['to-string', ['get', 'idx']] as unknown as string,
                'text-size': 12,
                'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
                'text-allow-overlap': true,
                'text-ignore-placement': true,
              }}
              paint={{
                'text-color': '#ffffff',
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
            <div className="px-3 py-1.5">
              <p className="text-sm font-medium text-white">{hovered.name}</p>
            </div>
          </Popup>
        )}
      </MapGL>

      {allBounds && (
        <button
          onClick={resetView}
          className="absolute left-3 top-3 z-10 inline-flex items-center gap-1.5 rounded-md border border-zinc-700 bg-zinc-900/80 px-2.5 py-1.5 text-xs font-medium text-zinc-300 backdrop-blur transition-colors hover:border-zinc-500 hover:text-white"
          aria-label="Reset view"
        >
          <Home className="h-3.5 w-3.5" />
          Reset view
        </button>
      )}
    </div>
  )
}
