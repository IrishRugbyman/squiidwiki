import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function ageFromFuzzyDates(
  dob: { year?: number | null; month?: number | null },
  asOf?: { year?: number | null; month?: number | null } | null,
): number | null {
  if (!dob.year) return null
  const endYear = asOf?.year ?? new Date().getFullYear()
  const endMonth = asOf?.month ?? (new Date().getMonth() + 1)
  const dobMonth = dob.month ?? 1
  const age = endYear - dob.year - (endMonth < dobMonth ? 1 : 0)
  return age >= 0 ? age : null
}

export function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const s = Math.floor(diff / 1000)
  if (s < 60) return 'just now'
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  if (d < 30) return `${d}d ago`
  const mo = Math.floor(d / 30)
  if (mo < 12) return `${mo}mo ago`
  return `${Math.floor(mo / 12)}y ago`
}

/**
 * Spells the member is still in. `affiliations` carries closed spells as well,
 * so every "which set is this person in now" question has to filter first.
 * Tolerates older payloads that predate is_current.
 */
export function currentAffiliations<T extends { is_current?: boolean; until_date?: unknown }>(
  affiliations: T[] | null | undefined,
): T[] {
  return (affiliations ?? []).filter((a) => a.is_current ?? a.until_date == null)
}

/** The spell that fills primary_set_*: primary if flagged, else the first current one. */
export function primaryAffiliation<
  T extends { is_primary: boolean; is_current?: boolean; until_date?: unknown },
>(affiliations: T[] | null | undefined): T | null {
  const current = currentAffiliations(affiliations)
  return current.find((a) => a.is_primary) ?? current[0] ?? null
}
