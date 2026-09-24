import { default as MapGL, Marker, NavigationControl } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import { INCIDENT_TYPE_HEX } from '@/lib/statusColors'
import type { IncidentType } from '@/lib/types'

const TILE_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

/**
 * Where an incident happened, on a small street-level map. Lazy-loaded like
 * every maplibre component, so the incident page pays for it only when the
 * incident has coordinates.
 */
export default function IncidentMiniMap({ lat, lng, type }: { lat: number; lng: number; type: IncidentType }) {
  const color = INCIDENT_TYPE_HEX[type] ?? '#f43f5e'
  return (
    <MapGL
      initialViewState={{ latitude: lat, longitude: lng, zoom: 14.5 }}
      style={{ width: '100%', height: '100%' }}
      mapStyle={TILE_STYLE}
      attributionControl={{ compact: true }}
      cooperativeGestures
    >
      <NavigationControl position="top-right" showCompass={false} />
      <Marker latitude={lat} longitude={lng} anchor="center">
        <span className="relative flex h-4 w-4" aria-label="Incident location">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60" style={{ backgroundColor: color }} />
          <span className="relative inline-flex h-4 w-4 rounded-full border-2 border-zinc-950" style={{ backgroundColor: color }} />
        </span>
      </Marker>
    </MapGL>
  )
}
