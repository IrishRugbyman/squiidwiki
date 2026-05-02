import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function ageFromFuzzyDates(
  dob: { year: number; month?: number | null },
  asOf?: { year: number; month?: number | null } | null,
): number | null {
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
