import type { MemberStatus } from '@/lib/types'

/**
 * The member status an OTIS "Current Status" implies, or null when it implies
 * nothing we should write.
 *
 * OTIS does not hand back a bare custody state. It qualifies it, in prose, after
 * a dash: a man serving a sentence who is temporarily at a courthouse reads
 * "Prisoner - Released to court on writ (08/13/2026)". He is still a prisoner.
 * An exact `=== 'Prisoner'` comparison therefore silently declined to set the
 * status on exactly the records that had the most detail, which is the bug this
 * function exists to stop.
 *
 * Only a live prisoner implies LOCKED. Parole, probation and discharge all mean
 * some degree of *out*, and each maps to a different thing on this wiki, so they
 * return null and leave the curator's own status alone rather than guessing.
 * Nothing is mapped here that has not been seen coming out of OTIS.
 */
export function memberStatusFromMdoc(otisStatus: string | null | undefined): MemberStatus | null {
  if (!otisStatus) return null
  // Cut the qualifier: everything from the first dash or bracket is prose about
  // where he is today, not what he is.
  const head = otisStatus.split(/[-(]/)[0].trim().toLowerCase()
  if (head === 'prisoner') return 'LOCKED'
  return null
}
