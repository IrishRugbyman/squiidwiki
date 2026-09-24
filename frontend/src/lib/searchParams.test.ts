import { describe, expect, it } from 'vitest'
import { textParam } from './searchParams'

describe('textParam', () => {
  it('keeps text', () => expect(textParam('toledo')).toBe('toledo'))
  it('turns a number the router parsed back into its text', () => expect(textParam(4822)).toBe('4822'))
  it('drops empty and non-text values', () => {
    expect(textParam('')).toBeUndefined()
    expect(textParam(undefined)).toBeUndefined()
    expect(textParam(true)).toBeUndefined()
    expect(textParam(Number.NaN)).toBeUndefined()
    expect(textParam({ a: 1 })).toBeUndefined()
  })
})
