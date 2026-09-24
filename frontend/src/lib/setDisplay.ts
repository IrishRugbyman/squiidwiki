import type { CSSProperties } from 'react'
import type { NameVariant } from '@/lib/types'

// How a set is named and colored wherever it is shown: the list, its cards,
// the detail page and the form all read these.

// Pick which slot leads display for this variant. Honors v.lead when it
// points to a populated slot; otherwise falls back to name → initials → number.
export function variantLead(v: NameVariant): 'name' | 'initials' | 'number' | null {
  if (v.lead && v[v.lead]?.trim()) return v.lead
  if (v.name?.trim()) return 'name'
  if (v.initials?.trim()) return 'initials'
  if (v.number?.trim()) return 'number'
  return null
}

export function variantDisplay(v: NameVariant): string {
  const lead = variantLead(v)
  return lead ? (v[lead] ?? '').trim() : ''
}

export function variantsToDisplayName(variants: NameVariant[]): string {
  const primary = variants.find((v) => v.is_primary) ?? variants[0]
  return primary ? variantDisplay(primary) : ''
}

// Render one variant compactly using its lead slot first, e.g.
// "5674 (JeffMobb ReubGang · JMRB)" or "Across The Ave (ATA · 282)".
export function formatVariant(v: NameVariant): string {
  const lead = variantLead(v)
  if (!lead) return ''
  const head = (v[lead] ?? '').trim()
  const extras: string[] = []
  for (const slot of ['name', 'initials', 'number'] as const) {
    if (slot === lead) continue
    const val = v[slot]?.trim()
    if (val) extras.push(val)
  }
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
