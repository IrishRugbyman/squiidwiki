import { createFileRoute, Link } from '@tanstack/react-router'
import { ChevronLeft, ChevronRight, Skull, Swords } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { Button } from '@/components/ui/button'
import { useAllIncidents, useAllMembers } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import type { FuzzyDateValue } from '@/components/FuzzyDate'

export const Route = createFileRoute('/_app/calendar')({
  component: CalendarPage,
})

// ─── Constants ────────────────────────────────────────────────────────────────

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

// ─── Event types ─────────────────────────────────────────────────────────────

type EventKind = 'SHOOTING' | 'MURDER' | 'DEATH'

const KIND_CONFIG: Record<EventKind, {
  dot: string; pill: string; pillHover: string; icon: typeof Skull; label: string
}> = {
  SHOOTING: { dot: 'bg-amber-500',  pill: 'bg-amber-950/80 text-amber-300 ring-1 ring-amber-800/50',  pillHover: 'hover:ring-amber-500',  icon: Swords, label: 'Shooting' },
  MURDER:   { dot: 'bg-rose-500',   pill: 'bg-rose-950/80 text-rose-300 ring-1 ring-rose-800/50',     pillHover: 'hover:ring-rose-500',    icon: Skull,  label: 'Murder'   },
  DEATH:    { dot: 'bg-zinc-500',   pill: 'bg-zinc-900 text-zinc-400 ring-1 ring-zinc-700',            pillHover: 'hover:ring-zinc-500',    icon: Skull,  label: 'Death'    },
}

interface CalendarEvent {
  id: string
  kind: EventKind
  label: string
  sublabel?: string
  href: string
  date: FuzzyDateValue | null
  verified?: boolean
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fuzzyToDay(v: FuzzyDateValue | null): { year: number; month: number; day: number } | null {
  if (!v || v.precision === 'UNKNOWN' || !v.year || !v.month || !v.day) return null
  return { year: v.year, month: v.month, day: v.day }
}

function fuzzyMatchesMonth(v: FuzzyDateValue | null, year: number, month: number): boolean {
  if (!v || v.precision === 'UNKNOWN' || !v.year) return false
  if (v.year !== year) return false
  if (v.month && v.month !== month) return false
  return true
}

// ─── Day detail panel ─────────────────────────────────────────────────────────

function DayDetail({ day, month, year, events, onClose }: {
  day: number; month: number; year: number; events: CalendarEvent[]; onClose: () => void
}) {
  const dateStr = `${MONTH_NAMES[month - 1]} ${day}, ${year}`
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">{dateStr}</h3>
        <button onClick={onClose} className="text-zinc-600 hover:text-zinc-400 transition-colors text-xs">✕</button>
      </div>
      <div className="space-y-2">
        {events.map((ev) => {
          const cfg = KIND_CONFIG[ev.kind]
          const Icon = cfg.icon
          return (
            <Link
              key={ev.id}
              to={ev.href as any}
              className={`flex items-start gap-3 rounded-lg p-2.5 transition-all ${cfg.pill} ${cfg.pillHover}`}
            >
              <div className="mt-0.5 shrink-0">
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-xs font-medium">{ev.label}</p>
                {ev.sublabel && <p className="mt-0.5 truncate text-[11px] opacity-70">{ev.sublabel}</p>}
                {ev.kind !== 'DEATH' && ev.verified !== undefined && (
                  <p className={`mt-0.5 text-[11px] ${ev.verified ? 'text-emerald-500' : 'opacity-50'}`}>
                    {ev.verified ? '✓ Verified' : 'Unverified'}
                  </p>
                )}
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ─── Month summary ────────────────────────────────────────────────────────────

function MonthSummary({ events }: { events: CalendarEvent[] }) {
  const murders   = events.filter((e) => e.kind === 'MURDER').length
  const shootings = events.filter((e) => e.kind === 'SHOOTING').length
  const deaths    = events.filter((e) => e.kind === 'DEATH').length

  if (!murders && !shootings && !deaths) return null

  const parts = [
    murders   > 0 && { label: `${murders} murder${murders !== 1 ? 's' : ''}`,   color: 'text-rose-400',  dot: 'bg-rose-500' },
    shootings > 0 && { label: `${shootings} shooting${shootings !== 1 ? 's' : ''}`, color: 'text-amber-400', dot: 'bg-amber-500' },
    deaths    > 0 && { label: `${deaths} death${deaths !== 1 ? 's' : ''}`,       color: 'text-zinc-400',  dot: 'bg-zinc-500' },
  ].filter(Boolean) as { label: string; color: string; dot: string }[]

  return (
    <div className="flex flex-wrap items-center gap-3">
      {parts.map(({ label, color, dot }) => (
        <span key={label} className={`inline-flex items-center gap-1.5 text-xs ${color}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
          {label}
        </span>
      ))}
    </div>
  )
}

// ─── Month/year picker ────────────────────────────────────────────────────────

function MonthYearPicker({ year, month, onChange }: {
  year: number; month: number; onChange: (y: number, m: number) => void
}) {
  const [open, setOpen] = useState(false)
  const [pickerYear, setPickerYear] = useState(year)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  useEffect(() => { if (open) setPickerYear(year) }, [open, year])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xl font-bold text-white hover:bg-zinc-800 transition-colors"
      >
        {MONTH_NAMES[month - 1]} <span className="text-zinc-500">{year}</span>
        <ChevronRight className={`h-4 w-4 text-zinc-500 transition-transform ${open ? 'rotate-90' : ''}`} />
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-1 w-64 rounded-xl border border-zinc-700 bg-zinc-900 p-3 shadow-xl">
          {/* Year row */}
          <div className="mb-3 flex items-center justify-between">
            <button onClick={() => setPickerYear((y) => y - 1)}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm font-semibold text-white">{pickerYear}</span>
            <button onClick={() => setPickerYear((y) => y + 1)}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          {/* Month grid */}
          <div className="grid grid-cols-3 gap-1">
            {MONTH_NAMES.map((name, i) => {
              const m = i + 1
              const isActive = m === month && pickerYear === year
              return (
                <button key={m} onClick={() => { onChange(pickerYear, m); setOpen(false) }}
                  className={`rounded-md py-1.5 text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-violet-600 text-white'
                      : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                  }`}>
                  {name.slice(0, 3)}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function CalendarPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const today = new Date()
  const [year, setYear]   = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [selectedDay, setSelectedDay] = useState<number | null>(null)

  // Keyboard navigation
  useEffect(() => {
    function handle(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === 'ArrowLeft') {
        setSelectedDay(null)
        setMonth((m) => { if (m === 1) { setYear((y) => y - 1); return 12 } return m - 1 })
      }
      if (e.key === 'ArrowRight') {
        setSelectedDay(null)
        setMonth((m) => { if (m === 12) { setYear((y) => y + 1); return 1 } return m + 1 })
      }
    }
    window.addEventListener('keydown', handle)
    return () => window.removeEventListener('keydown', handle)
  }, [])

  const { data: incidentData } = useAllIncidents(universe?.id ?? null)
  const { data: memberData }   = useAllMembers(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  const incidents = incidentData?.items ?? []
  const members   = memberData?.items ?? []

  // Collect all events for this month
  const allMonthEvents: CalendarEvent[] = []

  for (const inc of incidents) {
    if (!fuzzyMatchesMonth(inc.date, year, month)) continue
    const victims = inc.victim_names ?? []
    const label = victims.length > 0
      ? victims.slice(0, 2).join(', ') + (victims.length > 2 ? ` +${victims.length - 2}` : '')
      : (inc.type === 'MURDER' ? 'Murder' : 'Shooting')
    allMonthEvents.push({
      id: inc.id,
      kind: inc.type as EventKind,
      label,
      sublabel: victims.length > 0 ? (inc.type === 'MURDER' ? 'Murder' : 'Shooting') : undefined,
      href: `/incidents/${inc.id}`,
      date: inc.date,
      verified: inc.verified,
    })
  }

  for (const m of members) {
    if (m.status !== 'DEAD' || !m.date_of_death) continue
    if (!fuzzyMatchesMonth(m.date_of_death, year, month)) continue
    allMonthEvents.push({
      id: m.id + '-death',
      kind: 'DEATH',
      label: m.display_name,
      sublabel: 'Died',
      href: `/members/${m.slug ?? m.id}`,
      date: m.date_of_death,
    })
  }

  // day → events (only precise-day events go on the grid)
  const dayEvents: Record<number, CalendarEvent[]> = {}
  for (const ev of allMonthEvents) {
    const d = fuzzyToDay(ev.date)
    if (!d || d.year !== year || d.month !== month) continue
    dayEvents[d.day] ??= []
    dayEvents[d.day].push(ev)
  }

  // Month-level events (year+month precision, no day)
  const monthLevelEvents = allMonthEvents.filter((ev) => {
    const v = ev.date
    return v && v.year === year && v.month === month && !v.day
  })

  // Calendar grid
  const firstDay   = new Date(year, month - 1, 1).getDay()
  const daysInMonth = new Date(year, month, 0).getDate()

  const cells: (number | null)[] = [
    ...Array.from({ length: firstDay }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]
  while (cells.length % 7 !== 0) cells.push(null)
  const weeks: (number | null)[][] = []
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7))

  const isToday = (d: number) =>
    d === today.getDate() && month === today.getMonth() + 1 && year === today.getFullYear()

  function prevMonth() {
    setSelectedDay(null)
    if (month === 1) { setMonth(12); setYear(year - 1) } else setMonth(month - 1)
  }
  function nextMonth() {
    setSelectedDay(null)
    if (month === 12) { setMonth(1); setYear(year + 1) } else setMonth(month + 1)
  }
  function goToday() {
    setSelectedDay(null)
    setYear(today.getFullYear()); setMonth(today.getMonth() + 1)
  }

  const selectedEvents = selectedDay ? (dayEvents[selectedDay] ?? []) : []

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <MonthYearPicker year={year} month={month} onChange={(y, m) => { setYear(y); setMonth(m); setSelectedDay(null) }} />
          <div className="mt-1 pl-2">
            <MonthSummary events={allMonthEvents} />
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Legend */}
          <div className="hidden items-center gap-3 sm:flex mr-2">
            {(Object.entries(KIND_CONFIG) as [EventKind, typeof KIND_CONFIG[EventKind]][]).map(([kind, cfg]) => (
              <span key={kind} className="inline-flex items-center gap-1.5 text-xs text-zinc-500">
                <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
                {cfg.label}
              </span>
            ))}
          </div>
          <Button variant="outline" size="sm" onClick={prevMonth}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={goToday}>Today</Button>
          <Button variant="outline" size="sm" onClick={nextMonth}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Month-level events (imprecise dates) */}
      {monthLevelEvents.length > 0 && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-3">
          <p className="mb-2 text-xs font-medium text-zinc-500">Events with approximate dates this month</p>
          <div className="flex flex-wrap gap-2">
            {monthLevelEvents.map((ev) => {
              const cfg = KIND_CONFIG[ev.kind]
              const Icon = cfg.icon
              return (
                <Link key={ev.id} to={ev.href as any}
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs ${cfg.pill} ${cfg.pillHover} transition-all`}>
                  <Icon className="h-3 w-3" />
                  {ev.label}
                </Link>
              )
            })}
          </div>
        </div>
      )}

      {/* Grid + detail panel */}
      <div className={`grid gap-4 ${selectedDay && selectedEvents.length ? 'lg:grid-cols-[1fr_240px]' : 'grid-cols-1'}`}>

        {/* Calendar grid */}
        <div className="overflow-hidden rounded-xl border border-zinc-800">
          {/* Day-of-week headers */}
          <div className="grid grid-cols-7 border-b border-zinc-800 bg-zinc-900/50">
            {WEEKDAYS.map((d) => (
              <div key={d} className="py-2 text-center text-xs font-medium text-zinc-500">{d}</div>
            ))}
          </div>

          {/* Weeks */}
          {weeks.map((week, wi) => (
            <div key={wi} className="grid grid-cols-7 divide-x divide-zinc-800 border-b border-zinc-800 last:border-b-0">
              {week.map((day, di) => {
                const evs = day ? (dayEvents[day] ?? []) : []
                const isSelected = day === selectedDay
                const hasEvents = evs.length > 0
                const dots = evs.slice(0, 4)

                return (
                  <div
                    key={di}
                    onClick={() => {
                      if (!day) return
                      setSelectedDay(day === selectedDay ? null : day)
                    }}
                    className={`min-h-[88px] p-1.5 transition-colors ${
                      !day ? 'bg-zinc-950/30' :
                      isSelected ? 'bg-zinc-800/80 cursor-pointer' :
                      hasEvents ? 'bg-zinc-950 hover:bg-zinc-900/70 cursor-pointer' :
                      'bg-zinc-950 hover:bg-zinc-900/30 cursor-default'
                    }`}
                  >
                    {day && (
                      <>
                        {/* Day number */}
                        <div className="mb-1.5 flex items-start justify-between">
                          <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-medium ${
                            isToday(day)
                              ? 'bg-violet-600 text-white'
                              : isSelected
                              ? 'bg-zinc-600 text-white'
                              : 'text-zinc-500'
                          }`}>
                            {day}
                          </span>
                          {evs.length > 0 && (
                            <span className="text-[10px] tabular-nums text-zinc-600">{evs.length}</span>
                          )}
                        </div>

                        {/* Event pills — show up to 2, then "+N more" */}
                        <div className="space-y-0.5">
                          {evs.slice(0, 2).map((ev) => {
                            const cfg = KIND_CONFIG[ev.kind]
                            const Icon = cfg.icon
                            return (
                              <div key={ev.id}
                                className={`flex items-center gap-1 truncate rounded px-1 py-0.5 text-[10px] font-medium ${cfg.pill}`}>
                                <Icon className="h-2.5 w-2.5 shrink-0" />
                                <span className="truncate">{ev.label}</span>
                              </div>
                            )
                          })}
                          {evs.length > 2 && (
                            <div className="flex items-center gap-1.5 px-1">
                              {dots.slice(2).map((ev) => (
                                <span key={ev.id} className={`h-1.5 w-1.5 rounded-full ${KIND_CONFIG[ev.kind].dot}`} />
                              ))}
                              {evs.length > 4 && (
                                <span className="text-[10px] text-zinc-600">+{evs.length - 2}</span>
                              )}
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                )
              })}
            </div>
          ))}
        </div>

        {/* Day detail sidebar */}
        {selectedDay && selectedEvents.length > 0 && (
          <div className="lg:sticky lg:top-4 lg:self-start">
            <DayDetail
              day={selectedDay}
              month={month}
              year={year}
              events={selectedEvents}
              onClose={() => setSelectedDay(null)}
            />
          </div>
        )}
      </div>

      {/* No events state */}
      {allMonthEvents.length === 0 && (
        <p className="text-center text-sm text-zinc-600">
          No events recorded for {MONTH_NAMES[month - 1]} {year}.
          <span className="block mt-0.5 text-xs">Try navigating to a month with incidents or member deaths.</span>
        </p>
      )}
    </div>
  )
}
