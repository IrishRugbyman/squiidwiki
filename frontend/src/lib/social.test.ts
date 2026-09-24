import { describe, expect, it } from 'vitest'
import { normalizeHandle, socialEntries, socialHandle, splitSocial } from './social'

// Expected values here are written from the data and the intended display, never
// from running the functions. The bug being guarded against is the old shape:
// one string per platform, which silently dropped every account but the last.

describe('socialEntries', () => {
  it('flattens several accounts under one platform into one entry each', () => {
    const entries = socialEntries({
      instagram: ['redwing_duceptoa', 'redwing_duce', 'redwingducep.t.o.a', 'southside_duce'],
    })
    expect(entries.map((e) => e.raw)).toEqual([
      'redwing_duceptoa', 'redwing_duce', 'redwingducep.t.o.a', 'southside_duce',
    ])
    expect(entries.every((e) => e.platform === 'instagram')).toBe(true)
  })

  it('gives each entry a distinct key so a platform can repeat', () => {
    const keys = socialEntries({ instagram: ['a', 'b'], facebook: ['c'] }).map((e) => e.key)
    expect(new Set(keys).size).toBe(3)
  })

  it('still accepts a bare string, which is what most rows hold', () => {
    expect(socialEntries({ instagram: 'nino_sc722' })).toEqual([
      { platform: 'instagram', raw: 'nino_sc722', key: 'instagram-0' },
    ])
  })

  it('drops empty and blank accounts rather than rendering an empty chip', () => {
    expect(socialEntries({ instagram: ['a', '', '   '], twitter: '' }).map((e) => e.raw)).toEqual(['a'])
  })

  it('trims surrounding whitespace', () => {
    expect(socialEntries({ instagram: '  spaced  ' })[0].raw).toBe('spaced')
  })

  it('returns nothing for null or undefined', () => {
    expect(socialEntries(null)).toEqual([])
    expect(socialEntries(undefined)).toEqual([])
  })
})

describe('socialHandle', () => {
  it('prefixes a bare handle with @ exactly once', () => {
    expect(socialHandle('nino_sc722')).toBe('@nino_sc722')
    expect(socialHandle('@nino_sc722')).toBe('@nino_sc722')
  })

  it('reduces a profile URL to its handle, with or without a trailing slash', () => {
    expect(socialHandle('https://www.instagram.com/southside_duce/')).toBe('@southside_duce')
    expect(socialHandle('https://www.instagram.com/southside_duce')).toBe('@southside_duce')
  })

  it('falls back to the host when the last segment is a file, not a handle', () => {
    expect(socialHandle('https://www.facebook.com/profile.php')).toBe('www.facebook.com')
  })

  it('keeps a dotted vanity name as the handle, not the host', () => {
    expect(socialHandle('https://www.facebook.com/linwood.mcgiver')).toBe('@linwood.mcgiver')
    expect(socialHandle('https://www.instagram.com/lil.jay_/')).toBe('@lil.jay_')
  })

  it('still treats a page file as no handle, whatever its extension', () => {
    expect(socialHandle('https://www.facebook.com/home.html')).toBe('www.facebook.com')
    expect(socialHandle('https://example.com/Profile.ASPX')).toBe('example.com')
  })

  it('labels a vanity-less Facebook account by its numeric id, not by profile.php', () => {
    expect(socialHandle('profile.php?id=100020370098269')).toBe('@100020370098269')
    expect(socialHandle('https://www.facebook.com/profile.php?id=100020370098269')).toBe('@100020370098269')
  })

  it('returns a malformed URL unchanged rather than throwing', () => {
    expect(socialHandle('http://')).toBe('http://')
  })
})

describe('normalizeHandle', () => {
  it('strips protocol, host and @ down to a bare handle', () => {
    expect(normalizeHandle('instagram', 'https://www.instagram.com/southside_duce')).toBe('southside_duce')
    expect(normalizeHandle('facebook', 'facebook.com/rbm.beezy')).toBe('rbm.beezy')
    expect(normalizeHandle('twitter', '@egotmoney')).toBe('egotmoney')
  })

  it('accepts the m. and x.com host variants', () => {
    expect(normalizeHandle('facebook', 'https://m.facebook.com/hood.joe')).toBe('hood.joe')
    expect(normalizeHandle('twitter', 'https://x.com/MoneyMainCT')).toBe('MoneyMainCT')
  })

  it('drops a trailing path, query or fragment', () => {
    expect(normalizeHandle('instagram', 'https://instagram.com/nino_sc722/reels')).toBe('nino_sc722')
    expect(normalizeHandle('instagram', 'https://instagram.com/nino_sc722?hl=en')).toBe('nino_sc722')
  })

  it('keeps the numeric id of a Facebook account that has no vanity URL', () => {
    // Cutting at the `?` used to leave `profile.php`, which addresses nobody.
    expect(normalizeHandle('facebook', 'https://www.facebook.com/profile.php?id=100020370098269'))
      .toBe('profile.php?id=100020370098269')
  })

  it('keeps the numeric id when other query params surround it', () => {
    expect(normalizeHandle('facebook', 'https://www.facebook.com/profile.php?locale=en_US&id=61550000000001'))
      .toBe('profile.php?id=61550000000001')
  })

  it('keeps the numeric id when the value was already stored bare', () => {
    expect(normalizeHandle('facebook', 'profile.php?id=100020370098269')).toBe('profile.php?id=100020370098269')
  })

  it('returns empty for an empty or blank field', () => {
    expect(normalizeHandle('facebook', '')).toBe('')
    expect(normalizeHandle('facebook', '   ')).toBe('')
  })
})

describe('splitSocial', () => {
  it('splits on commas and discards blanks', () => {
    expect(splitSocial(' a , b ,, c ')).toEqual(['a', 'b', 'c'])
  })

  it('treats a single handle as a one-element list', () => {
    expect(splitSocial('solo')).toEqual(['solo'])
  })

  it('returns nothing for an empty field', () => {
    expect(splitSocial('   ')).toEqual([])
  })
})
