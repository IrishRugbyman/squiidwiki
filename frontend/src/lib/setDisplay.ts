import type { CSSProperties } from 'react'
import type { NameSlot, NameVariant } from '@/lib/types'

// How a set is named and colored wherever it is shown: the list, its cards,
// the detail page and the form all read these.
//
// The naming rules mirror backend/app/core/set_names.py, which derives
// `sets.name` from the primary variant. The form previews the name with these
// functions and the backend refuses a name that disagrees with its own, so the
// two must stay in step.

export const NAME_SLOTS: readonly NameSlot[] = ['name', 'initials', 'number']

function filled(v: NameVariant, slot: NameSlot): string {
  return (v[slot] ?? '').trim()
}

// The slots a variant displays, in order: its lead (one slot or several, empty
// ones skipped), else its first filled slot of name, initials, number.
export function leadSlots(v: NameVariant): NameSlot[] {
  const raw = v.lead == null ? [] : Array.isArray(v.lead) ? v.lead : [v.lead]
  const kept = [...new Set(raw)].filter((slot) => NAME_SLOTS.includes(slot) && filled(v, slot))
  if (kept.length > 0) return kept
  const first = NAME_SLOTS.find((slot) => filled(v, slot))
  return first ? [first] : []
}

// The lead as stored: the filled slots it names, a list of one collapsed to the
// slot itself, null when none is left.
export function normalizeLead(v: NameVariant): NameSlot | NameSlot[] | null {
  const raw = v.lead == null ? [] : Array.isArray(v.lead) ? v.lead : [v.lead]
  const kept = [...new Set(raw)].filter((slot) => NAME_SLOTS.includes(slot) && filled(v, slot))
  if (kept.length === 0) return null
  return kept.length === 1 ? kept[0] : kept
}

// The first slot a variant displays; kept for callers that need one.
export function variantLead(v: NameVariant): NameSlot | null {
  return leadSlots(v)[0] ?? null
}

export function variantDisplay(v: NameVariant): string {
  return leadSlots(v).map((slot) => filled(v, slot)).join(' ')
}

export function variantsToDisplayName(variants: NameVariant[]): string {
  const primary = variants.find((v) => v.is_primary) ?? variants[0]
  return primary ? variantDisplay(primary) : ''
}

// The filled slots a variant does not display, for "(Helmet Crew · 462)".
export function variantExtras(v: NameVariant): { slot: NameSlot; value: string }[] {
  const shown = leadSlots(v)
  return NAME_SLOTS.filter((slot) => !shown.includes(slot) && filled(v, slot)).map((slot) => ({
    slot,
    value: filled(v, slot),
  }))
}

// Render one variant compactly, its display first, e.g.
// "5674 (JeffMobb ReubGang · JMRB)" or "CFP 2400 (Cash Flow Posse)".
export function formatVariant(v: NameVariant): string {
  const head = variantDisplay(v)
  if (!head) return ''
  const extras = variantExtras(v).map((e) => e.value)
  return extras.length > 0 ? `${head} (${extras.join(' · ')})` : head
}

export function nonPrimaryVariantsText(variants?: NameVariant[] | null, sep = ' · '): string {
  if (!variants) return ''
  return variants.filter((v) => !v.is_primary).map(formatVariant).filter(Boolean).join(sep)
}

// Perceptually uniform palette: HSL with fixed saturation + lightness so every
// avatar has the same brightness regardless of the hashed hue.
export function setColorStyle(name: string): CSSProperties {
  let h = 0
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) & 0xffff
  const hue = h % 360
  return {
    backgroundColor: `hsl(${hue} 45% 26% / 0.75)`,
    color: `hsl(${hue} 60% 78%)`,
    borderColor: `hsl(${hue} 40% 36% / 0.45)`,
  }
}

// Parse a #RRGGBB / #RGB hex into an [r,g,b] tuple, or null if unparseable.
function parseHex(hex: string): [number, number, number] | null {
  let h = hex.trim().replace(/^#/, '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  if (h.length !== 6 && h.length !== 8) return null
  const n = parseInt(h.slice(0, 6), 16)
  if (Number.isNaN(n)) return null
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff]
}

// Translate a gang's hex color into the same dim-bg / bright-fg / soft-border
// triplet that setColorStyle uses for hashed colors, so avatars stay visually
// consistent regardless of the source.
export function gangColorStyle(hex: string): CSSProperties {
  const rgb = parseHex(hex)
  if (!rgb) return setColorStyle(hex)
  const [r, g, b] = rgb
  return {
    backgroundColor: `rgba(${r}, ${g}, ${b}, 0.22)`,
    color: `rgb(${Math.min(255, r + 80)}, ${Math.min(255, g + 80)}, ${Math.min(255, b + 80)})`,
    borderColor: `rgba(${r}, ${g}, ${b}, 0.55)`,
  }
}
