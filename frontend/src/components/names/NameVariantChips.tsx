import { variantDisplay, variantExtras } from '@/lib/setDisplay'
import type { NameVariant } from '@/lib/types'

/** Under a set or alliance title: the primary name's other slots as labelled
 *  chips ("INITIALS CFP", "NUMBER 2400"), then every other variant as an a/k/a pill. */
export function NameVariantChips({ variants }: { variants: NameVariant[] | null | undefined }) {
  const all = variants ?? []
  const primary = all.find((v) => v.is_primary)
  const others = all.filter((v) => !v.is_primary)
  const primaryExtras = primary ? variantExtras(primary) : []
  if (primaryExtras.length === 0 && others.length === 0) return null
  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
      {primaryExtras.map(({ slot, value }) => (
        <span key={slot} className="inline-flex items-center gap-1 rounded-full bg-zinc-800/70 px-2 py-0.5 text-zinc-300">
          <span className="text-[10px] uppercase tracking-wider text-zinc-400">{slot}</span>
          {value}
        </span>
      ))}
      {others.length > 0 && <span className="ml-1 text-[10px] uppercase tracking-wider text-zinc-400">a/k/a</span>}
      {others.map((v, i) => {
        const shown = variantDisplay(v)
        if (!shown) return null
        const extras = variantExtras(v).map((e) => e.value)
        return (
          <span key={i} className="inline-flex items-center gap-1 rounded-full border border-zinc-800 bg-zinc-900/60 px-2 py-0.5 text-zinc-400">
            <span className="text-zinc-200">{shown}</span>
            {extras.length > 0 && <span>· {extras.join(' · ')}</span>}
          </span>
        )
      })}
    </div>
  )
}
