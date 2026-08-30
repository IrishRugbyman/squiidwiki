import { describe, expect, it } from 'vitest'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { MemberIncarcerationRead } from '@/lib/types'
import {
  controllingSpell,
  formatTermRange,
  groupIncarcerations,
  incarcerationStatus,
  incarcerationSummary,
  parseSentenceNotes,
} from './incarceration'

// The fixtures below reproduce the *shape* of real MDOC OTIS profiles, with
// identifiers replaced. This repository is public, so no offender number, court
// file or person appears here; the research that these shapes came from lives in
// a separate private repository. What matters to these tests is the shape, and
// it is preserved exactly.
//
// `MANY_FILES` is the case the old renderer got wrong: eleven prison sentences
// across five court files, and *not one of them carries a discharge date*. It
// printed "present" against each, so one person held at one prison read as five
// concurrent imprisonments stretching back years. Only the controlling count
// carries the facility and the projections, exactly as `derive_spells` attaches
// them.
//
// `MIXED` is the other case: one discharged file alongside one still running.

function ymd(year: number, month: number, day: number): FuzzyDateValue {
  return { year, month, day, precision: 'YMD', approx: false }
}

let seq = 0
function spell(over: Partial<MemberIncarcerationRead>): MemberIncarcerationRead {
  seq += 1
  return {
    id: `00000000-0000-0000-0000-${String(seq).padStart(12, '0')}`,
    member_id: '00000000-0000-0000-0000-000000000001',
    from_date: null,
    to_date: null,
    earliest_release_date: null,
    max_discharge_date: null,
    life_sentence: false,
    facility: null,
    case_id: null,
    notes: null,
    created_at: '2026-08-29T00:37:28Z',
    ...over,
  }
}

const MANY_FILES: MemberIncarcerationRead[] = [
  // CASE-A, sentenced 20 Jul 2023: six counts, one of them the
  // controlling 25-to-45 assault that carries facility and projections.
  spell({ case_id: 'CASE-A', from_date: ymd(2023, 7, 20), notes: 'Offense: Weapons - Firearms - Possession by Felon' }),
  spell({ case_id: 'CASE-A', from_date: ymd(2023, 7, 20), notes: 'Offense: Weapons - Firearms - Discharge From A Vehicle Causing Injury' }),
  spell({
    case_id: 'CASE-A',
    from_date: ymd(2023, 7, 20),
    earliest_release_date: ymd(2053, 7, 17),
    max_discharge_date: ymd(2108, 9, 24),
    facility: 'A Correctional Facility',
    notes: 'Offense: Assault with Intent to Commit Murder',
  }),
  spell({ case_id: 'CASE-A', from_date: ymd(2023, 7, 20), notes: 'Offense: Weapons - Felony Firearms 2nd Offense' }),
  spell({ case_id: 'CASE-A', from_date: ymd(2023, 7, 20), notes: 'Offense: Weapons - Felony Firearms 2nd Offense' }),
  spell({ case_id: 'CASE-A', from_date: ymd(2023, 7, 20), notes: 'Offense: Weapons - Felony Firearms 2nd Offense' }),
  spell({ case_id: 'CASE-B', from_date: ymd(2019, 5, 7), notes: 'Offense: Controlled Substance-Delivery/Manf.' }),
  spell({ case_id: 'CASE-C', from_date: ymd(2014, 1, 30), notes: 'Offense: Weapons - Firearms - Possession by Felon' }),
  spell({ case_id: 'CASE-C', from_date: ymd(2014, 1, 30), notes: 'Offense: Weapons - Felony Firearms' }),
  spell({ case_id: 'CASE-D', from_date: ymd(2010, 4, 19), notes: 'Offense: Home Invasion - 2nd Degree' }),
  spell({ case_id: 'CASE-E', from_date: ymd(2009, 10, 14), notes: 'Offense: Assault with Intent to Rob while Armed' }),
]

describe('groupIncarcerations', () => {
  it('turns eleven OTIS sentence rows into five court files', () => {
    const groups = groupIncarcerations(MANY_FILES)
    expect(groups).toHaveLength(5)
    expect(groups.map((g) => g.caseId)).toEqual([
      'CASE-A',
      'CASE-B',
      'CASE-C',
      'CASE-D',
      'CASE-E',
    ])
    expect(groups[0].spells).toHaveLength(6)
  })

  it('lifts the facility off the controlling count onto its court file', () => {
    const [current] = groupIncarcerations(MANY_FILES)
    // Five of the six rows on this file have no facility of their own.
    expect(current.spells.filter((s) => s.facility).length).toBe(1)
    expect(current.facility).toBe('A Correctional Facility')
  })

  it('does not invent a facility for the older files', () => {
    const groups = groupIncarcerations(MANY_FILES)
    expect(groups.slice(1).map((g) => g.facility)).toEqual([null, null, null, null])
  })

  it('keeps every sentence, including counts repeated on one file', () => {
    const [current] = groupIncarcerations(MANY_FILES)
    const felonyFirearm = current.spells.filter((s) =>
      s.notes?.includes('Felony Firearms 2nd Offense'),
    )
    // Three counts of MCL 750.227BB, one per underlying felony. Deduplicating
    // them would misstate the sentence.
    expect(felonyFirearm).toHaveLength(3)
  })

  it('groups by court file, not by sentencing date', () => {
    // Two files sentenced the same day must stay apart.
    const groups = groupIncarcerations([
      spell({ case_id: 'A-1', from_date: ymd(2020, 1, 1) }),
      spell({ case_id: 'B-2', from_date: ymd(2020, 1, 1) }),
    ])
    expect(groups).toHaveLength(2)
  })

  it('keeps rows with no court file apart from each other', () => {
    // A federal detention and a spell from a press report share no case number
    // and are not the same stay.
    const groups = groupIncarcerations([
      spell({ from_date: ymd(2023, 8, 22), notes: 'Federal custody' }),
      spell({ from_date: ymd(2015, 3, 2), notes: 'County jail' }),
    ])
    expect(groups).toHaveLength(2)
  })

  it('orders newest first and sinks undated groups to the bottom', () => {
    const groups = groupIncarcerations([
      spell({ case_id: 'OLD', from_date: ymd(2009, 10, 14) }),
      spell({ case_id: 'NONE' }),
      spell({ case_id: 'NEW', from_date: ymd(2023, 7, 20) }),
    ])
    expect(groups.map((g) => g.caseId)).toEqual(['NEW', 'OLD', 'NONE'])
  })
})

describe('incarcerationStatus', () => {
  it('calls an undischarged OTIS sentence open, never present', () => {
    // The 2006 armed robbery: sentenced Oct 2009, no discharge on file, no
    // projection - its 25-year maximum has simply not run out.
    const [oldest] = groupIncarcerations([
      spell({ case_id: 'CASE-E', from_date: ymd(2009, 10, 14) }),
    ])
    expect(incarcerationStatus(oldest)).toBe('open')
  })

  it('calls the controlling count projected', () => {
    const [current] = groupIncarcerations(MANY_FILES)
    expect(incarcerationStatus(current)).toBe('projected')
  })

  it('needs every sentence on the file discharged before the file is', () => {
    // One count discharged and one still running is not a discharge.
    const [mixed] = groupIncarcerations([
      spell({ case_id: 'X', from_date: ymd(2017, 10, 26), to_date: ymd(2019, 10, 18) }),
      spell({ case_id: 'X', from_date: ymd(2017, 10, 26) }),
    ])
    expect(mixed.to).toBeNull()
    expect(incarcerationStatus(mixed)).toBe('open')
  })

  it('takes the last discharge when the whole file is closed', () => {
    const [closed] = groupIncarcerations([
      spell({ case_id: 'X', from_date: ymd(2015, 7, 1), to_date: ymd(2023, 6, 30) }),
      spell({ case_id: 'X', from_date: ymd(2015, 7, 1), to_date: ymd(2021, 2, 4) }),
    ])
    expect(closed.to).toEqual(ymd(2023, 6, 30))
    expect(incarcerationStatus(closed)).toBe('discharged')
  })

  it('lets a discharge outrank a projection that was overtaken', () => {
    // The mixed profile's older file: discharged Oct 2019. A stale 2036 projection on the
    // same row must not turn it back into a live sentence.
    const [spent] = groupIncarcerations([
      spell({
        case_id: 'CASE-F',
        from_date: ymd(2017, 10, 26),
        to_date: ymd(2019, 10, 18),
        max_discharge_date: ymd(2036, 11, 12),
      }),
    ])
    expect(incarcerationStatus(spent)).toBe('discharged')
  })

  it('lets life outrank a projection', () => {
    const [lifer] = groupIncarcerations([
      spell({ case_id: 'CASE-H', from_date: ymd(2023, 7, 19), life_sentence: true, max_discharge_date: ymd(2099, 1, 1) }),
    ])
    expect(incarcerationStatus(lifer)).toBe('life')
  })

  it('ignores an UNKNOWN-precision discharge date', () => {
    // An empty date is not a discharge; treating it as one would close a live
    // sentence on the strength of a blank form field.
    const [open] = groupIncarcerations([
      spell({
        case_id: 'X',
        from_date: ymd(2020, 1, 1),
        to_date: { year: null, month: null, day: null, precision: 'UNKNOWN', approx: false },
      }),
    ])
    expect(open.to).toBeNull()
    expect(incarcerationStatus(open)).toBe('open')
  })
})


// The note blocks below are byte-for-byte what `_spell_notes` wrote for
// the two profiles above.

const AWIM_NOTES = [
  'Offense: Assault with Intent to Commit Murder',
  'MCL 750.83',
  'County: Wayne',
  'Conviction type: Jury',
  'Sentence: 25 years 0 months 0 days to 45 years 0 months',
  'Date of offense: Jan 2, 2021',
].join('\n')

const CCW_NOTES = [
  'Offense: Weapons - Carrying Concealed',
  'MCL 750.227 / 769.12',
  'County: Oakland',
  'Conviction type: Plea',
  'Sentence: 1 year 0 months 0 days to 5 years 0 months',
  'Date of offense: Apr 10, 2016',
  'Discharge reason: Offender Discharge',
].join('\n')

describe('parseSentenceNotes', () => {
  it('reads every labelled field out of a generated block', () => {
    const p = parseSentenceNotes(AWIM_NOTES)
    expect(p.offense).toBe('Assault with Intent to Commit Murder')
    expect(p.mcl).toEqual(['750.83'])
    expect(p.county).toBe('Wayne')
    expect(p.convictionType).toBe('Jury')
    expect(p.minimum).toBe('25 years 0 months 0 days')
    expect(p.maximum).toBe('45 years 0 months')
    expect(p.dateOfOffense).toBe('Jan 2, 2021')
    expect(p.dischargeReason).toBeNull()
    expect(p.extra).toEqual([])
  })

  it('splits a habitual-offender MCL pair and reads the discharge reason', () => {
    const p = parseSentenceNotes(CCW_NOTES)
    expect(p.mcl).toEqual(['750.227', '769.12'])
    expect(p.dischargeReason).toBe('Offender Discharge')
  })

  it('keeps unrecognised lines instead of dropping them', () => {
    // A curator's own note must survive being parsed.
    const p = parseSentenceNotes('Offense: Murder\nHeld at county pending transfer')
    expect(p.offense).toBe('Murder')
    expect(p.extra).toEqual(['Held at county pending transfer'])
  })

  it('returns empty fields for no notes at all', () => {
    expect(parseSentenceNotes(null).offense).toBeNull()
    expect(parseSentenceNotes(null).mcl).toEqual([])
  })
})

describe('formatTermRange', () => {
  it('prints whole years with one unit at the end', () => {
    expect(formatTermRange('25 years 0 months 0 days', '45 years 0 months')).toBe('25-45y')
  })

  it('keeps months when a term uses them', () => {
    expect(formatTermRange('1 year 6 months 0 days', '20 years 0 months')).toBe('1y6m-20y')
  })

  it('drops the year when a term is months only', () => {
    // Rowvontae Walker's unarmed robbery: 0 years 8 months to 15 years.
    expect(formatTermRange('0 years 8 months 0 days', '15 years 0 months')).toBe('8m-15y')
  })

  it('reads a life maximum as life whatever the minimum says', () => {
    expect(formatTermRange('LIFE', 'LIFE')).toBe('life')
    expect(formatTermRange('33 years 4 months 0 days', 'LIFE')).toBe('life')
  })

  it('returns null when there is no term to show', () => {
    expect(formatTermRange(null, null)).toBeNull()
  })
})

describe('controllingSpell', () => {
  it('picks the count with the longest maximum, not the first or the longest minimum', () => {
    // The multi-count file: the 5-to-5 felony firearm is listed before the
    // 25-to-45 assault, and it is the assault that decides the release date.
    const [current] = groupIncarcerations([
      spell({ case_id: 'X', from_date: ymd(2023, 7, 20), notes: 'Offense: Weapons - Felony Firearms 2nd Offense\nSentence: 5 years 0 months 0 days to 5 years 0 months' }),
      spell({ case_id: 'X', from_date: ymd(2023, 7, 20), notes: AWIM_NOTES }),
      spell({ case_id: 'X', from_date: ymd(2023, 7, 20), notes: 'Offense: Weapons - Firearms - Possession by Felon\nSentence: 1 year 0 months 0 days to 5 years 0 months' }),
    ])
    expect(parseSentenceNotes(controllingSpell(current).notes).offense).toBe(
      'Assault with Intent to Commit Murder',
    )
  })

  it('lets a life count outrank a long fixed one', () => {
    const [g] = groupIncarcerations([
      spell({ case_id: 'Y', notes: 'Offense: Robbery Armed - Conspiracy\nSentence: 33 years 4 months 0 days to 50 years 0 months' }),
      spell({ case_id: 'Y', notes: 'Offense: Homicide - Felony Murder\nSentence: LIFE to LIFE' }),
    ])
    expect(parseSentenceNotes(controllingSpell(g).notes).offense).toBe('Homicide - Felony Murder')
  })
})

describe('incarcerationSummary', () => {
  it('lifts the live facility and projections to the top', () => {
    const s = incarcerationSummary(groupIncarcerations(MANY_FILES))
    expect(s).not.toBeNull()
    expect(s!.facility).toBe('A Correctional Facility')
    expect(s!.earliestRelease).toEqual(ymd(2053, 7, 17))
    expect(s!.maxDischarge).toEqual(ymd(2108, 9, 24))
  })

  it('ignores a facility attached to a file that is already discharged', () => {
    // Someone out since 2019 is not at that facility today.
    const s = incarcerationSummary(
      groupIncarcerations([
        spell({ case_id: 'OLD', from_date: ymd(2017, 10, 26), to_date: ymd(2019, 10, 18), facility: 'B Correctional Facility' }),
      ]),
    )
    expect(s).toBeNull()
  })

  it('returns null when there is nothing offender-level to show', () => {
    expect(incarcerationSummary(groupIncarcerations([spell({ case_id: 'X', from_date: ymd(2009, 10, 14) })]))).toBeNull()
  })
})
