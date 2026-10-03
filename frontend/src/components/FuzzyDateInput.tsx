import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { FuzzyDateValue } from '@/components/FuzzyDate'

interface Props {
  value: FuzzyDateValue | null
  onChange: (v: FuzzyDateValue | null) => void
  label?: string
  idPrefix: string
  // Optional "Life" mode — used by LOCKED member release dates. When provided,
  // a 4th radio button appears; selecting it sets life=true and date=null.
  life?: { value: boolean; onChange: (v: boolean) => void }
}

type Mode = 'exact' | 'year' | 'unknown' | 'life'

function pickMode(v: FuzzyDateValue | null, lifeFlag: boolean): Mode {
  if (lifeFlag) return 'life'
  if (!v || v.precision === 'UNKNOWN') return 'unknown'
  if (v.precision === 'YMD') return 'exact'
  return 'year'
}

export function FuzzyDateInput({ value, onChange, label, idPrefix, life }: Props) {
  const [mode, setMode] = useState<Mode>(pickMode(value, life?.value ?? false))
  const [exactDate, setExactDate] = useState(() => {
    if (value?.precision === 'YMD' && value.year && value.month && value.day) {
      return `${value.year}-${String(value.month).padStart(2, '0')}-${String(value.day).padStart(2, '0')}`
    }
    return ''
  })
  const [year, setYear] = useState(() => value?.year?.toString() ?? '')

  /**
   * Report a change the user made, and only then. This used to run from an
   * effect, which also fires on mount: opening a form re-encoded the date on
   * file through these three modes before anyone touched it, so an unchanged
   * save turned "June 2022" into "circa 2022" (a month-precision date has no
   * mode of its own here) and marked every bare year approximate.
   */
  function emit(nextMode: Mode, nextExact: string, nextYear: string) {
    if (life) life.onChange(nextMode === 'life')
    if (nextMode === 'life') {
      onChange(null)
    } else if (nextMode === 'unknown') {
      onChange({ precision: 'UNKNOWN', approx: false })
    } else if (nextMode === 'exact' && nextExact) {
      const [y, m, d] = nextExact.split('-').map(Number)
      if (y && m && d) onChange({ year: y, month: m, day: d, precision: 'YMD', approx: false })
    } else if (nextMode === 'year' && nextYear) {
      const y = parseInt(nextYear, 10)
      if (!isNaN(y)) onChange({ year: y, precision: 'Y', approx: true })
    }
  }

  const modes: Mode[] = life ? ['exact', 'year', 'unknown', 'life'] : ['exact', 'year', 'unknown']

  return (
    <div className="space-y-2">
      {label && <Label>{label}</Label>}
      <div className="flex flex-wrap gap-3 text-sm text-zinc-300">
        {modes.map((m) => (
          <label key={m} className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="radio"
              name={`${idPrefix}-mode`}
              value={m}
              checked={mode === m}
              onChange={() => { setMode(m); emit(m, exactDate, year) }}
              className="accent-violet-600"
            />
            <span className="capitalize">{m}</span>
          </label>
        ))}
      </div>
      {mode === 'exact' && (
        <Input
          type="date"
          value={exactDate}
          onChange={(e) => { setExactDate(e.target.value); emit(mode, e.target.value, year) }}
          className="max-w-xs"
        />
      )}
      {mode === 'year' && (
        <Input
          type="number"
          placeholder="YYYY"
          min={1900}
          max={2100}
          value={year}
          onChange={(e) => { setYear(e.target.value); emit(mode, exactDate, e.target.value) }}
          className="max-w-xs"
        />
      )}
      {mode === 'life' && (
        <p className="text-xs text-zinc-400">No release, sentenced to life.</p>
      )}
    </div>
  )
}
