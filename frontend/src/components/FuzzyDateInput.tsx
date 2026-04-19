import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { FuzzyDateValue } from '@/components/FuzzyDate'

interface Props {
  value: FuzzyDateValue | null
  onChange: (v: FuzzyDateValue | null) => void
  label?: string
  idPrefix: string
}

type Mode = 'exact' | 'year' | 'unknown'

function pickMode(v: FuzzyDateValue | null): Mode {
  if (!v || v.precision === 'UNKNOWN') return 'unknown'
  if (v.precision === 'YMD') return 'exact'
  return 'year'
}

export function FuzzyDateInput({ value, onChange, label, idPrefix }: Props) {
  const [mode, setMode] = useState<Mode>(pickMode(value))
  const [exactDate, setExactDate] = useState(() => {
    if (value?.precision === 'YMD' && value.year && value.month && value.day) {
      return `${value.year}-${String(value.month).padStart(2, '0')}-${String(value.day).padStart(2, '0')}`
    }
    return ''
  })
  const [year, setYear] = useState(() => value?.year?.toString() ?? '')

  useEffect(() => {
    if (mode === 'unknown') {
      onChange({ precision: 'UNKNOWN', approx: false })
    } else if (mode === 'exact' && exactDate) {
      const [y, m, d] = exactDate.split('-').map(Number)
      if (y && m && d) onChange({ year: y, month: m, day: d, precision: 'YMD', approx: false })
    } else if (mode === 'year' && year) {
      const y = parseInt(year, 10)
      if (!isNaN(y)) onChange({ year: y, precision: 'Y', approx: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, exactDate, year])

  return (
    <div className="space-y-2">
      {label && <Label>{label}</Label>}
      <div className="flex gap-3 text-sm text-zinc-300">
        {(['exact', 'year', 'unknown'] as Mode[]).map((m) => (
          <label key={m} className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="radio"
              name={`${idPrefix}-mode`}
              value={m}
              checked={mode === m}
              onChange={() => setMode(m)}
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
          onChange={(e) => setExactDate(e.target.value)}
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
          onChange={(e) => setYear(e.target.value)}
          className="max-w-xs"
        />
      )}
    </div>
  )
}
