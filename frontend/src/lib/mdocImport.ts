import type {
  MdocSpell,
  MemberIncarcerationDifference,
  MemberIncarcerationImportResult,
  MemberIncarcerationRead,
  UUID,
} from '@/lib/types'

/** The one call this needs from `api`, so a test can stand in for the server. */
export type PostFn = <T>(url: string, body: unknown) => Promise<T>

export interface MdocSpellWrite {
  memberId: UUID
  universeId: UUID
  /** Every spell `derive_spells` produced for the profile, probation already dropped. */
  spells: MdocSpell[]
  /**
   * The member's spells as the caller has them cached, if it has them.
   * Deliberately not consulted. Deciding "already on record" from this list
   * was a latent duplication path: the form's cached list was not refreshed by
   * the import itself, so a second import inside its five fresh minutes would
   * have seen the pre-import list and posted every sentence again.
   */
  cachedSpells?: MemberIncarcerationRead[]
}

/** What the import did, and what it left for a person to check. */
export interface MdocSpellWriteResult {
  /** New rows written. */
  saved: number
  /** Spells matched to a row already on record. */
  skipped: number
  /** Empty fields on matched rows that OTIS filled. */
  filled: number
  /** Values OTIS gives that disagree with ones on file: never written. */
  differences: MemberIncarcerationDifference[]
}

/**
 * Write an OTIS profile's spells onto a member, safely repeatable.
 *
 * One call to `POST /members/{id}/incarcerations/import`, which matches each
 * spell against the member's rows on the server by court file, offense line and
 * start date, by count: a second import of the same profile writes no row, and
 * two identical counts OTIS lists separately (three felony-firearm counts on
 * one court file) stay separate. A matched row is never overwritten; what OTIS
 * disagrees with comes back in `differences`. The caller refreshes its queries
 * afterwards.
 */
export async function writeMdocSpells(post: PostFn, w: MdocSpellWrite): Promise<MdocSpellWriteResult> {
  if (w.spells.length === 0) return { saved: 0, skipped: 0, filled: 0, differences: [] }
  const { created, matched, filled, differences } = await post<MemberIncarcerationImportResult>(
    `/members/${w.memberId}/incarcerations/import?universe_id=${w.universeId}`,
    { spells: w.spells },
  )
  return { saved: created.length, skipped: matched, filled: filled.length, differences }
}

const FIELD_LABELS: Record<string, string> = {
  to_date: 'end date',
  earliest_release_date: 'earliest release',
  max_discharge_date: 'max discharge',
  facility: 'facility',
  notes: 'notes',
  life_sentence: 'life sentence',
}

/** One line per field OTIS disagreed on, for the review summary: "end date (2 spells)". */
export function summariseDifferences(differences: MemberIncarcerationDifference[]): string {
  const byField = new Map<string, number>()
  for (const d of differences) byField.set(d.field, (byField.get(d.field) ?? 0) + 1)
  return [...byField]
    .map(([f, n]) => `${FIELD_LABELS[f] ?? f} (${n} spell${n === 1 ? '' : 's'})`)
    .join(', ')
}
