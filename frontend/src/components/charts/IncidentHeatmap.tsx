import { useMemo, useState } from 'react'
import type { IncidentListItem } from '@/lib/types'

const WEEKDAY_LABELS = ['', 'Mon', '', 'Wed', '', 'Fri', '']
const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

interface DayCell {
  date: Date
  key: string
  inYear: boolean
  count: number
  murders: number
}

function colorFor(count: number, murders: number): string {
  if (count === 0) return 'bg-zinc-900/70'
  if (murders > 0) {
    if (count >= 4) return 'bg-rose-500'
    if (count >= 2) return 'bg-rose-700'
    return 'bg-rose-800/80'
  }
  if (count >= 4) return 'bg-amber-400'
  if (count >= 2) return 'bg-amber-600'
  return 'bg-amber-800/80'
}

function fmtKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function fmtTooltip(d: Date): string {
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}

function buildYear(year: number, counts: Map<string, { count: number; murders: number }>): DayCell[][] {
  // Pad to start on Sunday so week columns align.
  const start = new Date(year, 0, 1)
  const cursor = new Date(start)
  cursor.setDate(cursor.getDate() - start.getDay())
  const end = new Date(year, 11, 31)

  const weeks: DayCell[][] = []
  while (cursor <= end || cursor.getDay() !== 0) {
    const week: DayCell[] = []
    for (let i = 0; i < 7; i++) {
      const date = new Date(cursor)
      const key = fmtKey(date)
      const c = counts.get(key)
      week.push({
        date,
        key,
        inYear: date.getFullYear() === year,
        count: c?.count ?? 0,
        murders: c?.murders ?? 0,
      })
      cursor.setDate(cursor.getDate() + 1)
    }
    weeks.push(week)
    if (cursor.getFullYear() > year && cursor.getDay() === 0) break
  }
  return weeks
}

interface IncidentHeatmapProps {
  incidents: IncidentListItem[]
}

export function IncidentHeatmap({ incidents }: IncidentHeatmapProps) {
  const availableYears = useMemo(() => {
    const set = new Set<number>()
    for (const inc of incidents) {
      if (inc.date?.precision === 'YMD' && inc.date.year) set.add(inc.date.year)
    }
    if (set.size === 0) {
      const y = new Date().getFullYear()
      return [y]
    }
    // Fill the full range so missing years are still browsable
    const min = Math.min(...set)
    const max = Math.max(...set)
    const years: number[] = []
    for (let y = min; y <= max; y++) years.push(y)
    return years
  }, [incidents])

  const [year, setYear] = useState<number>(availableYears[availableYears.length - 1])

  const countsByDate = useMemo(() => {
    const map = new Map<string, { count: number; murders: number }>()
    for (const inc of incidents) {
      const d = inc.date
      if (!d || d.precision !== 'YMD' || !d.year || !d.month || !d.day) continue
      const key = `${d.year}-${String(d.month).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`
      const e = map.get(key) ?? { count: 0, murders: 0 }
      e.count++
      if (inc.type === 'MURDER') e.murders++
      map.set(key, e)
    }
    return map
  }, [incidents])

  const weeks = useMemo(() => buildYear(year, countsByDate), [year, countsByDate])

  const yearTotal = useMemo(() => {
    let total = 0, murders = 0
    for (const wk of weeks) {
      for (const d of wk) {
        if (d.inYear) {
          total += d.count
          murders += d.murders
        }
      }
    }
    return { total, murders }
  }, [weeks])

  // Compute month-label positions: the column index where each month first appears
  const monthLabels = useMemo(() => {
    const labels: { month: number; col: number }[] = []
    let lastMonth = -1
    weeks.forEach((wk, col) => {
      const firstInYear = wk.find((d) => d.inYear)
      if (firstInYear) {
        const m = firstInYear.date.getMonth()
        if (m !== lastMonth) {
          labels.push({ month: m, col })
          lastMonth = m
        }
      }
    })
    return labels
  }, [weeks])

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Calendar density</h2>
          <p className="mt-0.5 text-xs text-zinc-400">
            {yearTotal.total} dated incident{yearTotal.total === 1 ? '' : 's'} in {year}
            {yearTotal.murders > 0 ? ` · ${yearTotal.murders} murder${yearTotal.murders === 1 ? '' : 's'}` : ''}
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-900/60 p-1">
          {availableYears.map((y) => (
            <button
              key={y}
              type="button"
              onClick={() => setYear(y)}
              className={`rounded px-2 py-0.5 text-[11px] font-medium tabular-nums transition-colors ${
                y === year ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'
              }`}
            >
              {y}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="inline-block min-w-fit">
          {/* Month labels */}
          <div className="ml-7 flex" style={{ height: 12 }}>
            {weeks.map((_, col) => {
              const label = monthLabels.find((l) => l.col === col)
              return (
                <div key={col} className="text-[9px] text-zinc-400" style={{ width: 12 }}>
                  {label ? MONTH_LABELS[label.month] : ''}
                </div>
              )
            })}
          </div>
          <div className="flex gap-[2px]">
            {/* Weekday labels column */}
            <div className="mr-1 flex flex-col justify-between text-[9px] text-zinc-400" style={{ paddingTop: 1 }}>
              {WEEKDAY_LABELS.map((d, i) => (
                <div key={i} style={{ height: 10 }}>{d}</div>
              ))}
            </div>
            {/* Weeks */}
            {weeks.map((wk, col) => (
              <div key={col} className="flex flex-col gap-[2px]">
                {wk.map((d) => (
                  <div
                    key={d.key}
                    title={
                      d.inYear
                        ? `${fmtTooltip(d.date)} · ${d.count} incident${d.count === 1 ? '' : 's'}${d.murders > 0 ? ` (${d.murders} murder${d.murders === 1 ? '' : 's'})` : ''}`
                        : ''
                    }
                    className={`h-[10px] w-[10px] rounded-md ${d.inYear ? colorFor(d.count, d.murders) : 'bg-transparent'}`}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-3 flex items-center justify-end gap-1.5 text-[10px] text-zinc-400">
        <span>Less</span>
        <span className="h-[10px] w-[10px] rounded-md bg-zinc-900/70" />
        <span className="h-[10px] w-[10px] rounded-md bg-amber-800/80" />
        <span className="h-[10px] w-[10px] rounded-md bg-amber-600" />
        <span className="h-[10px] w-[10px] rounded-md bg-amber-400" />
        <span className="h-[10px] w-[10px] rounded-md bg-rose-500" />
        <span>More · murders shown red</span>
      </div>
    </div>
  )
}

export default IncidentHeatmap
