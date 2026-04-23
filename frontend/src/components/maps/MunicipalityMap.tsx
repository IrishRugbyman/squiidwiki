import { useCallback, useMemo, useState } from 'react'
import Map, { Layer, Popup, Source, NavigationControl } from 'react-map-gl/maplibre'
import { useNavigate } from '@tanstack/react-router'
import type { MapLayerMouseEvent } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { MunicipalityListItem } from '@/lib/types'

const TILE_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

interface Props {
  municipalities: MunicipalityListItem[]
  focusId?: string
}

interface HoveredFeature {
  id: string
  name: string
  incidentCount: number
  latitude: number
  longitude: number
}

export default function MunicipalityMap({ municipalities, focusId }: Props) {
  const navigate = useNavigate()
  const [hovered, setHovered] = useState<HoveredFeature | null>(null)

  const mapped = useMemo(
    () => municipalities.filter((m) => m.latitude != null && m.longitude != null),
    [municipalities],
  )

  const maxCount = useMemo(
    () => Math.max(1, ...mapped.map((m) => m.incident_count)),
    [mapped],
  )

  const geojson = useMemo(
    () => ({
      type: 'FeatureCollection' as const,
      features: mapped.map((m) => ({
        type: 'Feature' as const,
        id: m.id,
        geometry: { type: 'Point' as const, coordinates: [m.longitude!, m.latitude!] },
        properties: {
          id: m.id,
          name: m.name,
          incident_count: m.incident_count,
          focused: m.id === focusId ? 1 : 0,
        },
      })),
    }),
    [mapped, focusId],
  )

  const circleLayer = useMemo(
    () => ({
      id: 'municipalities',
      type: 'circle' as const,
      paint: {
        'circle-radius': [
          'interpolate', ['linear'],
          ['get', 'incident_count'],
          0, 8,
          maxCount, 28,
        ] as unknown as number,
        'circle-color': [
          'case',
          ['==', ['get', 'focused'], 1], '#a78bfa',
          ['interpolate', ['linear'],
            ['get', 'incident_count'],
            0, '#3f3f46',
            maxCount, '#7c3aed',
          ],
        ] as unknown as string,
        'circle-opacity': 0.85,
        'circle-stroke-width': [
          'case', ['==', ['get', 'focused'], 1], 2, 1,
        ] as unknown as number,
        'circle-stroke-color': [
          'case', ['==', ['get', 'focused'], 1], '#c4b5fd', '#52525b',
        ] as unknown as string,
      },
    }),
    [maxCount],
  )

  const focusedMuni = useMemo(
    () => focusId ? municipalities.find((m) => m.id === focusId) : null,
    [focusId, municipalities],
  )

  const initialViewState = useMemo(() => {
    if (focusedMuni?.latitude != null && focusedMuni?.longitude != null) {
      return { latitude: focusedMuni.latitude, longitude: focusedMuni.longitude, zoom: 12 }
    }
    if (mapped.length > 0) {
      const avgLat = mapped.reduce((s, m) => s + m.latitude!, 0) / mapped.length
      const avgLng = mapped.reduce((s, m) => s + m.longitude!, 0) / mapped.length
      return { latitude: avgLat, longitude: avgLng, zoom: 10 }
    }
    return { latitude: 40.7128, longitude: -74.006, zoom: 10 }
  }, [focusedMuni, mapped])

  const onMouseMove = useCallback(
    (e: MapLayerMouseEvent) => {
      const features = e.features
      if (features && features.length > 0) {
        const f = features[0]
        setHovered({
          id: f.properties.id,
          name: f.properties.name,
          incidentCount: f.properties.incident_count,
          latitude: (f.geometry as { coordinates: number[] }).coordinates[1],
          longitude: (f.geometry as { coordinates: number[] }).coordinates[0],
        })
      } else {
        setHovered(null)
      }
    },
    [],
  )

  const onClick = useCallback(
    (e: MapLayerMouseEvent) => {
      const features = e.features
      if (features && features.length > 0) {
        const id = features[0].properties.id as string
        navigate({ to: '/municipalities/$id', params: { id } })
      }
    },
    [navigate],
  )

  return (
    <Map
      initialViewState={initialViewState}
      style={{ width: '100%', height: '100%' }}
      mapStyle={TILE_STYLE}
      interactiveLayerIds={['municipalities']}
      onMouseMove={onMouseMove}
      onMouseLeave={() => setHovered(null)}
      onClick={onClick}
      cursor={hovered ? 'pointer' : 'grab'}
    >
      <NavigationControl position="top-right" />

      <Source id="municipalities" type="geojson" data={geojson}>
        <Layer {...circleLayer} />
      </Source>

      {hovered && (
        <Popup
          latitude={hovered.latitude}
          longitude={hovered.longitude}
          closeButton={false}
          anchor="bottom"
          offset={16}
          className="!bg-zinc-900 !border-zinc-700 !text-white !rounded-lg !shadow-xl !p-0"
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
