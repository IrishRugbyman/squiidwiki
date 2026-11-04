import { describe, expect, it } from 'vitest'
import type { MemberListItem, MemberSetAffiliation } from '@/lib/types'
import { rankPeople } from './people'

const SET = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const OTHER_SET = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'

function affiliation(set_id: string): MemberSetAffiliation {
  return {
    id: null,
    set_id,
    set_name: null,
    set_slug: null,
    rank: null,
    is_primary: true,
    from_date: null,
    until_date: null,
    is_current: true,
  }
}

function member(id: string, display_name: string, sets: string[] = [], aliases: string[] | null = null) {
  return { id, display_name, aliases, affiliations: sets.map(affiliation) } as unknown as MemberListItem
}

const names = (xs: { member: MemberListItem }[]) => xs.map((x) => x.member.display_name)

describe('rankPeople', () => {
  it('puts a member of the photo set first, ahead of a closer name match elsewhere', () => {
    const results = [
      member('1', 'Ken', [OTHER_SET]),
      member('2', 'Kenny Bandz', [SET]),
      member('3', 'Big Ken', []),
    ]
    const ranked = rankPeople(results, 'ken', new Set([SET]))
    expect(names(ranked)).toEqual(['Kenny Bandz', 'Ken', 'Big Ken'])
    expect(ranked.map((r) => r.inPhotoSet)).toEqual([true, false, false])
  })

  it('orders by exact, then prefix, then word start, then anywhere, then alphabetically', () => {
    const results = [
      member('1', 'Lil Kenzie'),
      member('2', 'Skenny'),
      member('3', 'Kendrick'),
      member('4', 'Ken'),
      member('5', 'Kenzo'),
    ]
    expect(names(rankPeople(results, 'Ken', new Set()))).toEqual(['Ken', 'Kendrick', 'Kenzo', 'Lil Kenzie', 'Skenny'])
  })

  it('scores a member by his best name, so an exact alias counts as exact', () => {
    const results = [member('1', 'Kendrick'), member('2', 'Big K', [], ['Ken'])]
    expect(names(rankPeople(results, 'ken', new Set()))).toEqual(['Big K', 'Kendrick'])
  })

  it('treats a result with no affiliations as outside the set rather than failing', () => {
    const bare = { id: '1', display_name: 'Ken' } as unknown as MemberListItem
    expect(rankPeople([bare], 'ken', new Set([SET]))).toEqual([{ member: bare, inPhotoSet: false }])
  })
})
