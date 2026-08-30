import { describe, expect, it } from 'vitest'
import { formatEmojiInput, isLikelyEmoji, parseEmojiInput, setBadge } from './emoji'

// Expected values are written from the intended behaviour and from what the
// backend validator accepts, never from running these functions.

describe('isLikelyEmoji', () => {
  it('accepts glyphs, including multi-code-point ones', () => {
    expect(isLikelyEmoji('🔵')).toBe(true)
    expect(isLikelyEmoji('🕊️')).toBe(true)
    expect(isLikelyEmoji('1️⃣')).toBe(true)
  })

  it('rejects plain text, which belongs in name variants', () => {
    expect(isLikelyEmoji('BO')).toBe(false)
    expect(isLikelyEmoji('752')).toBe(false)
    expect(isLikelyEmoji('')).toBe(false)
  })

  it('rejects an entry longer than the backend allows', () => {
    expect(isLikelyEmoji('🔵'.repeat(9))).toBe(false)
  })
})

describe('parseEmojiInput', () => {
  it('splits on spaces and commas alike', () => {
    expect(parseEmojiInput('🔵 🕊️')).toEqual(['🔵', '🕊️'])
    expect(parseEmojiInput('🔵,🕊️')).toEqual(['🔵', '🕊️'])
  })

  it('splits emojis pasted with no separator at all', () => {
    expect(parseEmojiInput('🔵🕊️💯')).toEqual(['🔵', '🕊️', '💯'])
  })

  it('keeps a ZWJ sequence together rather than shattering it', () => {
    expect(parseEmojiInput('👨‍👩‍👧')).toEqual(['👨‍👩‍👧'])
  })

  it('de-duplicates, keeping first position, because order is the badge', () => {
    expect(parseEmojiInput('🔵 🕊️ 🔵')).toEqual(['🔵', '🕊️'])
  })

  it('returns nothing for an empty or blank field', () => {
    expect(parseEmojiInput('')).toEqual([])
    expect(parseEmojiInput('   ')).toEqual([])
  })
})

describe('formatEmojiInput', () => {
  it('round-trips through parse unchanged', () => {
    expect(parseEmojiInput(formatEmojiInput(['🔵', '🕊️']))).toEqual(['🔵', '🕊️'])
  })
})

describe('setBadge', () => {
  it('is the first emoji', () => {
    expect(setBadge(['🔵', '🕊️'])).toBe('🔵')
  })

  it('is null when the set has none', () => {
    expect(setBadge([])).toBe(null)
    expect(setBadge(null)).toBe(null)
    expect(setBadge(undefined)).toBe(null)
  })
})
