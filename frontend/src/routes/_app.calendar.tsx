import { createFileRoute } from '@tanstack/react-router'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { Button } from '@/components/ui/button'
import { useIncidents, useMembers } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import type { FuzzyDateValue } from '@/components/FuzzyDate'

export const Route = createFileRoute('/_app/calendar')({
  component: CalendarPage,
})

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

function fuzzyToDate(v: FuzzyDateValue | null): { year: number; month?: number; day?: number } | null {
  if (!v || v.precision === 'UNKNOWN') return null
  return { year: v.year!, month: v.month ?? undefined, day: v.day ?? undefined }
}

interface CalendarEvent {
  id: string
  label: string
  type: 'incident' | 'death'
  color: string
  href: string
}

function CalendarPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1) // 1-indexed

  const { data: incidentData } = useIncidents(universe?.id ?? null)
  const { data: memberData } = useMembers(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  const incidents = incidentData?.items ?? []
  const members = memberData?.items ?? []

  // Build a day → events map for the current month/year
  const dayEvents: Record<number, CalendarEvent[]> = {}

  for (const inc of incidents) {
    const d = fuzzyToDate(inc.date)
    if (!d || d.year !== year || d.month !== month || !d.day) continue
    dayEvents[d.day] ??= []
    dayEvents[d.day].push({
      id: inc.id,
      label: inc.type,
      type: 'incident',
      color: inc.verified ? 'bg-violet-900 text-violet-300' : 'bg-zinc-800 text-zinc-400',
      href: `/incidents/${inc.id}`,
    })
  }

  for (const m of members) {
    if (m.status !== 'DEAD') continue
    const d = fuzzyToDate((m as any).date_of_death ?? null)
    if (!d || d.year !== year || d.month !== month || !d.day) continue
    dayEvents[d.day] ??= []
    dayEvents[d.day].push({
      id: m.id + '-death',
      label: m.display_name,
      type: 'death',
      color: 'bg-red-950 text-red-400',
      href: `/members/${(m as any).slug ?? m.id}`,
    })
  }

  // Grid layout
  const firstDay = new Date(year, month - 1, 1).getDay() // 0=Sun
  const daysInMonth = new Date(year, month, 0).getDate()

  function prevMonth() {
    if (month === 1) { setMonth(12); setYear(year - 1) }
    else setMonth(month - 1)
  }
  function nextMonth() {
    if (month === 12) { setMonth(1); setYear(year + 1) }
    else setMonth(month + 1)
  }

  const cells: (number | null)[] = [
    ...Array.from({ length: firstDay }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]
  while (cells.length % 7 !== 0) cells.push(null)

  const weeks: (number | null)[][] = []
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7))

  const isToday = (d: number) =>
    d === today.getDate() && month === today.getMonth() + 1 && year === today.getFullYear()

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">
          {MONTH_NAMES[month - 1]} {year}
        </h1>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={prevMonth}><ChevronLeft className="h-4 w-4" /></Button>
          <Button variant="outline" size="sm" onClick={() => { setYear(today.getFullYear()); setMonth(today.getMonth() + 1) }}>Today</Button>
          <Button variant="outline" size="sm" onClick={nextMonth}><ChevronRight className="h-4 w-4" /></Button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <div className="grid grid-cols-7 border-b border-zinc-800">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
            <div key={d} className="py-2 text-center text-xs font-medium text-zinc-500">{d}</div>
          ))}
        </div>
        {weeks.map((week, wi) => (
          <div key={wi} className="grid grid-cols-7 divide-x divide-zinc-800 border-b border-zinc-800 last:border-b-0">
            {week.map((day, di) => (
              <div
                key={di}
                className={`min-h-[80px] p-1.5 ${day ? 'bg-zinc-950' : 'bg-zinc-900/20'}`}
              >
                {day && (
                  <>
                    <div className={`mb-1 text-xs font-medium ${isToday(day) ? 'flex h-5 w-5 items-center justify-center rounded-full bg-violet-600 text-white' : 'text-zinc-500'}`}>
                      {day}
                    </div>
                    <div className="space-y-0.5">
                      {(dayEvents[day] ?? []).slice(0, 3).map((ev) => (
                        <a key={ev.id} href={ev.href}>
                          <div className={`truncate rounded px-1 py-0.5 text-[10px] font-medium ${ev.color} hover:opacity-80 transition-opacity`}>
                            {ev.label}
                          </div>
                        </a>
                      ))}
                      {(dayEvents[day] ?? []).length > 3 && (
                        <div className="text-[10px] text-zinc-600">+{(dayEvents[day] ?? []).length - 3} more</div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
