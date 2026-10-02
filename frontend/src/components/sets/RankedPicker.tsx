import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const NONE = '__none__'

interface Option {
  id: string
  name: string
}

interface RankedPickerProps {
  /** Chosen ids in rank order; the first is the primary. */
  value: string[]
  onChange: (next: string[]) => void
  options: Option[]
  /** Singular noun for labels: "gang", "alliance". */
  noun: string
}

/**
 * An ordered multi-pick: chips for what is chosen, primary first, each with
 * "make primary" and remove, and a select to add another. A set's gangs and its
 * alliances both work this way, the first mirrored into the set's single column.
 */
export function RankedPicker({ value, onChange, options, noun }: RankedPickerProps) {
  const byId = new Map(options.map((o) => [o.id, o]))
  return (
    <>
      {value.length > 0 && (
        <ul className="flex flex-wrap gap-1.5" aria-label={`${noun[0].toUpperCase()}${noun.slice(1)}s, primary first`}>
          {value.map((id, i) => {
            const name = byId.get(id)?.name ?? `Unknown ${noun}`
            return (
              <li
                key={id}
                className="flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800/60 py-0.5 pl-2 pr-1 text-xs text-zinc-200"
              >
                <span>{name}</span>
                {i === 0 && value.length > 1 && <span className="text-[10px] text-zinc-500">primary</span>}
                {i > 0 && (
                  <button
                    type="button"
                    className="rounded px-1 text-zinc-500 hover:text-zinc-200"
                    onClick={() => onChange([id, ...value.filter((x) => x !== id)])}
                    aria-label={`Make ${name} the primary ${noun}`}
                    title="Make primary"
                  >
                    ↑
                  </button>
                )}
                <button
                  type="button"
                  className="rounded px-1 text-zinc-500 hover:text-red-400"
                  onClick={() => onChange(value.filter((x) => x !== id))}
                  aria-label={`Remove ${name}`}
                >
                  ×
                </button>
              </li>
            )
          })}
        </ul>
      )}
      <Select
        value={NONE}
        onValueChange={(v) => { if (v !== NONE && !value.includes(v)) onChange([...value, v]) }}
      >
        <SelectTrigger aria-label={`Add a ${noun}`}>
          <SelectValue placeholder={value.length ? `Add another ${noun}` : `No ${noun}`} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE}>{value.length ? `Add another ${noun}` : `No ${noun}`}</SelectItem>
          {options
            .filter((o) => !value.includes(o.id))
            .map((o) => (
              <SelectItem key={o.id} value={o.id}>{o.name}</SelectItem>
            ))}
        </SelectContent>
      </Select>
    </>
  )
}
