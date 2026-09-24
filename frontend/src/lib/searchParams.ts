/**
 * A free-text URL search param. TanStack Router parses `?q=4822` as the number
 * 4822, so a validator that accepted strings only dropped every all-digit
 * search (a ZIP code, a set named "700") from a pasted or reloaded link.
 */
export function textParam(v: unknown): string | undefined {
  if (typeof v === 'number' && Number.isFinite(v)) return String(v)
  return typeof v === 'string' && v ? v : undefined
}
