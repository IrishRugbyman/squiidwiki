import { useCallback, useMemo, useState } from 'react'
import Map, { Layer, Popup, Source, NavigationControl } from 'react-map-gl/maplibre'
import { useNavigate } from '@tanstack/react-router'
import type { MapLayerMouseEvent } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { GeoJSONGeometry, MunicipalityGeoJSON } from '@/lib/types'

const TILE_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

interface Props {
  geojson: MunicipalityGeoJSON
  focusId?: string
}

interface HoveredFeature {
  id: string
  name: string
  incidentCount: number
  lng: number
  lat: number
}

function centroid(geometry: GeoJSONGeometry): [number, number] {
  const coords = geometry.type === 'Polygon'
    ? (geometry.coordinates as number[][][])[0]
    : (geometry.coordinates as number[][][][])[0][0]
  const lng = coords.reduce((s, c) => s + c[0], 0) / coords.length
  const lat = coords.reduce((s, c) => s + c[1], 0) / coords.length
  return [lng, lat]
}

export default function MunicipalityMap({ geojson, focusId }: Props) {
  const navigate = useNavigate()
  const [hovered, setHovered] = useState<HoveredFeature | null>(null)

  const maxCount = useMemo(
    () => Math.max(1, ...geojson.features.map((f) => f.properties.incident_count)),
    [geojson],
  )

  const initialViewState = useMemo(() => {
    const focused = focusId ? geojson.features.find((f) => f.id === focusId) : null
    if (focused) {
      const [lng, lat] = centroid(focused.geometry)
      return { longitude: lng, latitude: lat, zoom: 12 }
    }
    if (geojson.features.length > 0) {
      const [lng, lat] = centroid(geojson.features[0].geometry)
      return { longitude: lng, latitude: lat, zoom: 10 }
    }
    return { longitude: -74.006, latitude: 40.7128, zoom: 10 }
  }, [focusId, geojson])

  const fillLayer = useMemo(
    () => ({
      id: 'municipalities-fill',
      type: 'fill' as const,
      paint: {
        'fill-color': [
          'case',
          ['==', ['get', 'id'], focusId ?? ''],
          '#7c3aed',
          ['interpolate', ['linear'],
            ['get', 'incident_count'],
            0, '#27272a',
            maxCount, '#5b21b6',
          ],
        ] as unknown as string,
        'fill-opacity': [
          'case',
          ['==', ['get', 'id'], focusId ?? ''],
          0.6,
          0.45,
        ] as unknown as number,
      },
    }),
    [maxCount, focusId],
  )

  const lineLayer = {
    id: 'municipalities-line',
    type: 'line' as const,
    paint: {
      'line-color': [
        'case',
        ['==', ['get', 'id'], focusId ?? ''],
        '#a78bfa',
        '#52525b',
      ] as unknown as string,
      'line-width': [
        'case',
        ['==', ['get', 'id'], focusId ?? ''],
        2,
        1,
      ] as unknown as number,
    },
  }

  const onMouseMove = useCallback((e: MapLayerMouseEvent) => {
    if (e.features && e.features.length > 0) {
      const f = e.features[0]
      setHovered({
        id: f.properties.id as string,
        name: f.properties.name as string,
        incidentCount: f.properties.incident_count as number,
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
      })
    } else {
      setHovered(null)
    }
  }, [])

  const onClick = useCallback((e: MapLayerMouseEvent) => {
    if (e.features && e.features.length > 0) {
      const id = e.features[0].properties.id as string
      navigate({ to: '/municipalities/$id', params: { id } })
    }
  }, [navigate])

  return (
    <Map
      initialViewState={initialViewState}
      style={{ width: '100%', height: '100%' }}
      mapStyle={TILE_STYLE}
      interactiveLayerIds={['municipalities-fill']}
      onMouseMove={onMouseMove}
      onMouseLeave={() => setHovered(null)}
      onClick={onClick}
      cursor={hovered ? 'pointer' : 'grab'}
    >
      <NavigationControl position="top-right" />

      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      <Source id="municipalities" type="geojson" data={geojson as any}>
        <Layer {...fillLayer} />
        <Layer {...lineLayer} />
      </Source>

      {hovered && (
        <Popup
          latitude={hovered.lat}
          longitude={hovered.lng}
          closeButton={false}
          anchor="bottom"
          offset={8}
          className="!bg-zinc-900 !border-zinc-700 !rounded-lg !shadow-xl !p-0"
        >
          <div className="px-3 py-2 min-w-[140px]">
            <p className="font-medium text-sm text-white">{hovered.name}</p>
            <p className="text-xs text-zinc-400 mt-0.5">
              {hovered.incidentCount} incident{hovered.incidentCount !== 1 ? 's' : ''}
            </p>
          </div>
        </Popup>
      )}
    </Map>
  )
}
