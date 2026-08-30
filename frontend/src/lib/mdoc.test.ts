import { describe, expect, it } from 'vitest'
import { memberStatusFromMdoc } from './mdoc'

// The strings here are real OTIS "Current Status" values, not invented shapes.
// The first one is what MDOC 896285 returned on 2026-08-27 and what the old
// exact-equality check failed to recognise.

describe('memberStatusFromMdoc', () => {
  it('reads a prisoner out to court on a writ as still LOCKED', () => {
    expect(memberStatusFromMdoc('Prisoner - Released to court on writ (08/13/2026)')).toBe('LOCKED')
  })

  it('reads a plain prisoner as LOCKED', () => {
    expect(memberStatusFromMdoc('Prisoner')).toBe('LOCKED')
  })

  it('tolerates casing and stray whitespace', () => {
    expect(memberStatusFromMdoc('  PRISONER  ')).toBe('LOCKED')
  })

  it('declines to guess for someone who is out', () => {
    expect(memberStatusFromMdoc('Discharged')).toBeNull()
    expect(memberStatusFromMdoc('Parole')).toBeNull()
    expect(memberStatusFromMdoc('Probation')).toBeNull()
  })

  it('does not match a word that merely starts with the same letters', () => {
    expect(memberStatusFromMdoc('Prisoners of the county')).toBeNull()
  })

  it('returns null for nothing at all', () => {
    expect(memberStatusFromMdoc(null)).toBeNull()
    expect(memberStatusFromMdoc(undefined)).toBeNull()
    expect(memberStatusFromMdoc('')).toBeNull()
  })
})
