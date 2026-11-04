import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { leadSlots, variantDisplay } from '@/lib/setDisplay'
import { emptyVariant } from '@/lib/nameVariants'
import type { NameVariant } from '@/lib/types'

// The name editor shared by the set and alliance forms: one card per variant,
// its slots, which variant is primary, and which slots it shows (in click order,
// so Initials then Number shows "CFP 2400"). The display rules are in
// lib/setDisplay.ts and mirror app/core/set_names.py on the backend.

const SLOT_PLACEHOLDER = { name: 'Across The Ave', initials: 'ATA', number: '282' } as const

export function NameVariantsEditor({ variants, onChange, radioName, noun }: {
  variants: NameVariant[]
  onChange: (next: NameVariant[] | ((prev: NameVariant[]) => NameVariant[])) => void
  /** Unique per form, so two open forms do not share one radio group. */
  radioName: string
  /** "set" or "alliance", for the hint. */
  noun: string
}) {
  const edit = (idx: number, patch: Partial<NameVariant>) =>
    onChange((prev) => prev.map((x, i) => (i === idx ? { ...x, ...patch } : x)))

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Names *</Label>
        <span className="text-[11px] text-zinc-400">Primary is shown as the {noun}'s display name</span>
      </div>
      <div className="space-y-2">
        {variants.map((v, idx) => (
          <div
            key={idx}
            className={`rounded-md border p-2 ${v.is_primary ? 'border-violet-700/60 bg-violet-950/20' : 'border-zinc-800 bg-zinc-950/40'}`}
          >
            <div className="grid grid-cols-3 gap-2">
              {(['name', 'initials', 'number'] as const).map((slot) => (
                <div key={slot} className="space-y-1">
                  <Label className="text-[11px] capitalize text-zinc-400">{slot}</Label>
                  <Input
                    value={v[slot] ?? ''}
                    onChange={(e) => edit(idx, { [slot]: e.target.value })}
                    placeholder={SLOT_PLACEHOLDER[slot]}
                  />
                </div>
              ))}
            </div>
            <div className="mt-2 flex items-center justify-between gap-3">
              <label className="flex cursor-pointer items-center gap-1.5 text-xs text-zinc-400">
                <input
                  type="radio"
                  name={radioName}
                  checked={v.is_primary}
                  onChange={() => onChange((prev) => prev.map((x, i) => ({ ...x, is_primary: i === idx })))}
                  className="h-3 w-3 accent-violet-500"
                />
                Primary
              </label>
              <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-zinc-400">
                <span title="Pick the parts shown, in the order you click them: Initials then Number shows CFP 2400">Show as</span>
                {(['name', 'initials', 'number'] as const).map((slot) => {
                  const filled = !!v[slot]?.trim()
                  const shown = leadSlots(v)
                  const position = shown.indexOf(slot)
                  const active = position >= 0
                  return (
                    <button
                      key={slot}
                      type="button"
                      disabled={!filled}
                      aria-pressed={active}
                      onClick={() =>
                        onChange((prev) =>
                          prev.map((x, i) => {
                            if (i !== idx) return x
                            const current = leadSlots(x)
                            const next = current.includes(slot) ? current.filter((s) => s !== slot) : [...current, slot]
                            return { ...x, lead: next.length === 0 ? null : next.length === 1 ? next[0] : next }
                          }),
                        )
                      }
                      className={`rounded px-1.5 py-0.5 capitalize transition-colors ${
                        active && filled
                          ? 'bg-violet-700/40 text-violet-200 ring-1 ring-violet-600/50'
                          : filled
                            ? 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                            : 'cursor-not-allowed opacity-30'
                      }`}
                    >
                      {active && shown.length > 1 ? `${position + 1}. ` : ''}
                      {slot}
                    </button>
                  )
                })}
                {variantDisplay(v) && (
                  <span className="ml-1 text-zinc-300">
                    → <span className="font-medium text-zinc-100">{variantDisplay(v)}</span>
                  </span>
                )}
              </div>
              {variants.length > 1 && (
                <button
                  type="button"
                  onClick={() =>
                    onChange((prev) => {
                      const next = prev.filter((_, i) => i !== idx)
                      if (!next.some((x) => x.is_primary) && next.length > 0) next[0] = { ...next[0], is_primary: true }
                      return next
                    })
                  }
                  className="text-xs text-zinc-400 hover:text-red-400"
                >
                  Remove
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      <Button type="button" variant="outline" size="sm" onClick={() => onChange((prev) => [...prev, emptyVariant(false)])}>
        <Plus className="mr-1 h-3.5 w-3.5" />
        Add variant
      </Button>
    </div>
  )
}
