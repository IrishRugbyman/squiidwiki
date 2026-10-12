import { normalizeLead, variantsToDisplayName } from './setDisplay'
import type { NameVariant } from './types'

// Form-side handling of names in slots, shared by the set and alliance forms
// (components/names/NameVariantsEditor.tsx renders them).

export function emptyVariant(isPrimary = false): NameVariant {
  return { name: '', initials: '', number: '', is_primary: isPrimary, lead: null }
}

/** The form's starting variants: the record's own, else one built from its name. */
export function seedVariants(src: { name?: string | null; name_variants?: NameVariant[] | null } | null | undefined): NameVariant[] {
  if (src?.name_variants?.length) {
    return src.name_variants.map((v) => ({
      name: v.name ?? '',
      initials: v.initials ?? '',
      number: v.number ?? '',
      is_primary: !!v.is_primary,
      lead: v.lead ?? null,
    }))
  }
  return [{ name: src?.name ?? '', initials: '', number: '', is_primary: true, lead: null }]
}

/** Variants ready to send, with the name the backend will derive from them,
 *  or the reason they cannot be saved. */
export function cleanVariants(variants: NameVariant[]): { variants: NameVariant[]; name: string } | { error: string } {
  const cleaned = variants
    .map((v) => {
      const c = {
        name: (v.name ?? '').trim() || null,
        initials: (v.initials ?? '').trim() || null,
        number: (v.number ?? '').trim() || null,
        is_primary: v.is_primary,
        lead: v.lead ?? null,
      }
      // Slots the lead names but the variant leaves empty are dropped.
      return { ...c, lead: normalizeLead(c) }
    })
    .filter((v) => v.name || v.initials || v.number)
  if (cleaned.length === 0) return { error: 'At least one name variant is required' }
  if (!cleaned.some((v) => v.is_primary)) cleaned[0].is_primary = true
  // The backend derives the name from the primary variant and refuses one that
  // disagrees, so this is the same computation, not a guess.
  const name = variantsToDisplayName(cleaned)
  if (!name) return { error: 'The primary variant must have a name, initials, or number' }
  return { variants: cleaned, name }
}
