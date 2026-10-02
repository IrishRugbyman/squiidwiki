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
import { INCIDENT_TYPE_LABEL } from '@/lib/incidentColors'
import { groundKey, groupBySameGround, nextSetOnClick } from '@/lib/sharedGround'
import { INCIDENT_TYPE_HEX } from '@/lib/statusColors'
import type { IncidentType, MunicipalityGeoJSON, SetTerritoryPolygon, UUID } from '@/lib/types'
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

// Every vertex of a territory, whether it is one polygon or several pieces.
function walkTerritory(t: GeoJSON.Polygon | GeoJSON.MultiPolygon, cb: (lng: number, lat: number) => void) {
  if (t.type === 'Polygon') walkRings(t.coordinates as number[][][], cb)
  else for (const piece of t.coordinates) walkRings(piece as number[][][], cb)
}

function polygonBounds(polys: (GeoJSON.Polygon | GeoJSON.MultiPolygon)[]): LngLatBounds | null {
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity
  let found = false
  for (const p of polys) {
    walkTerritory(p, (lng, lat) => {
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

/** The colours a set's ground is striped in, or null for a solid fill.
 *
 *  A set claiming several gangs (NBD: Gangster Disciples and Satan Disciples)
 *  shows each gang's main colour, so both cards read at a glance. A set with
 *  one gang shows that gang's own two colours. */
function stripeColors(s: SetTerritoryPolygon): string[] | null {
  const distinct = [...new Set((s.gang_colors ?? []).map((c) => c.toLowerCase()))]
  if (distinct.length >= 2) return distinct.slice(0, 4)
  if (s.gang_color && s.gang_color_secondary && s.gang_color.toLowerCase() !== s.gang_color_secondary.toLowerCase()) {
    return [s.gang_color, s.gang_color_secondary]
  }
  return null
}

// Stripe pattern image id for this set (null when only one color available).
function stripePatternId(s: SetTerritoryPolygon): string | null {
  const colors = stripeColors(s)
  return colors ? `stripe-${colors.map((c) => c.replace('#', '')).join('-')}` : null
}

// Build a 16×16 diagonal-stripe tile: primary-color lines over secondary fill.
/** The teardrop pin, drawn white so an SDF icon can take any colour. */
function buildPinImage(): ImageData | null {
  const w = 22, h = 30
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) return null
  ctx.fillStyle = 'white'
  ctx.beginPath()
  ctx.arc(w / 2, w / 2 - 1, w / 2 - 1, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.moveTo(w / 2 - 5, w / 2 + 4)
  ctx.lineTo(w / 2, h - 2)
  ctx.lineTo(w / 2 + 5, w / 2 + 4)
  ctx.fill()
  // Punch the hole through the head.
  ctx.globalCompositeOperation = 'destination-out'
  ctx.beginPath()
  ctx.arc(w / 2, w / 2 - 1, 4, 0, Math.PI * 2)
  ctx.fillStyle = 'rgba(0,0,0,1)'
  ctx.fill()
  ctx.globalCompositeOperation = 'source-over'
  return ctx.getImageData(0, 0, w, h)
}

const STRIPE_ID = /^stripe-([0-9a-fA-F]{3,8}(?:-[0-9a-fA-F]{3,8}){1,3})$/

/** A seamless tile of diagonal bands. Two colours keep the original look (the
 *  primary as narrow lines over the secondary); three or four, from a set
 *  claiming several gangs, cycle in equal bands. */
function buildStripeCanvas(colors: string[]): ImageData {
  const band = 8
  const size = colors.length === 2 ? 16 : band * colors.length
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')!
  if (colors.length === 2) {
    ctx.fillStyle = colors[1]
    ctx.fillRect(0, 0, size, size)
    ctx.strokeStyle = colors[0]
    ctx.lineWidth = 5
    for (let i = -size; i < size * 2; i += band) {
      ctx.beginPath()
      ctx.moveTo(i, 0)
      ctx.lineTo(i + size, size)
      ctx.stroke()
    }
    return ctx.getImageData(0, 0, size, size)
  }
  // Equal bands: pixel (x, y) takes the colour of its diagonal (x + y), which
  // repeats every `size` pixels in both directions, so the tile is seamless.
  for (let x = 0; x < size; x++) {
    for (let y = 0; y < size; y++) {
      ctx.fillStyle = colors[Math.floor(((x + y) % size) / band)]
      ctx.fillRect(x, y, 1, 1)
    }
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
  const [hovered, setHovered] = useState<{ id: UUID; name: string; lng: number; lat: number } | null>(null)
  const [mapReady, setMapReady] = useState(false)

  // ─── set polygons FeatureCollection ──────────────────────────────────────
  // In alliance view, union the polygons of each alliance's sets; a set in two
  // alliances is drawn into both. Sets in none keep their individual polygons.
  const setsFC = useMemo<GeoJSON.FeatureCollection>(() => {
    if (viewMode === 'alliances') {
      const byAlliance = new Map<string, SetTerritoryPolygon[]>()
      const ungrouped: SetTerritoryPolygon[] = []
      for (const s of setPolygons) {
        const ids = s.alliance_ids?.length ? s.alliance_ids : s.alliance_id ? [s.alliance_id] : []
        if (ids.length === 0) ungrouped.push(s)
        for (const k of ids) {
          if (!byAlliance.has(k)) byAlliance.set(k, [])
          byAlliance.get(k)!.push(s)
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
          const unioned = unionFeatures(featureCollection(memberFeatures as Feature<Polygon | MultiPolygon>[]))
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
    // Sets view: one feature per territory, gang-tinted (status fallback).
    // Sets that hold the very same ground (264, 752 and YS all carry the
    // Villages at Parkside outline) are drawn once: three stacked copies
    // tripled the fill and left only the top one reachable. `setIds` lists
    // them all so a click can cycle through, and the one selected (or else the
    // first) lends the shape its colour and its click target.
    return {
      type: 'FeatureCollection',
      features: groupBySameGround(setPolygons).map((group) => {
        const lead = group.find((s) => s.id === selectedSetId) ?? group[0]
        const ids = group.map((s) => s.id)
        return {
          type: 'Feature',
          id: ids.join(','),
          properties: {
            id: ids.join(','),
            kind: 'set',
            firstSetId: lead.id,
            setIds: ids.join(','),
            name: group.map((s) => s.name).join(' / '),
            color: setColorOf(lead),
            strokeColor: setStrokeOf(lead),
            patternId: stripePatternId(lead),
            isSelected: ids.includes(selectedSetId as UUID),
          },
          geometry: lead.territory_polygon!,
        }
      }),
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
        // Identical ground is already one merged shape (see setsFC); an
        // overlay over all of it would only hide that shape from clicks.
        if (groundKey(polySets[i]) === groundKey(polySets[j])) continue
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

  // Refit when `fitSignal` changes (sidebar select / reset button): to the
  // selected set's own boundary or pin when it has one, else to everything.
  // It used to refit to every loaded polygon, so picking a set never moved
  // the map to that set.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const sel = selectedSetId ? setPolygons.find((s) => s.id === selectedSetId) : undefined
    if (sel?.territory_polygon) {
      const b = polygonBounds([sel.territory_polygon])
      if (b) {
        map.fitBounds(b, { padding: 80, duration: 600, maxZoom: 15 })
        return
      }
    }
    if (sel?.territory_point) {
      const [lng, lat] = sel.territory_point.coordinates
      map.flyTo({ center: [lng, lat], zoom: Math.max(map.getZoom(), 14), duration: 600 })
      return
    }
    if (allBounds) map.fitBounds(allBounds, { padding: 60, duration: 600 })
    // Also on selectedSetId: the selection arrives through the URL, which can
    // land a render after the signal, and the fit must see the new set.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fitSignal, selectedSetId])

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
    if (f?.layer?.id === 'shared-territory-fill' && f.properties) {
      const { nameA, nameB } = f.properties as { nameA: string; nameB: string }
      setHovered({ id: '' as UUID, name: `${nameA} + ${nameB}`, lng: e.lngLat.lng, lat: e.lngLat.lat })
    } else if (f?.layer?.id === 'incident-points-layer' && f.properties) {
      const { label, incidentType } = f.properties as { label?: string; incidentType?: string }
      setHovered({
        id: (f.properties.id ?? '') as UUID,
        name: label
          ? `${INCIDENT_TYPE_LABEL[incidentType as IncidentType] ?? 'Incident'}: ${label}`
          : 'Incident',
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
    // The shared-territory overlay sits on top and names no set, so a click in
    // an overlap reaches through it to the first set shape underneath.
    const setHit = e.features?.find((x) => x.properties?.firstSetId)
    if (!setHit) return
    const lead = setHit.properties.firstSetId as UUID
    const ids = String(setHit.properties.setIds ?? lead).split(',') as UUID[]
    onSelectSet(nextSetOnClick(ids, selectedSetId, lead))
  }, [drawingFor, pinMode, onPinPlaced, onSelectSet, onSelectIncident, selectedSetId])

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
        onLoad={(e) => {
          // Images are registered here, before any layer that uses them can
          // mount (those wait for mapReady). Registered from effects instead,
          // they always arrived after the layers, since React runs a child's
          // effects first, and maplibre warned of each missing image.
          const map = e.target
          const pin = buildPinImage()
          if (pin && !map.hasImage('set-territory-pin')) map.addImage('set-territory-pin', pin, { sdf: true })
          // Stripe patterns are made on demand: a set's two gang colours are in its pattern id.
          map.on('styleimagemissing', (ev: { id: string }) => {
            const m = STRIPE_ID.exec(ev.id)
            if (m && !map.hasImage(ev.id)) map.addImage(ev.id, buildStripeCanvas(m[1].split('-').map((h) => `#${h}`)))
          })
          setMapReady(true)
        }}
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
          {/* Diagonal stripe fill, for gang sets with two colours. After load,
              when its patterns can be supplied. */}
          {mapReady && <Layer
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
          />}
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
        {mapReady && setPointsFC.features.length > 0 && (
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
        {mapReady && pendingPointFC && (
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
