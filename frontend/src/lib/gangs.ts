import type { CSSProperties } from 'react'
import type { GangListItem, GangNation, UUID } from '@/lib/types'

export const NATION_LABEL: Record<GangNation, string> = {
  FOLK: 'Folk Nation',
  PEOPLE: 'People Nation',
}

/** The street shorthand Detroit uses for each nation. */
export const NATION_NUMBER: Record<GangNation, string> = { FOLK: '6', PEOPLE: '5' }

/** A card's two colours as a hard diagonal split, the way the map stripes a
 *  territory; one colour fills solid, none falls back to neutral. */
export function gangSwatchStyle(color: string | null, secondary: string | null): CSSProperties {
  if (!color) return { backgroundColor: '#3f3f46' }
  if (!secondary || secondary.toLowerCase() === color.toLowerCase()) return { backgroundColor: color }
  return { background: `linear-gradient(135deg, ${color} 0 50%, ${secondary} 50% 100%)` }
}

/** A wide band in both colours for a page header. */
export function gangBandStyle(color: string | null, secondary: string | null): CSSProperties {
  if (!color) return { background: 'linear-gradient(90deg, #27272a, #18181b)' }
  const second = secondary ?? '#000000'
  return {
    background: `repeating-linear-gradient(135deg, ${color} 0 18px, ${second} 18px 36px)`,
  }
}

export interface GangNode {
  gang: GangListItem
  children: GangNode[]
}

/** Cards as a forest: roots are cards with no parent (or a parent that is
 *  not in the list), children sorted by size then name. */
export function gangForest(gangs: GangListItem[]): GangNode[] {
  const byId = new Map(gangs.map((g) => [g.id, { gang: g, children: [] as GangNode[] }]))
  const roots: GangNode[] = []
  for (const node of byId.values()) {
    const parent = node.gang.parent_id ? byId.get(node.gang.parent_id) : undefined
    if (parent && parent !== node) parent.children.push(node)
    else roots.push(node)
  }
  const order = (a: GangNode, b: GangNode) =>
    b.gang.member_count - a.gang.member_count || a.gang.name.localeCompare(b.gang.name)
  const sortDeep = (nodes: GangNode[]) => {
    nodes.sort(order)
    nodes.forEach((n) => sortDeep(n.children))
  }
  sortDeep(roots)
  return roots
}

/** The nation a card sits under: its own, else the nearest ancestor's. */
export function effectiveNation(g: GangListItem, byId: Map<UUID, GangListItem>): GangNation | null {
  let cur: GangListItem | undefined = g
  const seen = new Set<UUID>()
  while (cur && !seen.has(cur.id)) {
    if (cur.nation) return cur.nation
    seen.add(cur.id)
    cur = cur.parent_id ? byId.get(cur.parent_id) : undefined
  }
  return null
}

/** Ids of a card and everything under it, so a parent picker can exclude them. */
export function descendantIds(rootId: UUID, gangs: GangListItem[]): Set<UUID> {
  const out = new Set<UUID>([rootId])
  let grew = true
  while (grew) {
    grew = false
    for (const g of gangs) {
      if (g.parent_id && out.has(g.parent_id) && !out.has(g.id)) {
        out.add(g.id)
        grew = true
      }
    }
  }
  return out
}
