import type { SetAllianceSummary, SetGangSummary } from '@/lib/types'

/** Names of every gang a set claims, primary first. Falls back to the single
 *  primary for payloads that predate `gangs` (a stale cache, a single read). */
export function gangNamesOf(set: { gangs?: SetGangSummary[]; gang_name: string | null }): string[] {
  if (set.gangs && set.gangs.length > 0) return set.gangs.map((g) => g.name)
  return set.gang_name ? [set.gang_name] : []
}

/** Ids of every gang a set claims, primary first, with the same fallback. */
export function gangIdsOf(set: { gangs?: SetGangSummary[]; gang_id: string | null }): string[] {
  if (set.gangs && set.gangs.length > 0) return set.gangs.map((g) => g.id)
  return set.gang_id ? [set.gang_id] : []
}

/** Every gang as pill props (name, slug, colour), primary first. */
export function gangRefsOf(set: {
  gangs?: SetGangSummary[]
  gang_name: string | null
  gang_color?: string | null
}): { name: string; slug: string | null; color: string | null }[] {
  if (set.gangs && set.gangs.length > 0) return set.gangs.map((g) => ({ name: g.name, slug: g.slug, color: g.color }))
  return set.gang_name ? [{ name: set.gang_name, slug: null, color: set.gang_color ?? null }] : []
}

/** Every alliance a set is in as {id, name, slug}, primary first, falling back
 *  to the single primary for payloads that predate `alliances`. */
export function allianceRefsOf(set: {
  alliances?: SetAllianceSummary[]
  alliance_id: string | null
  alliance_name: string | null
}): SetAllianceSummary[] {
  if (set.alliances && set.alliances.length > 0) return set.alliances
  return set.alliance_id && set.alliance_name ? [{ id: set.alliance_id, name: set.alliance_name, slug: null }] : []
}
