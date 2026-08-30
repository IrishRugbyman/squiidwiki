import { afterEach, describe, expect, it, vi } from 'vitest'
import { ageFromFuzzyDates, cn, currentAffiliations, primaryAffiliation, timeAgo } from './utils'

describe('cn', () => {
  it('lets the last conflicting Tailwind utility win', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })

  it('keeps utilities that do not conflict', () => {
    expect(cn('px-2', 'py-4')).toBe('px-2 py-4')
  })

  it('drops falsy branches', () => {
    expect(cn('base', false && 'never', undefined, null, 'end')).toBe('base end')
  })
})

describe('ageFromFuzzyDates', () => {
  it('is the year difference once the birth month has passed', () => {
    // Born 1990-06, asked as of 2020-07: the June birthday is behind us.
    expect(ageFromFuzzyDates({ year: 1990, month: 6 }, { year: 2020, month: 7 })).toBe(30)
  })

  it('counts the birth month itself as already had', () => {
    expect(ageFromFuzzyDates({ year: 1990, month: 6 }, { year: 2020, month: 6 })).toBe(30)
  })

  it('subtracts a year when the birthday is still ahead', () => {
    // Born 1990-06, asked as of 2020-05: still 29.
    expect(ageFromFuzzyDates({ year: 1990, month: 6 }, { year: 2020, month: 5 })).toBe(29)
  })

  it('assumes January when the birth month is unknown', () => {
    // Month defaults to 1, so any as-of month in the same year counts the birthday.
    expect(ageFromFuzzyDates({ year: 1990 }, { year: 2020, month: 1 })).toBe(30)
  })

  it('is null without a birth year, because nothing can be derived', () => {
    expect(ageFromFuzzyDates({ month: 6 }, { year: 2020, month: 7 })).toBeNull()
  })

  it('is null rather than negative when the as-of date precedes the birth', () => {
    // A data-entry error must not render as "-10".
    expect(ageFromFuzzyDates({ year: 2030 }, { year: 2020, month: 6 })).toBeNull()
  })

  it('falls back to today when no as-of date is given', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2020-07-15T00:00:00Z'))
    expect(ageFromFuzzyDates({ year: 1990, month: 6 })).toBe(30)
    expect(ageFromFuzzyDates({ year: 1990, month: 8 })).toBe(29)
    vi.useRealTimers()
  })
})

describe('timeAgo', () => {
  const NOW = new Date('2020-07-15T12:00:00Z')

  function ago(ms: number): string {
    return timeAgo(new Date(NOW.getTime() - ms).toISOString())
  }

  const SECOND = 1000
  const MINUTE = 60 * SECOND
  const HOUR = 60 * MINUTE
  const DAY = 24 * HOUR

  afterEach(() => vi.useRealTimers())

  function freeze() {
    vi.useFakeTimers()
    vi.setSystemTime(NOW)
  }

  it.each([
    [0, 'just now'],
    [30 * SECOND, 'just now'],
    [59 * SECOND, 'just now'],
    [60 * SECOND, '1m ago'],
    [59 * MINUTE, '59m ago'],
    [60 * MINUTE, '1h ago'],
    [23 * HOUR, '23h ago'],
    [24 * HOUR, '1d ago'],
    [29 * DAY, '29d ago'],
    [30 * DAY, '1mo ago'],
    [359 * DAY, '11mo ago'],
    [360 * DAY, '1y ago'],
  ])('renders %i ms ago as %s', (offset, expected) => {
    freeze()
    expect(ago(offset)).toBe(expected)
  })

  it('rolls over to years at twelve 30-day months, not at 365 days', () => {
    // The buckets are 30-day months, so the year boundary lands at 360 days.
    // Documented here because it is a deliberate approximation, not a bug.
    freeze()
    expect(ago(359 * DAY)).toBe('11mo ago')
    expect(ago(360 * DAY)).toBe('1y ago')
  })
})

describe('currentAffiliations', () => {
  it('keeps only the spells flagged current', () => {
    const rows = [
      { id: 'a', is_current: true },
      { id: 'b', is_current: false },
    ]
    expect(currentAffiliations(rows).map((r) => r.id)).toEqual(['a'])
  })

  it('falls back to an absent until_date on payloads that predate is_current', () => {
    const rows = [
      { id: 'open', until_date: null },
      { id: 'closed', until_date: { year: 2019 } },
    ]
    expect(currentAffiliations(rows).map((r) => r.id)).toEqual(['open'])
  })

  it('prefers is_current over until_date when both are present', () => {
    // A closed spell that the server still marks current stays current: the
    // flag is the server's answer and the date is only the fallback.
    const rows = [{ id: 'a', is_current: true, until_date: { year: 2019 } }]
    expect(currentAffiliations(rows).map((r) => r.id)).toEqual(['a'])
  })

  it('is an empty array for null and undefined', () => {
    expect(currentAffiliations(null)).toEqual([])
    expect(currentAffiliations(undefined)).toEqual([])
  })
})

describe('primaryAffiliation', () => {
  it('picks the flagged spell', () => {
    const rows = [
      { id: 'a', is_primary: false, is_current: true },
      { id: 'b', is_primary: true, is_current: true },
    ]
    expect(primaryAffiliation(rows)?.id).toBe('b')
  })

  it('ignores a primary spell that has ended', () => {
    // This is the whole point of filtering to current first: a member who left
    // the set they were primary in must not still show it.
    const rows = [
      { id: 'past-primary', is_primary: true, is_current: false },
      { id: 'present', is_primary: false, is_current: true },
    ]
    expect(primaryAffiliation(rows)?.id).toBe('present')
  })

  it('falls back to the first current spell when none is flagged', () => {
    const rows = [
      { id: 'a', is_primary: false, is_current: true },
      { id: 'b', is_primary: false, is_current: true },
    ]
    expect(primaryAffiliation(rows)?.id).toBe('a')
  })

  it('is null when nothing is current', () => {
    expect(primaryAffiliation([{ id: 'a', is_primary: true, is_current: false }])).toBeNull()
    expect(primaryAffiliation([])).toBeNull()
    expect(primaryAffiliation(null)).toBeNull()
  })
})
