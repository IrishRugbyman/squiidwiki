// Every page that shows one universe's data lives under `/$universe/...`, so a
// link says which universe it means: `/michigan/members/ralph`. Slugs are only
// unique within a universe, so before this a link opened whichever universe the
// viewer happened to have selected.

/** First path segments of the universe-scoped sections, as they were before the
 *  universe moved into the URL. An old link (`/members/ralph`) arrives as a
 *  universe called "members" and is redirected into the active universe. */
export const SCOPED_SECTIONS = [
  'alliances',
  'calendar',
  'gangs',
  'incidents',
  'map',
  'members',
  'municipalities',
  'research',
  'sets',
  'sources',
  'timeline',
] as const

/** Route params for an entity that may live in another universe than the page
 *  linking to it. An incident sits in the universe it happened in, and its
 *  participants can come from any: a Michigan member's page lists the Ohio
 *  shooting he took part in, and that row must open under `/ohio/`, not
 *  `/michigan/`. A null slug keeps the current universe. */
export function paramsIn(slug: string | null | undefined, id: string) {
  return <P extends { universe: string }>(prev: P) => ({ ...prev, universe: slug ?? prev.universe, id })
}

/** The same path in another universe: `/michigan/sets/x` becomes `/illinois/sets`.
 *  An entity id means nothing in the other universe, so a detail page lands on
 *  its section's list instead. */
export function pathInUniverse(pathname: string, slug: string): string {
  const parts = pathname.split('/').filter(Boolean)
  const section = parts[1]
  if (!section || !(SCOPED_SECTIONS as readonly string[]).includes(section)) return `/${slug}`
  // municipalities/map is a page, not an entity.
  if (section === 'municipalities' && parts[2] === 'map') return `/${slug}/municipalities/map`
  return `/${slug}/${section}`
}
