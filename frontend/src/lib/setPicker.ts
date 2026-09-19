import type { ComboboxItem } from '@/components/members/MemberFormSheet/pickers/AffiliationCombobox'
import type { SetListItem } from '@/lib/types'

/**
 * Sets as searchable combobox rows. Every name variant's name, initials and
 * number is searchable, so "ABC" or "313" finds a set whose display name is
 * neither, and two sets sharing initials both come up.
 */
export function setPickerItems(sets: SetListItem[]): ComboboxItem[] {
  return sets.map((s) => ({
    id: s.id,
    name: s.name,
    hint: s.status === 'EXTINCT' ? 'extinct' : undefined,
    dotClass: s.status === 'EXTINCT' ? 'bg-zinc-600' : 'bg-emerald-400',
    keywords: (s.name_variants ?? [])
      .flatMap((v) => [v.name, v.initials, v.number])
      .filter(Boolean)
      .join(' '),
  }))
}
