import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { MemberIncarcerationRead } from '@/lib/types'

/**
 * Grouping and status for the incarceration panel.
 *
 * The table holds **one row per sentence**, because that is what MDOC OTIS
 * publishes: a profile nests `Prison Sentences > Sentence 1..N`, each with its
 * own offence, court file, term and discharge date. The facility and the
 * projected release dates sit one level up, on the *offender*, and the importer
 * attaches them to the single controlling sentence (see `derive_spells` in
 * `backend/app/services/mdoc.py`).
 *
 * Rendering that shape one row at a time is what made a man serving four
 * concurrent counts on one court file read as four separate imprisonments, three
 * of them at "Unknown facility" - a facility that is not unknown at all, merely
 * recorded against a different count. So the grouping is done here: one card per
 * court file, the offender-level facts lifted to the card, the sentences listed
 * inside it.
 *
 * The rows themselves are left exactly as OTIS states them. Collapsing them in
 * the database would lose which count carries which term and would be undone by
 * the next import.
 */

/** Sentences sharing one court file, with the offender-level facts lifted out. */
export interface IncarcerationGroup {
  /** Stable React key: the court file, or the row id when there is none. */
  key: string
  caseId: string | null
  facility: string | null
  /** Earliest sentencing date in the group. */
  from: FuzzyDateValue | null
  /** The discharge, set only when *every* sentence in the group has one. */
  to: FuzzyDateValue | null
  earliestRelease: FuzzyDateValue | null
  maxDischarge: FuzzyDateValue | null
  lifeSentence: boolean
  spells: MemberIncarcerationRead[]
}

/**
 * How to describe where a group stands. `open` is the case this module exists
 * for: OTIS gives a sentencing date and no discharge, which means the sentence
 * has not discharged - it does *not* mean the man is sitting in that prison
 * today, and it must never render as "present".
 */
export type IncarcerationStatus =
  | 'discharged' // every sentence has a discharge date
  | 'life' // a life maximum
  | 'projected' // still running, with a release projection
  | 'open' // still running, no projection published

/** Sort order for a FuzzyDate; missing parts count as the start of the period. */
function sortKey(d: FuzzyDateValue | null | undefined): number | null {
  if (!d || d.precision === 'UNKNOWN' || !d.year) return null
  return d.year * 10000 + (d.month ?? 1) * 100 + (d.day ?? 1)
}

function earliest(dates: (FuzzyDateValue | null | undefined)[]): FuzzyDateValue | null {
  let best: FuzzyDateValue | null = null
  let bestKey = Infinity
  for (const d of dates) {
    const k = sortKey(d)
    if (k !== null && k < bestKey) {
      best = d as FuzzyDateValue
      bestKey = k
    }
  }
  return best
}

function latest(dates: (FuzzyDateValue | null | undefined)[]): FuzzyDateValue | null {
  let best: FuzzyDateValue | null = null
  let bestKey = -Infinity
  for (const d of dates) {
    const k = sortKey(d)
    if (k !== null && k > bestKey) {
      best = d as FuzzyDateValue
      bestKey = k
    }
  }
  return best
}

function firstSet<T>(values: (T | null | undefined)[]): T | null {
  for (const v of values) if (v !== null && v !== undefined && v !== '') return v
  return null
}

/**
 * One group per court file, newest first.
 *
 * A row with no court file is its own group: hand-entered spells (a federal
 * detention, a spell known only from a press report) carry no MDOC case number
 * and must not be pooled together into one meaningless card.
 */
export function groupIncarcerations(spells: MemberIncarcerationRead[]): IncarcerationGroup[] {
  const groups = new Map<string, MemberIncarcerationRead[]>()
  for (const spell of spells) {
    const caseId = spell.case_id?.trim()
    const key = caseId ? `case:${caseId}` : `spell:${spell.id}`
    const bucket = groups.get(key)
    if (bucket) bucket.push(spell)
    else groups.set(key, [spell])
  }

  const out: IncarcerationGroup[] = []
  for (const [key, rows] of groups) {
    const allDischarged = rows.every((r) => r.to_date && r.to_date.precision !== 'UNKNOWN')
    out.push({
      key,
      caseId: firstSet(rows.map((r) => r.case_id)),
      facility: firstSet(rows.map((r) => r.facility)),
      from: earliest(rows.map((r) => r.from_date)),
      to: allDischarged ? latest(rows.map((r) => r.to_date)) : null,
      earliestRelease: firstSet(rows.map((r) => r.earliest_release_date)),
      maxDischarge: firstSet(rows.map((r) => r.max_discharge_date)),
      lifeSentence: rows.some((r) => r.life_sentence),
      spells: rows,
    })
  }

  // Newest first. A group with no usable date sorts last rather than jumping to
  // the top, which is where `null` would otherwise land it.
  return out.sort((a, b) => (sortKey(b.from) ?? -Infinity) - (sortKey(a.from) ?? -Infinity))
}

/**
 * Precedence matters. A discharged sentence is over whatever else is recorded
 * against it, so `to_date` is read before the projections: printing "Max: 2046"
 * for a man released in 2015 is the mistake `to_date` exists to prevent. A life
 * maximum outranks a projection for the same reason in the other direction.
 */
export function incarcerationStatus(group: IncarcerationGroup): IncarcerationStatus {
  if (group.to) return 'discharged'
  if (group.lifeSentence) return 'life'
  if (group.earliestRelease || group.maxDischarge) return 'projected'
  return 'open'
}

/**
 * The `open` wording, which is the whole point of this module.
 *
 * OTIS leaves the discharge blank on every sentence that has not discharged,
 * and a Michigan indeterminate term runs until its maximum expires - so a man
 * who keeps returning on new felonies has several old sentences open at once,
 * alongside the one he is actually serving. Saying "present" of each of them
 * claims he is serving five prison terms in five places right now. Saying
 * nothing at all loses the fact. This states exactly what the record says.
 */
export const OPEN_SENTENCE_LABEL = 'no discharge recorded'


// ── Sentence detail ─────────────────────────────────────────────────────────
//
// `notes` on an OTIS row is a block written by `_spell_notes` in
// `backend/app/services/mdoc.py`, one `Label: value` per line. It is machine
// written by this same codebase, so parsing it back is reading our own format
// rather than scraping prose - but it is also the field a curator types into by
// hand, so anything that does not match falls back to the raw text untouched.

export interface ParsedSentence {
  offense: string | null
  mcl: string[]
  county: string | null
  convictionType: string | null
  minimum: string | null
  maximum: string | null
  dateOfOffense: string | null
  dischargeReason: string | null
  /** Lines that matched no known label, kept so nothing is silently dropped. */
  extra: string[]
}

const EMPTY_SENTENCE: ParsedSentence = {
  offense: null,
  mcl: [],
  county: null,
  convictionType: null,
  minimum: null,
  maximum: null,
  dateOfOffense: null,
  dischargeReason: null,
  extra: [],
}

export function parseSentenceNotes(notes: string | null): ParsedSentence {
  if (!notes) return { ...EMPTY_SENTENCE }
  const out: ParsedSentence = { ...EMPTY_SENTENCE, mcl: [], extra: [] }
  for (const rawLine of notes.split('\n')) {
    const line = rawLine.trim()
    if (!line) continue
    if (line.startsWith('Offense:')) out.offense = line.slice(8).trim() || null
    else if (line.startsWith('MCL ')) out.mcl = line.slice(4).split('/').map((p) => p.trim()).filter(Boolean)
    else if (line.startsWith('County:')) out.county = line.slice(7).trim() || null
    else if (line.startsWith('Conviction type:')) out.convictionType = line.slice(16).trim() || null
    else if (line.startsWith('Date of offense:')) out.dateOfOffense = line.slice(16).trim() || null
    else if (line.startsWith('Discharge reason:')) out.dischargeReason = line.slice(17).trim() || null
    else if (line.startsWith('Sentence:')) {
      const [lo, hi] = line.slice(9).split(' to ')
      out.minimum = lo?.trim() || null
      out.maximum = hi?.trim() || null
    } else out.extra.push(line)
  }
  return out
}

const TERM_UNIT = /(\d+)\s*(year|month|day)s?/gi
const LIFE = /\blife\b/i

interface Term {
  years: number
  months: number
  days: number
}

function parseTerm(raw: string | null): Term | null {
  if (!raw || LIFE.test(raw)) return null
  const t: Term = { years: 0, months: 0, days: 0 }
  let matched = false
  for (const m of raw.matchAll(TERM_UNIT)) {
    matched = true
    const n = Number(m[1])
    const unit = m[2].toLowerCase()
    if (unit === 'year') t.years = n
    else if (unit === 'month') t.months = n
    else t.days = n
  }
  return matched ? t : null
}

function termText(t: Term, withUnit: boolean): string {
  const parts: string[] = []
  if (t.years) parts.push(withUnit ? `${t.years}y` : String(t.years))
  if (t.months) parts.push(`${t.months}m`)
  if (t.days) parts.push(`${t.days}d`)
  if (!parts.length) return withUnit ? '0y' : '0'
  return parts.join('')
}

/**
 * The term as it fits in a list: "25-45y", "1y6m-20y", "life".
 *
 * MDOC writes every term to three units whether or not they are used - "25
 * years 0 months 0 days to 45 years 0 months" - which is six words to say a
 * number most readers scan in two characters. The zeros are dropped, and when
 * both ends are whole years the unit is printed once at the end.
 */
export function formatTermRange(minimum: string | null, maximum: string | null): string | null {
  if (maximum && LIFE.test(maximum)) return 'life'
  const lo = parseTerm(minimum)
  const hi = parseTerm(maximum)
  if (!lo && !hi) return null
  if (!hi) return lo ? `${termText(lo, true)}+` : null
  if (!lo) return `to ${termText(hi, true)}`
  const wholeYears = !lo.months && !lo.days && !hi.months && !hi.days
  return wholeYears
    ? `${termText(lo, false)}-${termText(hi, true)}`
    : `${termText(lo, true)}-${termText(hi, true)}`
}

/** Rough length of a maximum term, for ranking only. Life sorts highest. */
function maxTermWeight(maximum: string | null): number {
  if (maximum && LIFE.test(maximum)) return Number.POSITIVE_INFINITY
  const t = parseTerm(maximum)
  return t ? t.years * 365 + t.months * 30 + t.days : -1
}

/**
 * The count that decides how long the file runs, which is the one worth showing
 * when only one line fits. Same rule the importer uses to decide which sentence
 * carries the release projection, so the headline offence and the release date
 * on a card always describe the same count.
 */
export function controllingSpell(group: IncarcerationGroup): MemberIncarcerationRead {
  let best = group.spells[0]
  let bestWeight = -Infinity
  for (const spell of group.spells) {
    const weight = maxTermWeight(parseSentenceNotes(spell.notes).maximum)
    if (weight > bestWeight) {
      best = spell
      bestWeight = weight
    }
  }
  return best
}

/**
 * The offender-level facts, lifted off whichever card carries them.
 *
 * Facility and release dates describe the man, not any one court file, so they
 * head the panel once instead of repeating down it.
 */
export interface IncarcerationSummary {
  facility: string | null
  earliestRelease: FuzzyDateValue | null
  maxDischarge: FuzzyDateValue | null
  lifeSentence: boolean
}

export function incarcerationSummary(groups: IncarcerationGroup[]): IncarcerationSummary | null {
  const live = groups.filter((g) => incarcerationStatus(g) !== 'discharged')
  const facility = live.find((g) => g.facility)?.facility ?? null
  const earliestRelease = live.find((g) => g.earliestRelease)?.earliestRelease ?? null
  const maxDischarge = live.find((g) => g.maxDischarge)?.maxDischarge ?? null
  const lifeSentence = live.some((g) => g.lifeSentence)
  if (!facility && !earliestRelease && !maxDischarge && !lifeSentence) return null
  return { facility, earliestRelease, maxDischarge, lifeSentence }
}
