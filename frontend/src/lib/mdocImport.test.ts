import { describe, expect, it } from 'vitest'
import { writeMdocSpells, type PostFn } from './mdocImport'
import type { MdocSpell, MemberIncarcerationRead } from './types'

// Regression for the duplicate spells OTIS re-imports left in production: the
// member form decided "already on record" from a cached spell list that the
// import never refreshed, so a second import inside the cache's five fresh
// minutes posted every sentence again. Every value here is invented.

const MEMBER = '00000000-0000-4000-8000-000000000001'
const UNIVERSE = '00000000-0000-4000-8000-0000000000aa'

const ymd = (year: number, month: number, day: number) => ({ year, month, day, precision: 'YMD' as const, approx: false })

function count(case_id: string, offense: string, from = ymd(2099, 3, 1)): MdocSpell {
  return {
    from_date: from,
    to_date: null,
    earliest_release_date: null,
    max_discharge_date: null,
    life_sentence: false,
    facility: null,
    case_id,
    notes: `Offense: ${offense}\nCounty: Testcounty`,
  }
}

// One profile as derive_spells returns it: two court files, and two genuinely
// separate felony-firearm counts on the first that read exactly alike.
const PROFILE: MdocSpell[] = [
  count('2099-000001-FC', 'Assault with Intent to Commit Murder'),
  count('2099-000001-FC', 'Weapons - Felony Firearms'),
  count('2099-000001-FC', 'Weapons - Felony Firearms'),
  count('2098-000002-FH', 'Controlled Substance-Delivery/Manf.', ymd(2098, 5, 1)),
]

const keyOf = (s: { case_id: string | null; notes: string | null; from_date: unknown; to_date: unknown }) =>
  JSON.stringify([s.case_id, (s.notes ?? '').split('\n')[0], s.from_date, s.to_date])

/**
 * A stand-in for the backend's two write routes. The plain route writes what
 * it is sent, as the real one does; the import route matches by count on court
 * file, offense line and dates, the contract `import_member_incarcerations`
 * keeps (tested against the database in backend/tests/test_otis_import.py).
 */
function fakeServer() {
  const rows: MemberIncarcerationRead[] = []
  let n = 0
  const write = (s: MdocSpell): MemberIncarcerationRead => {
    const row = { ...s, id: `row-${++n}`, member_id: MEMBER, created_at: new Date(n * 1000).toISOString() }
    rows.push(row)
    return row
  }
  const post = (async (url: string, body: unknown) => {
    const path = url.split('?')[0]
    if (path === `/members/${MEMBER}/incarcerations`) return write(body as MdocSpell)
    if (path === `/members/${MEMBER}/incarcerations/import`) {
      const onFile = new Map<string, number>()
      for (const r of rows) onFile.set(keyOf(r), (onFile.get(keyOf(r)) ?? 0) + 1)
      const created: MemberIncarcerationRead[] = []
      let matched = 0
      for (const s of (body as { spells: MdocSpell[] }).spells) {
        const left = onFile.get(keyOf(s)) ?? 0
        if (left > 0) {
          onFile.set(keyOf(s), left - 1)
          matched += 1
        } else created.push(write(s))
      }
      return { created, matched }
    }
    throw new Error(`unexpected POST ${url}`)
  }) as PostFn
  const tally = () => {
    const out: Record<string, number> = {}
    for (const r of rows) {
      const k = `${r.case_id} ${(r.notes ?? '').split('\n')[0]}`
      out[k] = (out[k] ?? 0) + 1
    }
    return out
  }
  return { rows, post, tally }
}

const ONE_PER_SENTENCE = {
  '2099-000001-FC Offense: Assault with Intent to Commit Murder': 1,
  '2099-000001-FC Offense: Weapons - Felony Firearms': 2,
  '2098-000002-FH Offense: Controlled Substance-Delivery/Manf.': 1,
}

describe('writeMdocSpells', () => {
  it('re-importing a profile against a stale cached spell list writes one row per sentence', async () => {
    const server = fakeServer()
    // The edit sheet's cached list, taken before the first import and, as in
    // production, still "fresh" when the same profile is imported again.
    const stale: MemberIncarcerationRead[] = []
    const write = () =>
      writeMdocSpells(server.post, { memberId: MEMBER, universeId: UNIVERSE, spells: PROFILE, cachedSpells: stale })

    await write()
    expect(server.tally()).toEqual(ONE_PER_SENTENCE)

    const again = await write()
    expect(server.tally()).toEqual(ONE_PER_SENTENCE)
    expect(again).toEqual({ saved: 0, skipped: 4 })
    await write()
    expect(server.rows).toHaveLength(4)
  })

  it('keeps two identical counts OTIS lists separately', async () => {
    const server = fakeServer()
    const out = await writeMdocSpells(server.post, { memberId: MEMBER, universeId: UNIVERSE, spells: PROFILE, cachedSpells: [] })
    expect(out).toEqual({ saved: 4, skipped: 0 })
    expect(server.tally()['2099-000001-FC Offense: Weapons - Felony Firearms']).toBe(2)
  })

  it('writes a second identical count when only one is on record, even with a fresh cache', async () => {
    const server = fakeServer()
    await server.post(`/members/${MEMBER}/incarcerations?universe_id=${UNIVERSE}`, PROFILE[1])
    const fresh = [...server.rows]
    const out = await writeMdocSpells(server.post, { memberId: MEMBER, universeId: UNIVERSE, spells: PROFILE, cachedSpells: fresh })
    expect(out.saved).toBe(3)
    expect(server.tally()).toEqual(ONE_PER_SENTENCE)
  })
})
