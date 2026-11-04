import { describe, expect, it } from 'vitest'
import { wordDiff } from './wordDiff'

const join = (parts: ReturnType<typeof wordDiff>, keep: 'add' | 'del') =>
  parts.filter((p) => p.op === 'same' || p.op === keep).map((p) => p.text).join('')

describe('wordDiff', () => {
  it('marks only the words that changed', () => {
    const parts = wordDiff('Opened a studio in 2019.', 'Opened a label in 2019.')
    expect(parts.filter((p) => p.op === 'del').map((p) => p.text)).toEqual(['studio'])
    expect(parts.filter((p) => p.op === 'add').map((p) => p.text)).toEqual(['label'])
  })

  it('rebuilds both texts exactly', () => {
    const a = 'One two  three\nfour'
    const b = 'One three\nfour five'
    const parts = wordDiff(a, b)
    expect(join(parts, 'del')).toBe(a)
    expect(join(parts, 'add')).toBe(b)
  })

  it('handles an empty side', () => {
    expect(wordDiff('', 'New text')).toEqual([{ op: 'add', text: 'New text' }])
    expect(wordDiff('Old text', '')).toEqual([{ op: 'del', text: 'Old text' }])
  })
})
