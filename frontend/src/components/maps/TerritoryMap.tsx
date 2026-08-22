import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { default as MapGL, Layer, Popup, Source, NavigationControl } from 'react-map-gl/maplibre'
import type { MapLayerMouseEvent, MapRef } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import { TerraDraw, TerraDrawPolygonMode } from 'terra-draw'
import { TerraDrawMapLibreGLAdapter } from 'terra-draw-maplibre-gl-adapter'
import { Home } from 'lucide-react'
import unionFeatures from '@turf/union'
import intersect from '@turf/intersect'
import { featureCollection, feature } from '@turf/helpers'
import type { Feature, Polygon, MultiPolygon } from 'geojson'
import { BRAND } from '@/lib/brand'
import { INCIDENT_TYPE_HEX } from '@/lib/statusColors'
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
  /** Called when a single incident pin is clicked. */
  onSelectIncident?: (id: UUID) => void
  /** Numbered markers for address-mode polygon construction. */
  addressMarkers?: { lng: number; lat: number }[]
  viewMode: 'sets' | 'alliances'
  onPolygonComplete: (poly: GeoJSON.Polygon) => void
  onSelectSet: (id: UUID) => void
  /** Reset/zoom signal — when this id changes, refit to the relevant bounds. */
  fitSignal: number
  fallbackCenter?: { longitude: number; latitude: number; zoom: number }
  /** When true, map clicks place a territory pin instead of selecting a set. */
  pinMode?: boolean
  /** Pending pin preview (while user hasn't saved yet). */
  pendingPoint?: { lng: number; lat: number } | null
  /** Color to use for the pending pin preview. Defaults to violet. */
  pendingPointColor?: string | null
  /** Fired when the user clicks to place a pin (only when pinMode=true). */
  onPinPlaced?: (lng: number, lat: number) => void
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
  return status === 'ACTIVE' ? BRAND.strong : '#52525b'
}

// Pick the per-set primary fill color: gang nation color if set, else status fallback.
function setColorOf(s: SetTerritoryPolygon): string {
  return s.gang_color ?? statusColor(s.status)
}

// Secondary stroke color: gang secondary if set, else same as primary.
function setStrokeOf(s: SetTerritoryPolygon): string {
  return s.gang_color_secondary ?? setColorOf(s)
}

// Stripe pattern image id for this set (null when only one color available).
function stripePatternId(s: SetTerritoryPolygon): string | null {
  if (!s.gang_color || !s.gang_color_secondary) return null
  return `stripe-${s.gang_color.replace('#', '')}-${s.gang_color_secondary.replace('#', '')}`
}

// Build a 16×16 diagonal-stripe tile: primary-color lines over secondary fill.
function buildStripeCanvas(primary: string, secondary: string): ImageData {
  const size = 16
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')!
  ctx.fillStyle = secondary
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = primary
  ctx.lineWidth = 5
  for (let i = -size; i < size * 2; i += 8) {
    ctx.beginPath()
    ctx.moveTo(i, 0)
    ctx.lineTo(i + size, size)
    ctx.stroke()
  }
  return ctx.getImageData(0, 0, size, size)
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
  onSelectIncident,
  addressMarkers,
  viewMode,
  onPolygonComplete,
  onSelectSet,
  fitSignal,
  fallbackCenter = { longitude: -83.0458, latitude: 42.3314, zoom: 10 },
  pinMode = false,
  pendingPoint,
  pendingPointColor,
  onPinPlaced,
}: TerritoryMapProps) {
  const mapRef = useRef<MapRef | null>(null)
  const drawRef = useRef<TerraDraw | null>(null)
  const registeredPatternsRef = useRef<Set<string>>(new Set())
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
        const polyMembers = members.filter((m) => m.territory_polygon)
        if (polyMembers.length === 0) continue
        const memberFeatures = polyMembers.map((m) => ({
          type: 'Feature' as const,
          properties: {},
          geometry: m.territory_polygon!,
        }))
        let geom: Polygon | MultiPolygon = polyMembers[0].territory_polygon!
        if (memberFeatures.length > 1) {
          // @turf/union takes a FeatureCollection in newer versions.
          const unioned = unionFeatures(featureCollection(memberFeatures as Feature<Polygon>[]))
          if (unioned) geom = unioned.geometry as Polygon | MultiPolygon
        }
        const allianceColor = `hsl(${hashHue(allianceId)} 70% 55%)`
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
            color: allianceColor,
            strokeColor: allianceColor,
            patternId: null,
            isSelected: members.some((m) => m.id === selectedSetId),
          },
          geometry: geom,
        })
      }
      for (const s of ungrouped) {
        if (!s.territory_polygon) continue
        features.push({
          type: 'Feature',
          id: s.id,
          properties: {
            id: s.id,
            kind: 'set',
            firstSetId: s.id,
            name: s.name,
            color: setColorOf(s),
            strokeColor: setStrokeOf(s),
            patternId: stripePatternId(s),
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
      features: setPolygons.filter((s) => s.territory_polygon).map((s) => ({
        type: 'Feature',
        id: s.id,
        properties: {
          id: s.id,
          kind: 'set',
          firstSetId: s.id,
          name: s.name,
          color: setColorOf(s),
          strokeColor: setStrokeOf(s),
          patternId: stripePatternId(s),
          isSelected: s.id === selectedSetId,
        },
        geometry: s.territory_polygon!,
      })),
    }
  }, [setPolygons, viewMode, selectedSetId])

  // ─── set point markers FeatureCollection ────────────────────────────────
  const setPointsFC = useMemo<GeoJSON.FeatureCollection>(() => ({
    type: 'FeatureCollection',
    features: setPolygons
      .filter((s) => s.territory_point)
      .map((s) => ({
        type: 'Feature' as const,
        id: s.id,
        properties: {
          id: s.id,
          firstSetId: s.id,
          name: s.name,
          color: setColorOf(s),
          isSelected: s.id === selectedSetId,
        },
        geometry: s.territory_point!,
      })),
  }), [setPolygons, selectedSetId])

  const pendingPointFC = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (!pendingPoint) return null
    return {
      type: 'FeatureCollection',
      features: [{
        type: 'Feature' as const,
        properties: {},
        geometry: { type: 'Point' as const, coordinates: [pendingPoint.lng, pendingPoint.lat] },
      }],
    }
  }, [pendingPoint])

  // Detect pairwise polygon intersections (sets view only) to highlight shared territory.
  const sharedFC = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (viewMode !== 'sets') return null
    const polySets = setPolygons.filter((s) => s.territory_polygon)
    const intersections: Feature<Polygon | MultiPolygon>[] = []
    for (let i = 0; i < polySets.length; i++) {
      for (let j = i + 1; j < polySets.length; j++) {
        try {
          const a = feature(polySets[i].territory_polygon)
          const b = feature(polySets[j].territory_polygon)
          const ix = intersect(featureCollection([a, b]))
          if (ix && (ix.geometry.type === 'Polygon' || ix.geometry.type === 'MultiPolygon')) {
            intersections.push({
              type: 'Feature',
              properties: {
                nameA: polySets[i].name,
                nameB: polySets[j].name,
              },
              geometry: ix.geometry as Polygon | MultiPolygon,
            })
          }
        } catch { /* skip degenerate geometries */ }
      }
    }
    if (intersections.length === 0) return null
    return { type: 'FeatureCollection', features: intersections }
  }, [setPolygons, viewMode])

  const incidentFC = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (!incidentPoints.length) return null
    return {
      type: 'FeatureCollection',
      features: incidentPoints.map((p) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
        properties: { id: p.id, incidentType: p.type, label: p.label ?? '' },
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
    const polys = setPolygons.filter((s) => s.territory_polygon).map((s) => s.territory_polygon!)
    const pb = polygonBounds(polys)
    let [minLng, minLat, maxLng, maxLat] = pb
      ? [pb[0][0], pb[0][1], pb[1][0], pb[1][1]]
      : [Infinity, Infinity, -Infinity, -Infinity]
    let found = !!pb
    for (const s of setPolygons) {
      if (!s.territory_point) continue
      const [lng, lat] = s.territory_point.coordinates
      if (lng < minLng) minLng = lng
      if (lat < minLat) minLat = lat
      if (lng > maxLng) maxLng = lng
      if (lat > maxLat) maxLat = lat
      found = true
    }
    return found ? [[minLng, minLat], [maxLng, maxLat]] : null
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

  // Register a custom SDF pin icon once the map is ready.
  useEffect(() => {
    if (!mapReady) return
    const map = mapRef.current?.getMap()
    if (!map || map.hasImage('set-territory-pin')) return
    const w = 22, h = 30
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    // Pin head (circle)
    ctx.fillStyle = 'white'
    ctx.beginPath()
    ctx.arc(w / 2, w / 2 - 1, w / 2 - 1, 0, Math.PI * 2)
    ctx.fill()
    // Pin tail (downward triangle)
    ctx.beginPath()
    ctx.moveTo(w / 2 - 5, w / 2 + 4)
    ctx.lineTo(w / 2, h - 2)
    ctx.lineTo(w / 2 + 5, w / 2 + 4)
    ctx.fill()
    // Inner hole (transparent) — destination-out punches through the white
    ctx.globalCompositeOperation = 'destination-out'
    ctx.beginPath()
    ctx.arc(w / 2, w / 2 - 1, 4, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,0,0,1)'
    ctx.fill()
    ctx.globalCompositeOperation = 'source-over'
    const imageData = ctx.getImageData(0, 0, w, h)
    map.addImage('set-territory-pin', imageData, { sdf: true })
  }, [mapReady])

  // Register diagonal stripe patterns for each unique gang color pair.
  useEffect(() => {
    if (!mapReady) return
    const map = mapRef.current?.getMap()
    if (!map) return
    for (const s of setPolygons) {
      const id = stripePatternId(s)
      if (!id) continue
      if (registeredPatternsRef.current.has(id) || map.hasImage(id)) continue
      map.addImage(id, buildStripeCanvas(s.gang_color!, s.gang_color_secondary!))
      registeredPatternsRef.current.add(id)
    }
  }, [mapReady, setPolygons])

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
    if (f?.layer?.id === 'shared-territory-fill' && f.properties) {
      const { nameA, nameB } = f.properties as { nameA: string; nameB: string }
      setHovered({ id: '' as UUID, name: `${nameA} + ${nameB}`, lng: e.lngLat.lng, lat: e.lngLat.lat })
    } else if (f?.layer?.id === 'incident-points-layer' && f.properties) {
      const { label, incidentType } = f.properties as { label?: string; incidentType?: string }
      setHovered({
        id: (f.properties.id ?? '') as UUID,
        name: label ? `${incidentType === 'MURDER' ? 'Murder' : 'Shooting'}: ${label}` : 'Incident',
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
      })
    } else if (f && f.properties && f.properties.firstSetId) {
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
    if (pinMode) {
      onPinPlaced?.(e.lngLat.lng, e.lngLat.lat)
      return
    }
    if (drawingFor) return
    const f = e.features?.[0]
    if (f?.layer?.id === 'incident-clusters') {
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
    if (f?.layer?.id === 'incident-points-layer' && f.properties?.id) {
      onSelectIncident?.(f.properties.id as UUID)
      return
    }
    if (f?.properties?.firstSetId) {
      onSelectSet(f.properties.firstSetId as UUID)
    }
  }, [drawingFor, pinMode, onPinPlaced, onSelectSet, onSelectIncident])

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
        interactiveLayerIds={drawingFor || pinMode ? [] : ['set-polygons-fill', 'set-polygons-pattern', 'shared-territory-fill', 'incident-clusters', 'incident-points-layer', 'set-points-layer']}
        onMouseMove={onMouseMove}
        onMouseLeave={onMouseLeave}
        onClick={onClick}
        onLoad={() => setMapReady(true)}
        cursor={drawingFor || pinMode ? 'crosshair' : hovered ? 'pointer' : 'grab'}
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
          {/* Solid fill — only for sets without a stripe pattern (no gang, or gang with one color) */}
          <Layer
            id="set-polygons-fill"
            type="fill"
            filter={['==', ['get', 'patternId'], null] as unknown as boolean}
            paint={{
              'fill-color': ['get', 'color'] as unknown as string,
              'fill-opacity': [
                'case',
                ['boolean', ['get', 'isSelected'], false], 0.5,
                0.2,
              ] as unknown as number,
            }}
          />
          {/* Diagonal stripe fill — for gang sets with two colors */}
          <Layer
            id="set-polygons-pattern"
            type="fill"
            filter={['!=', ['get', 'patternId'], null] as unknown as boolean}
            paint={{
              'fill-pattern': ['get', 'patternId'] as unknown as string,
              'fill-opacity': [
                'case',
                ['boolean', ['get', 'isSelected'], false], 0.65,
                0.4,
              ] as unknown as number,
            }}
          />
          <Layer
            id="set-polygons-line"
            type="line"
            paint={{
              'line-color': ['get', 'strokeColor'] as unknown as string,
              'line-width': [
                'case',
                ['boolean', ['get', 'isSelected'], false], 2.5,
                1,
              ] as unknown as number,
              'line-opacity': 0.9,
            }}
          />
        </Source>

        {/* Shared territory overlay — rendered on top of set polygons */}
        {sharedFC && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="shared-territory" type="geojson" data={sharedFC as any}>
            <Layer
              id="shared-territory-fill"
              type="fill"
              paint={{
                'fill-color': '#ffffff',
                'fill-opacity': 0.08,
              }}
            />
            <Layer
              id="shared-territory-line"
              type="line"
              paint={{
                'line-color': '#ffffff',
                'line-width': 1.5,
                'line-opacity': 0.5,
                'line-dasharray': [3, 3],
              }}
            />
          </Source>
        )}

        {/* Incident points (on top of polygons, below draw) */}
        {incidentFC && (
          <Source
            id="incident-points"
            type="geojson"
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            data={incidentFC as any}
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
                'circle-stroke-width': 1.25,
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
                'circle-radius': 5,
                'circle-color': [
                  'match', ['get', 'incidentType'],
                  // Driven by INCIDENT_TYPE_HEX so map dots, chips and charts never drift.
                  ...Object.entries(INCIDENT_TYPE_HEX).flat(),
                  '#a1a1aa',
                ] as unknown as string,
                'circle-stroke-width': 1.25,
                'circle-stroke-color': '#18181b',
                'circle-opacity': 0.85,
              }}
            />
          </Source>
        )}

        {/* Set territory point markers — teardrop pins above polygon layers */}
        {setPointsFC.features.length > 0 && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="set-points" type="geojson" data={setPointsFC as any}>
            <Layer
              id="set-points-layer"
              type="symbol"
              layout={{
                'icon-image': 'set-territory-pin',
                'icon-size': [
                  'case',
                  ['boolean', ['get', 'isSelected'], false], 1.5,
                  1.2,
                ] as unknown as number,
                'icon-anchor': 'bottom',
                'icon-allow-overlap': true,
                'icon-ignore-placement': true,
              }}
              paint={{
                'icon-color': ['get', 'color'] as unknown as string,
                'icon-halo-color': '#ffffff',
                'icon-halo-width': 1,
              }}
            />
          </Source>
        )}

        {/* Pending pin preview (pin mode, before save) */}
        {pendingPointFC && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Source id="pending-point" type="geojson" data={pendingPointFC as any}>
            <Layer
              id="pending-point-layer"
              type="symbol"
              layout={{
                'icon-image': 'set-territory-pin',
                'icon-size': 1.4,
                'icon-anchor': 'bottom',
                'icon-allow-overlap': true,
              }}
              paint={{
                'icon-color': pendingPointColor ?? BRAND.strong,
                'icon-opacity': 0.75,
                'icon-halo-color': '#ffffff',
                'icon-halo-width': 1.5,
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
                'line-color': BRAND.strong,
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
                'circle-color': BRAND.strong,
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
