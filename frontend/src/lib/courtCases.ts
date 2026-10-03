import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { CaseDisposition, CourtCaseKind, CourtCaseSpellBrief, CourtJurisdiction } from './types'

export const DISPOSITIONS: CaseDisposition[] = ['PENDING', 'PLEADED', 'CONVICTED', 'ACQUITTED', 'DISMISSED', 'DIED']

export const DISPOSITION_LABEL: Record<CaseDisposition, string> = {
  PENDING: 'Pending',
  PLEADED: 'Pleaded',
  CONVICTED: 'Convicted',
  ACQUITTED: 'Acquitted',
  DISMISSED: 'Dismissed',
  DIED: 'Died before verdict',
}

export const DISPOSITION_CHIP: Record<CaseDisposition, string> = {
  PENDING: 'border-zinc-700 bg-zinc-800/60 text-zinc-300',
  PLEADED: 'border-amber-800/60 bg-amber-950/40 text-amber-300',
  CONVICTED: 'border-rose-800/60 bg-rose-950/40 text-rose-300',
  ACQUITTED: 'border-emerald-800/60 bg-emerald-950/40 text-emerald-300',
  DISMISSED: 'border-sky-800/60 bg-sky-950/40 text-sky-300',
  DIED: 'border-zinc-700 bg-zinc-900 text-zinc-400',
}

export const JURISDICTIONS: CourtJurisdiction[] = ['US_FEDERAL', 'US_STATE', 'FR', 'OTHER']
export const JURISDICTION_LABEL: Record<CourtJurisdiction, string> = {
  US_FEDERAL: 'US federal',
  US_STATE: 'US state',
  FR: 'France',
  OTHER: 'Other',
}

export const CASE_KINDS: CourtCaseKind[] = ['CRIMINAL', 'CIVIL', 'MAGISTRATE', 'APPEAL']
export const CASE_KIND_LABEL: Record<CourtCaseKind, string> = {
  CRIMINAL: 'Criminal',
  CIVIL: 'Civil',
  MAGISTRATE: 'Magistrate',
  APPEAL: 'Appeal',
}

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`

/** "Life", "35 years", "8 years 4 months", "18 months"; null when nothing is known. */
export function formatSentence(months: number | null | undefined, life = false): string | null {
  if (life) return 'Life'
  if (months == null) return null
  if (months === 0) return 'No custody'
  if (months < 24 && months % 12 !== 0) return plural(months, 'month')
  const years = Math.floor(months / 12)
  const rest = months % 12
  return rest ? `${plural(years, 'year')} ${plural(rest, 'month')}` : plural(years, 'year')
}

/** "E.D. Mich. 2:17-cr-20740", or the court alone for a case known by name. */
export function courtAndDocket(c: { court: string; docket: string | null }): string {
  return c.docket ? `${c.court} ${c.docket}` : c.court
}

/** One member's time served for a case: OTIS records a spell per count, so a
 *  man serving eighteen counts of one file has eighteen rows that say the same
 *  thing. Folded into one: the earliest start, still running if any count is
 *  (life if any running count is life), else the latest end; the facility any
 *  count names. */
export interface ServedForCase {
  memberId: string
  memberName: string | null
  memberSlug: string | null
  memberUniverseSlug: string | null
  from: FuzzyDateValue | null
  to: FuzzyDateValue | null
  running: boolean
  life: boolean
  facility: string | null
  counts: number
}

const dateKey = (d: FuzzyDateValue | null | undefined): number | null =>
  d?.year ? d.year * 10000 + (d.month ?? 0) * 100 + (d.day ?? 0) : null

export function servedByMember(spells: CourtCaseSpellBrief[]): ServedForCase[] {
  const out = new Map<string, ServedForCase>()
  for (const s of spells) {
    const running = !s.to_date?.year
    const prev = out.get(s.member_id)
    if (!prev) {
      out.set(s.member_id, {
        memberId: s.member_id,
        memberName: s.member_name,
        memberSlug: s.member_slug,
        memberUniverseSlug: s.member_universe_slug,
        from: s.from_date,
        to: running ? null : s.to_date,
        running,
        life: running && s.life_sentence,
        facility: s.facility,
        counts: 1,
      })
      continue
    }
    prev.counts += 1
    const from = dateKey(s.from_date)
    if (from != null && (dateKey(prev.from) == null || from < dateKey(prev.from)!)) prev.from = s.from_date
    if (running) {
      prev.running = true
      prev.to = null
      if (s.life_sentence) prev.life = true
    } else if (!prev.running && (dateKey(s.to_date) ?? 0) > (dateKey(prev.to) ?? 0)) {
      prev.to = s.to_date
    }
    prev.facility ??= s.facility
  }
  return [...out.values()]
}
