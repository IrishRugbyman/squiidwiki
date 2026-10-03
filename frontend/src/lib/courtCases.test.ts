import { describe, expect, it } from 'vitest'
import { courtAndDocket, formatSentence } from './courtCases'

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
