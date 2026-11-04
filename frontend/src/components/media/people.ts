import type { MediaPerson, MemberListItem, UUID } from '@/lib/types'

/** True when every tagged person has a place in the left-to-right order. */
export function isOrdered(people: readonly MediaPerson[]): boolean {
  return people.length > 0 && people.every((p) => p.position !== null)
}

/** One row of the people editor: a member and nothing else; order is the array's. */
export interface PersonDraft {
  member_id: UUID
  display_name: string
}

export function draftsFrom(people: readonly MediaPerson[]): PersonDraft[] {
  return people.map((p) => ({ member_id: p.member_id, display_name: p.display_name }))
}

/**
 * The body of PUT /media/{id}/people: positions 0..n-1 in the editor's order, or
 * all null when the order is unknown.
 */
export function peoplePayload(drafts: readonly PersonDraft[], ordered: boolean) {
  return drafts.map((d, i) => ({ member_id: d.member_id, position: ordered ? i : null }))
}

/** `items` with the one at `from` moved to `to` (a no-op outside the array). */
export function move<T>(items: readonly T[], from: number, to: number): T[] {
  if (from === to || from < 0 || to < 0 || from >= items.length || to >= items.length) {
    return [...items]
  }
  const next = [...items]
  const [item] = next.splice(from, 1)
  next.splice(to, 0, item)
  return next
}

/**
 * Whether two people lists would save the same thing. In an ordered list the
 * sequence is part of it; in an unordered one only who is in it.
 */
export function samePeople(
  a: readonly PersonDraft[],
  aOrdered: boolean,
  b: readonly PersonDraft[],
  bOrdered: boolean,
): boolean {
  if (a.length !== b.length) return false
  // An empty list has no order to disagree about.
  if (a.length > 0 && aOrdered !== bOrdered) return false
  const ids = (x: readonly PersonDraft[]) => x.map((d) => d.member_id)
  if (aOrdered) return ids(a).every((id, i) => id === ids(b)[i])
  const other = new Set(ids(b))
  return ids(a).every((id) => other.has(id))
}

/** One search hit as the people editor lists it: whether he is in the photo's set comes first. */
export interface RankedPerson {
  member: MemberListItem
  inPhotoSet: boolean
}

/**
 * How well a name answers the query, lower is better: the whole name, the
 * start of it, the start of one of its words, anywhere in it.
 */
function nameScore(name: string, q: string): number {
  const n = name.toLowerCase()
  if (n === q) return 0
  if (n.startsWith(q)) return 1
  if (n.split(/[\s\-_.'"()]+/).some((w) => w.startsWith(q))) return 2
  if (n.includes(q)) return 3
  return 4
}

/**
 * The search results in the order the editor shows them. The backend returns
 * every match unordered, so with a short query like "ken" the man actually in
 * the photo was routinely past the first screen. Members of the set the photo
 * belongs to lead, then by how closely the display name or an alias matches,
 * then alphabetically.
 */
export function rankPeople(
  results: readonly MemberListItem[],
  query: string,
  photoSetIds: ReadonlySet<UUID>,
): RankedPerson[] {
  const q = query.trim().toLowerCase()
  return results
    .map((member) => {
      const inPhotoSet = (member.affiliations ?? []).some((a) => photoSetIds.has(a.set_id))
      const names = [member.display_name, ...(member.aliases ?? [])]
      const score = Math.min(...names.map((n) => nameScore(n, q)))
      return { member, inPhotoSet, score }
    })
    .sort(
      (a, b) =>
        Number(b.inPhotoSet) - Number(a.inPhotoSet) ||
        a.score - b.score ||
        a.member.display_name.localeCompare(b.member.display_name),
    )
    .map(({ member, inPhotoSet }) => ({ member, inPhotoSet }))
}
