import type { MdocSpell, MemberIncarcerationImportResult, MemberIncarcerationRead, UUID } from '@/lib/types'

/** The one call this needs from `api`, so a test can stand in for the server. */
export type PostFn = <T>(url: string, body: unknown) => Promise<T>

export interface MdocSpellWrite {
  memberId: UUID
  universeId: UUID
  /** Every spell `derive_spells` produced for the profile, probation already dropped. */
  spells: MdocSpell[]
  /**
   * The member's spells as the caller has them cached, if it has them.
   * Deliberately not consulted. Deciding "already on record" from this list is
   * what duplicated 103 groups of spells: the form's cached list was not
   * refreshed by the import itself, so a second import inside its five fresh
   * minutes saw the pre-import list and posted every sentence again.
   */
  cachedSpells?: MemberIncarcerationRead[]
}

/** How many spells were written, and how many were already on record. */
export interface MdocSpellWriteResult {
  saved: number
  skipped: number
}

/**
 * Write an OTIS profile's spells onto a member, safely repeatable.
 *
 * One call to `POST /members/{id}/incarcerations/import`, which matches each
 * spell against the member's rows on the server, by count: a second import of
 * the same profile writes nothing, and two identical counts OTIS lists
 * separately (three felony-firearm counts on one court file) stay separate.
 * The caller refreshes its queries afterwards.
 */
export async function writeMdocSpells(post: PostFn, w: MdocSpellWrite): Promise<MdocSpellWriteResult> {
  if (w.spells.length === 0) return { saved: 0, skipped: 0 }
  const { created, matched } = await post<MemberIncarcerationImportResult>(
    `/members/${w.memberId}/incarcerations/import?universe_id=${w.universeId}`,
    { spells: w.spells },
  )
  return { saved: created.length, skipped: matched }
}
