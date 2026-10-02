import type { UUID } from './types'

/** The one field these helpers read from a set on the map. */
interface HasTerritory {
  id: UUID
  territory_polygon: GeoJSON.Polygon | GeoJSON.MultiPolygon | null
}

/**
 * Two sets hold the same ground when their outlines are the same coordinates,
 * which is how a shared territory is written (one polygon copied onto each).
 */
export function groundKey(s: HasTerritory): string {
  return JSON.stringify(s.territory_polygon?.coordinates ?? null)
}

/** Sets with a polygon, grouped by identical ground, in their original order. */
export function groupBySameGround<T extends HasTerritory>(sets: T[]): T[][] {
  const groups = new Map<string, T[]>()
  for (const s of sets) {
    if (!s.territory_polygon) continue
    const k = groundKey(s)
    const g = groups.get(k)
    if (g) g.push(s)
    else groups.set(k, [s])
  }
  return [...groups.values()]
}

/**
 * The set a click on a shared shape selects. A shape standing for several sets
 * steps through them, one per click, starting from `lead` when none of them is
 * selected yet.
 */
export function nextSetOnClick(ids: UUID[], selected: UUID | null, lead: UUID): UUID {
  const at = selected ? ids.indexOf(selected) : -1
  return at === -1 ? lead : ids[(at + 1) % ids.length]
}
