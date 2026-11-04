import { describe, expect, it } from 'vitest'
import { courtAndDocket, formatSentence, sentencedPhrase, servedByMember } from './courtCases'
import type { CourtCaseSpellBrief } from './types'

describe('formatSentence', () => {
  it('reads whole years as years', () => {
    expect(formatSentence(420)).toBe('35 years')
    expect(formatSentence(12)).toBe('1 year')
  })
  it('keeps the months of a term that is not whole years', () => {
    expect(formatSentence(100)).toBe('8 years 4 months')
    expect(formatSentence(25)).toBe('2 years 1 month')
  })
  it('keeps a short term in months', () => {
    expect(formatSentence(18)).toBe('18 months')
    expect(formatSentence(1)).toBe('1 month')
  })
  it('says life over any number of months', () => {
    expect(formatSentence(null, true)).toBe('Life')
    expect(formatSentence(480, true)).toBe('Life')
  })
  it('separates a known zero from an unknown term', () => {
    expect(formatSentence(0)).toBe('No custody')
    expect(formatSentence(null)).toBeNull()
  })
})

describe('courtAndDocket', () => {
  it('joins the court and docket, or gives the court alone', () => {
    expect(courtAndDocket({ court: 'E.D. Mich.', docket: '2:99-cr-1' })).toBe('E.D. Mich. 2:99-cr-1')
    expect(courtAndDocket({ court: "Cour d'assises", docket: null })).toBe("Cour d'assises")
  })
})

describe('servedByMember', () => {
  const spell = (over: Partial<CourtCaseSpellBrief>): CourtCaseSpellBrief => ({
    id: Math.random().toString(36),
    member_id: 'm1',
    member_name: 'One',
    member_slug: 'one',
    member_universe_slug: 'michigan',
    from_date: { year: 2008, month: 9, day: 10, precision: 'YMD', approx: false },
    to_date: null,
    facility: null,
    life_sentence: false,
    ...over,
  })

  it('folds one member\'s counts into one line, life if any running count is', () => {
    const rows = servedByMember([
      spell({}),
      spell({ life_sentence: true }),
      spell({ facility: 'Thumb Correctional Facility' }),
      spell({}),
    ])
    expect(rows).toHaveLength(1)
    expect(rows[0]).toMatchObject({ counts: 4, running: true, life: true, facility: 'Thumb Correctional Facility' })
  })

  it('takes the earliest start and, when every count has ended, the latest end', () => {
    const [row] = servedByMember([
      spell({ from_date: { year: 2010, precision: 'Y', approx: false }, to_date: { year: 2012, month: 1, precision: 'YM', approx: false } }),
      spell({ from_date: { year: 2009, month: 5, precision: 'YM', approx: false }, to_date: { year: 2015, month: 3, day: 2, precision: 'YMD', approx: false } }),
    ])
    expect(row.from).toEqual({ year: 2009, month: 5, precision: 'YM', approx: false })
    expect(row.to).toEqual({ year: 2015, month: 3, day: 2, precision: 'YMD', approx: false })
    expect(row.running).toBe(false)
  })

  it('keeps members apart, in the order they first appear', () => {
    const rows = servedByMember([spell({}), spell({ member_id: 'm2', member_name: 'Two' }), spell({})])
    expect(rows.map((r) => [r.memberId, r.counts])).toEqual([['m1', 2], ['m2', 1]])
  })
})

describe('sentencedPhrase', () => {
  it('names the term, life, or nothing', () => {
    expect(sentencedPhrase(210, false)).toBe('sentenced to 17 years 6 months')
    expect(sentencedPhrase(null, true)).toBe('sentenced to life')
    expect(sentencedPhrase(null, false)).toBe('sentenced')
  })
})
