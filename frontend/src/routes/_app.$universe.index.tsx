import { createFileRoute, Link } from '@tanstack/react-router'
import {
  AlertTriangle, CheckCircle2, ChevronRight, FileText,
  Network, Plus, Search, Shield, User, Users, type LucideIcon,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { NoUniverse } from '@/components/NoUniverse'
import { RECENT_ICON, RECENT_ROUTE, type RecentDetailRoute } from '@/lib/recentRoutes'
import { INCIDENT_TYPE_ICON, INCIDENT_TYPE_LABEL, INCIDENT_TYPE_TEXT, INCIDENT_TYPE_TILE } from '@/lib/incidentColors'
import { MemberFormSheet } from '@/components/members/MemberFormSheet'
import { IncidentFormSheet } from './_app.$universe.incidents.index'
import { SetFormSheet } from './_app.$universe.sets.index'
import { SourceFormSheet } from './_app.$universe.sources.index'
import {
  useAllMembers, useAllSets, useDatedIncidents, useIncidents, useUniverseAnalytics,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useUniverseRecents } from '@/stores/recents'
import { useCommandPalette } from '@/stores/commandPalette'
import {
  MEMBER_STATUS_DESCRIPTION, MEMBER_STATUS_HEX, MEMBER_STATUS_ORDER,
  RELIABILITY_DESCRIPTION, RELIABILITY_HEX,
} from '@/lib/statusColors'
import { BRAND_INACTIVE } from '@/lib/brand'
import type { IncidentListItem, IncidentType, MemberStatus, SourceReliability } from '@/lib/types'

export const Route = createFileRoute('/_app/$universe/')({
  component: Dashboard,
})

/* ────────────────────────────────────────────────────────────────────────────
   The dashboard is a launch pad first and a report second.

   What people come here to do, in order: find something (search), go back to
   what they were just reading (recents), write something down (quick create),
   and see what changed (the feed). The previous version answered none of those
   above the fold: it opened on five counters, and its "Recent incidents" feed
   printed MURDER / SHOOTING and a date per row, dropping the victim, shooter and
   place that the list endpoint already returns. Six rows read identically.

   Counts and charts stay, below the work. One accent (violet); the categorical
   palettes (member status, incident type, reliability) keep their colours
   because they carry meaning, and nothing else spends colour on decoration.
   ──────────────────────────────────────────────────────────────────────── */

const FEED_SIZE = 8
const WEEK_CAP = 8
const RESERVED_SET_NAMES = new Set(['Unknown', 'Civilian', 'Police'])

// ─── Primitives ───────────────────────────────────────────────────────────────

const ROW_LINK =
  'group rounded-md transition-colors hover:bg-zinc-800/60 active:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500'

/** The panel header IS the navigation: no separate "View all" link. */
function Panel({
  title, hint, to, children, className,
}: {
  title: string
  hint?: string
  to?: string
  children: React.ReactNode
  className?: string
}) {
  const heading = (
    <>
      <h2 className="text-xs font-semibold text-zinc-200">{title}</h2>
      {hint && <span className="truncate text-[11px] text-zinc-400">{hint}</span>}
    </>
  )
  return (
    <section className={`min-w-0 rounded-lg border border-zinc-800 bg-zinc-900/30 ${className ?? ''}`}>
      <div className="border-b border-zinc-800">
        {to ? (
          <Link
            from="/$universe"
            to={to}
            className="group flex items-baseline gap-2 px-3 py-2 transition-colors hover:bg-zinc-800/40 active:bg-zinc-800/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500"
          >
            {heading}
            <ChevronRight className="ml-auto h-3.5 w-3.5 shrink-0 self-center text-zinc-500 transition-colors group-hover:text-violet-400" />
          </Link>
        ) : (
          <div className="flex items-baseline gap-2 px-3 py-2">{heading}</div>
        )}
      </div>
      <div className="p-2">{children}</div>
    </section>
  )
}

/**
 * Row-shaped placeholder at the real row's height. The shared ListItemSkeleton
 * is a bordered card half again as tall, so the panels jumped when data landed.
 */
function RowSkeleton({ tile = true }: { tile?: boolean }) {
  return (
    <div className="flex items-center gap-3 px-2 py-2">
      {tile && <Skeleton className="h-8 w-8 shrink-0 rounded-md" />}
      <div className="min-w-0 flex-1 space-y-1.5">
        <Skeleton className="h-3.5 w-2/5" />
        <Skeleton className="h-3 w-3/5" />
      </div>
      <Skeleton className="h-3 w-14 shrink-0" />
    </div>
  )
}

/** Compact in-panel empty. `EmptyState` is py-16 and belongs on full list pages. */
function PanelEmpty({ children }: { children: React.ReactNode }) {
  return <p className="px-2 py-3 text-center text-xs text-zinc-400">{children}</p>
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="rounded border border-zinc-700 bg-zinc-800/80 px-1.5 py-0.5 font-mono text-[10px] leading-none text-zinc-400">
      {children}
    </kbd>
  )
}

// ─── Search launcher ──────────────────────────────────────────────────────────

/**
 * Looks like a field, opens the command palette. The palette already searches
 * every entity type at once and remembers recents; a second search on this page
 * would be a weaker copy of it. The placeholder names the real counts, so the
 * field says what it can find.
 */
function SearchLauncher({ placeholder }: { placeholder: string }) {
  const open = useCommandPalette((s) => s.setOpen)
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
  return (
    <button
      type="button"
      onClick={() => open(true)}
      className="group flex h-11 w-full min-w-0 items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3.5 text-left shadow-sm shadow-black/20 transition-colors hover:border-zinc-700 hover:bg-zinc-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
    >
      <Search className="h-4 w-4 shrink-0 text-zinc-500 transition-colors group-hover:text-violet-400" />
      <span className="min-w-0 flex-1 truncate text-sm text-zinc-400">{placeholder}</span>
      <span className="hidden shrink-0 items-center gap-1 sm:flex">
        <Kbd>/</Kbd>
        <span className="text-[10px] text-zinc-500">or</span>
        <Kbd>{isMac ? '⌘' : 'Ctrl'} K</Kbd>
      </span>
    </button>
  )
}

// ─── Quick create ─────────────────────────────────────────────────────────────

type CreateKind = 'incident' | 'member' | 'set' | 'source'

const CREATE_ACTIONS: { kind: CreateKind; label: string; icon: LucideIcon }[] = [
  { kind: 'incident', label: 'Incident', icon: AlertTriangle },
  { kind: 'member', label: 'Member', icon: User },
  { kind: 'set', label: 'Set', icon: Shield },
  { kind: 'source', label: 'Source', icon: FileText },
]

/**
 * Opens the real create sheets in place. The old "Record incident" button was a
 * link to the incidents list, one more click away from the form it named.
 */
function QuickCreate({ universeId }: { universeId: string }) {
  const [creating, setCreating] = useState<CreateKind | null>(null)
  const close = () => setCreating(null)
  return (
    <>
      <div className="grid shrink-0 grid-cols-4 gap-1.5 sm:flex" role="group" aria-label="Create new">
        {CREATE_ACTIONS.map(({ kind, label, icon: Icon }, i) => (
          <button
            key={kind}
            type="button"
            onClick={() => setCreating(kind)}
            className={`inline-flex h-11 min-w-0 items-center justify-center gap-1 rounded-md px-2 text-xs sm:gap-1.5 sm:px-3 font-medium transition-[color,background-color,transform] duration-150 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 ${
              i === 0
                ? 'bg-violet-600 text-white hover:bg-violet-500 active:bg-violet-700'
                : 'border border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-800 hover:text-white'
            }`}
            aria-label={`New ${label.toLowerCase()}`}
          >
            {i === 0 ? <Plus className="h-3.5 w-3.5 shrink-0" /> : <Icon className="hidden h-3.5 w-3.5 shrink-0 sm:block" />}
            <span className="truncate">{label}</span>
          </button>
        ))}
      </div>
      <IncidentFormSheet universeId={universeId} open={creating === 'incident'} onClose={close} />
      <MemberFormSheet universeId={universeId} open={creating === 'member'} onClose={close} />
      <SetFormSheet universeId={universeId} open={creating === 'set'} onClose={close} />
      <SourceFormSheet universeId={universeId} open={creating === 'source'} onClose={close} />
    </>
  )
}

// ─── Metrics ──────────────────────────────────────────────────────────────────

function Metric({
  icon: Icon, label, value, to, loading,
}: {
  icon: LucideIcon
  label: string
  value: number | undefined
  to: string
  loading: boolean
}) {
  return (
    <Link
      from="/$universe"
      to={to}
      className="group flex min-w-0 flex-col gap-1 px-2 py-2 transition-colors hover:bg-zinc-900 active:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500 sm:px-3"
    >
      <span className="flex min-w-0 items-center gap-1.5 text-[10px] text-zinc-400 sm:text-[11px]">
        <Icon className="hidden h-3 w-3 shrink-0 transition-colors group-hover:text-violet-400 sm:block" />
        <span className="truncate">{label}</span>
      </span>
      {loading
        ? <Skeleton className="h-5 w-10" />
        : <span className="text-lg font-semibold leading-none tabular-nums text-white md:text-xl">{value?.toLocaleString() ?? '-'}</span>}
    </Link>
  )
}

// ─── Jump back in ─────────────────────────────────────────────────────────────

function JumpBackIn() {
  const entries = useUniverseRecents()
  if (entries.length === 0) return null
  return (
    <section aria-labelledby="recents-heading" className="min-w-0">
      <h2 id="recents-heading" className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
        Jump back in
      </h2>
      {/* One scrolling row rather than a wrapping cloud: eight chips never push
          the feed down, and on a phone the row swipes. */}
      <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {entries.map((r) => {
          const Icon = RECENT_ICON[r.type]
          return (
            <Link
              key={`${r.type}-${r.id}`}
              to={`${RECENT_ROUTE[r.type]}/$id` as RecentDetailRoute}
              params={{ universe: r.universe, id: r.slug ?? r.id }}
              className="group inline-flex max-w-[14rem] shrink-0 items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900/60 py-1 pl-2 pr-3 text-xs text-zinc-300 transition-colors hover:border-violet-500/40 hover:bg-zinc-800 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
            >
              <Icon className="h-3 w-3 shrink-0 text-zinc-500 transition-colors group-hover:text-violet-400" />
              <span className="truncate">{r.label}</span>
            </Link>
          )
        })}
      </div>
    </section>
  )
}

// ─── Incident feed ────────────────────────────────────────────────────────────

function joinNames(names: string[], max = 2): string {
  if (names.length <= max) return names.join(', ')
  return `${names.slice(0, max).join(', ')} +${names.length - max}`
}

function IncidentRow({ inc }: { inc: IncidentListItem }) {
  const type = inc.type as IncidentType
  const Icon = INCIDENT_TYPE_ICON[type] ?? AlertTriangle
  const label = INCIDENT_TYPE_LABEL[type] ?? inc.type
  const victims = inc.victim_names ?? []
  const shooters = inc.shooter_names ?? []
  const headline = victims.length > 0 ? joinNames(victims) : (inc.location_text || label)
  // A location headline usually ends in the city already.
  const place = headline === inc.location_text ? null : inc.municipality_name
  const detail = [
    label,
    shooters.length > 0 ? `by ${joinNames(shooters)}` : null,
    place,
  ].filter(Boolean).join(' · ')

  return (
    <Link
      from="/$universe" to="/$universe/incidents/$id"
      params={{ id: inc.id }}
      className={`${ROW_LINK} grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 px-2 py-2`}
    >
      <span className={`flex h-8 w-8 items-center justify-center rounded-md ${INCIDENT_TYPE_TILE[type] ?? 'bg-zinc-800 text-zinc-400'}`}>
        <Icon className="h-4 w-4" />
      </span>
      <span className="min-w-0">
        <span className="flex items-center gap-1.5">
          <span className="truncate text-sm font-medium text-zinc-200 transition-colors group-hover:text-white">{headline}</span>
          {inc.verified && (
            <Tooltip>
              <TooltipTrigger asChild>
                <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" aria-label="Verified" />
              </TooltipTrigger>
              <TooltipContent side="top">Verified incident</TooltipContent>
            </Tooltip>
          )}
        </span>
        <span className="block truncate text-xs text-zinc-400">{detail}</span>
      </span>
      <span className="shrink-0 text-right text-xs tabular-nums text-zinc-400">
        {inc.date ? <FuzzyDate value={inc.date} /> : 'Undated'}
      </span>
    </Link>
  )
}

// ─── This week in history ─────────────────────────────────────────────────────

interface HistoryEvent {
  key: string
  offset: number
  yearsAgo: number
  kind: 'incident' | 'death'
  label: string
  detail: string
  to: string
  params: Record<string, string>
  type?: IncidentType
}

function dayLabel(offset: number, d: Date): string {
  if (offset === 0) return 'Today'
  if (offset === 1) return 'Tomorrow'
  return d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })
}

/**
 * Anniversaries in the next seven days: incidents, and deaths recorded on a
 * member without an incident behind them. A day-precision date is required, so
 * nothing lands on a day it was not known to happen.
 *
 * "This week" rather than "On this day": with a few hundred dated events a
 * single calendar day is usually empty, and an empty panel on every visit
 * teaches people to stop looking at it.
 */
function useWeekInHistory(universeId: string | null) {
  const { data: incidents, isLoading: incLoading } = useDatedIncidents(universeId)
  const { data: members, isLoading: memLoading } = useAllMembers(universeId)

  const events = useMemo(() => {
    const now = new Date()
    const thisYear = now.getFullYear()
    const days = Array.from({ length: 7 }, (_, offset) => {
      const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + offset)
      return { offset, month: d.getMonth() + 1, day: d.getDate() }
    })
    const offsetOf = (month?: number | null, day?: number | null) =>
      days.find((d) => d.month === month && d.day === day)?.offset

    const out: HistoryEvent[] = []
    const victimKeys = new Set<string>()

    for (const inc of incidents?.items ?? []) {
      const dt = inc.date
      if (!dt || dt.precision !== 'YMD' || !dt.year) continue
      const offset = offsetOf(dt.month, dt.day)
      if (offset === undefined) continue
      const yearsAgo = thisYear - dt.year
      if (yearsAgo < 1 && offset > 0) continue
      const victims = inc.victim_names ?? []
      for (const v of victims) victimKeys.add(`${v}|${dt.year}-${dt.month}-${dt.day}`)
      const label = INCIDENT_TYPE_LABEL[inc.type as IncidentType] ?? inc.type
      out.push({
        key: `i-${inc.id}`,
        offset,
        yearsAgo,
        kind: 'incident',
        label: victims.length > 0 ? joinNames(victims) : label,
        detail: [label, inc.municipality_name].filter(Boolean).join(' · '),
        to: '/$universe/incidents/$id',
        params: { id: inc.id },
        type: inc.type as IncidentType,
      })
    }

    for (const m of members?.items ?? []) {
      const dt = m.date_of_death
      if (m.status !== 'DEAD' || !dt || dt.precision !== 'YMD' || !dt.year) continue
      const offset = offsetOf(dt.month, dt.day)
      if (offset === undefined) continue
      // The incident row already names this victim on this date.
      if (victimKeys.has(`${m.display_name}|${dt.year}-${dt.month}-${dt.day}`)) continue
      const yearsAgo = thisYear - dt.year
      if (yearsAgo < 1 && offset > 0) continue
      out.push({
        key: `d-${m.id}`,
        offset,
        yearsAgo,
        kind: 'death',
        label: m.display_name,
        detail: ['Died', m.primary_set_name].filter(Boolean).join(' · '),
        to: '/$universe/members/$id',
        params: { id: m.slug ?? m.id },
      })
    }

    return out.sort((a, b) => a.offset - b.offset || b.yearsAgo - a.yearsAgo)
  }, [incidents, members])

  return { events, loading: incLoading || memLoading }
}

function WeekInHistory({ universeId }: { universeId: string }) {
  const { events, loading } = useWeekInHistory(universeId)
  const shown = events.slice(0, WEEK_CAP)
  const now = new Date()

  return (
    <Panel
      title="This week in history"
      hint={events.length > WEEK_CAP ? `${events.length} anniversaries` : undefined}
      to="/$universe/calendar"
    >
      {loading ? (
        <div className="space-y-0.5">
          {Array.from({ length: 3 }).map((_, i) => <RowSkeleton key={i} tile={false} />)}
        </div>
      ) : shown.length === 0 ? (
        <PanelEmpty>No dated anniversaries in the next seven days.</PanelEmpty>
      ) : (
        <ol className="space-y-0.5">
          {shown.map((ev) => {
            const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + ev.offset)
            return (
              <li key={ev.key}>
                <Link
                  from="/$universe"
                  to={ev.to}
                  params={ev.params}
                  className={`${ROW_LINK} grid grid-cols-[3.75rem_minmax(0,1fr)_auto] items-center gap-2 px-2 py-1.5`}
                >
                  <span className={`text-[11px] font-medium ${ev.offset === 0 ? 'text-violet-400' : 'text-zinc-500'}`}>
                    {dayLabel(ev.offset, d)}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm text-zinc-200 transition-colors group-hover:text-white">{ev.label}</span>
                    <span className={`block truncate text-[11px] ${ev.type ? INCIDENT_TYPE_TEXT[ev.type] : 'text-zinc-400'}`}>{ev.detail}</span>
                  </span>
                  <span className="shrink-0 text-[11px] tabular-nums text-zinc-400">
                    {ev.yearsAgo < 1 ? 'this year' : `${ev.yearsAgo}y ago`}
                  </span>
                </Link>
              </li>
            )
          })}
        </ol>
      )}
    </Panel>
  )
}

// ─── Proportion bar (roster, sources) ─────────────────────────────────────────

interface Slice { key: string; label: string; count: number; color: string; description?: string }

/** With `memberLinks`, each legend entry opens the members list filtered to that status. */
function ProportionBar({ slices, loading, memberLinks = false }: { slices: Slice[]; loading: boolean; memberLinks?: boolean }) {
  const total = slices.reduce((s, x) => s + x.count, 0)
  if (loading) {
    return (
      <div className="space-y-2 p-1">
        <Skeleton className="h-2.5 w-full rounded-full" />
        <div className="flex gap-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-3 w-14" />)}
        </div>
      </div>
    )
  }
  if (total === 0) return <PanelEmpty>Nothing recorded yet.</PanelEmpty>
  return (
    <div className="p-1">
      <div className="mb-2.5 flex h-2.5 w-full gap-px overflow-hidden rounded-full bg-zinc-800">
        {slices.filter((s) => s.count > 0).map((s) => {
          const pct = (s.count / total) * 100
          return (
            <Tooltip key={s.key}>
              <TooltipTrigger asChild>
                <div className="transition-[filter] hover:brightness-125" style={{ width: `${pct}%`, backgroundColor: s.color }} />
              </TooltipTrigger>
              <TooltipContent side="top">
                <div className="flex flex-col gap-0.5">
                  <span className="font-semibold">{s.label}: {s.count} ({pct.toFixed(1)}%)</span>
                  {s.description && <span className="text-zinc-300">{s.description}</span>}
                </div>
              </TooltipContent>
            </Tooltip>
          )
        })}
      </div>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        {slices.filter((s) => s.count > 0).map((s) => (
          <li key={s.key} className="min-w-0">
            {memberLinks ? (
              <Link
                from="/$universe" to="/$universe/members"
                search={{ status: s.key as MemberStatus }}
                className="-mx-1 flex min-w-0 items-center gap-1.5 rounded px-1 py-0.5 transition-colors hover:bg-zinc-800/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
              >
                <LegendEntry slice={s} />
              </Link>
            ) : (
              <span className="flex min-w-0 items-center gap-1.5 py-0.5"><LegendEntry slice={s} /></span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

function LegendEntry({ slice }: { slice: Slice }) {
  return (
    <>
      <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: slice.color }} />
      <span className="truncate text-zinc-400">{slice.label}</span>
      <span className="ml-auto font-medium tabular-nums text-zinc-200">{slice.count}</span>
    </>
  )
}

const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

// ─── Incidents by year ────────────────────────────────────────────────────────

/**
 * Yearly bars on a continuous axis. The chart this replaces plotted months as
 * categories, so only months that had an incident got a slot: 2006 and 2021
 * sat next to each other, a decade of silence vanished, and the tick labels
 * were bare "06 09 12" month numbers with no year. At a few dozen incidents a
 * year, monthly resolution is noise anyway.
 */
function IncidentsByYear({ months, total }: { months: { month: string; count: number }[]; total: number }) {
  const byYear = new Map<number, number>()
  for (const { month, count } of months) {
    const y = Number(month.slice(0, 4))
    if (Number.isFinite(y)) byYear.set(y, (byYear.get(y) ?? 0) + count)
  }
  if (byYear.size === 0) return <PanelEmpty>No dated incidents yet.</PanelEmpty>

  const years = [...byYear.keys()]
  const first = Math.min(...years)
  const last = Math.max(...years)
  const series = Array.from({ length: last - first + 1 }, (_, i) => ({ year: first + i, count: byYear.get(first + i) ?? 0 }))
  const max = Math.max(...series.map((s) => s.count))
  const dated = series.reduce((s, x) => s + x.count, 0)
  const undated = Math.max(0, total - dated)
  const labelEvery = Math.max(1, Math.ceil(series.length / 8))

  return (
    <div className="p-1">
      <div className="flex h-32 items-end gap-px" role="img" aria-label={`Incidents per year, ${first} to ${last}`}>
        {series.map((s) => (
          <Tooltip key={s.year}>
            <TooltipTrigger asChild>
              <div className="group flex h-full min-w-0 flex-1 items-end">
                <div
                  className={`w-full rounded-t-sm transition-colors ${s.count > 0 ? 'bg-violet-500/70 group-hover:bg-violet-400' : 'bg-zinc-800/60'}`}
                  style={{ height: s.count > 0 ? `${Math.max(4, (s.count / max) * 100)}%` : '2px' }}
                />
              </div>
            </TooltipTrigger>
            <TooltipContent side="top">{s.year}: {s.count} incident{s.count === 1 ? '' : 's'}</TooltipContent>
          </Tooltip>
        ))}
      </div>
      <div className="mt-1.5 flex gap-px">
        {series.map((s, i) => (
          <span key={s.year} className="min-w-0 flex-1 text-center text-[10px] tabular-nums text-zinc-500">
            {i % labelEvery === 0 || i === series.length - 1 ? `'${String(s.year).slice(2)}` : ''}
          </span>
        ))}
      </div>
      {undated > 0 && (
        <p className="mt-2 text-[11px] text-zinc-500">{undated} undated incident{undated === 1 ? '' : 's'} not shown.</p>
      )}
    </div>
  )
}

// ─── Leaderboard ──────────────────────────────────────────────────────────────

function LeaderColumn({
  heading, loading, empty, children,
}: {
  heading: string
  loading: boolean
  empty: boolean
  children: React.ReactNode
}) {
  return (
    <div className="min-w-0 p-2">
      <h3 className="px-2 pb-1 text-[10px] font-medium uppercase tracking-wider text-zinc-400">{heading}</h3>
      {loading ? (
        <div className="space-y-0.5">
          {Array.from({ length: 5 }).map((_, i) => <RowSkeleton key={i} tile={false} />)}
        </div>
      ) : empty ? (
        <PanelEmpty>Nothing ranked yet.</PanelEmpty>
      ) : (
        <ol className="space-y-0.5">{children}</ol>
      )}
    </div>
  )
}

function LeaderRow({
  to, params, rank, label, count, countLabel,
}: {
  to: string
  params: Record<string, string>
  rank: number
  label: string
  count: number
  countLabel: string
}) {
  return (
    <li>
      <Link from="/$universe" to={to} params={params} className={`${ROW_LINK} flex items-center gap-2.5 px-2 py-1.5`}>
        <span className="w-3 shrink-0 text-right font-mono text-[11px] text-zinc-500">{rank}</span>
        <span className="min-w-0 flex-1 truncate text-sm text-zinc-300 transition-colors group-hover:text-white">{label}</span>
        <span className="shrink-0 rounded-full bg-zinc-800 px-2 py-0.5 text-[11px] font-medium tabular-nums text-zinc-300">
          {count} <span className="text-zinc-500">{countLabel}</span>
        </span>
      </Link>
    </li>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

function Dashboard() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const { data: analytics, isLoading: analyticsLoading } = useUniverseAnalytics(universeId)
  const { data: incidentData, isLoading: incidentsLoading } = useIncidents(universeId)
  const { data: setsData } = useAllSets(universeId)

  if (!universe) return <NoUniverse />

  const recentIncidents = (incidentData?.items ?? []).slice(0, FEED_SIZE)
  const setSlug: Record<string, string | null> = {}
  const reservedSetIds = new Set<string>()
  for (const s of setsData?.items ?? []) {
    setSlug[s.id] = s.slug
    if (s.is_reserved) reservedSetIds.add(s.id)
  }

  const statusSlices: Slice[] = MEMBER_STATUS_ORDER.map((status: MemberStatus) => ({
    key: status,
    label: titleCase(status),
    count: analytics?.member_by_status?.[status] ?? 0,
    color: MEMBER_STATUS_HEX[status] ?? BRAND_INACTIVE,
    description: MEMBER_STATUS_DESCRIPTION[status],
  }))
  const reliabilitySlices: Slice[] = (['HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED'] as SourceReliability[]).map((r) => ({
    key: r,
    label: titleCase(r),
    count: analytics?.source_by_reliability?.[r] ?? 0,
    color: RELIABILITY_HEX[r],
    description: RELIABILITY_DESCRIPTION[r],
  }))

  // The reserved sets (Unknown, Civilian, Police) are holding pens, not crews:
  // "Unknown" ranking second-most-active says nothing about who is active. The
  // backend now leaves them out; this guards an API that has not restarted yet.
  const topSets = (analytics?.top_sets_by_incidents ?? [])
    .filter((s) => !reservedSetIds.has(s.id) && !RESERVED_SET_NAMES.has(s.name))
    .slice(0, 5)
  const topMembers = analytics?.top_members_by_incidents ?? []
  const topSources = analytics?.top_sources_by_references ?? []

  const n = (v: number | undefined) => (v ?? 0).toLocaleString()
  const searchPlaceholder = analytics
    ? `Search ${n(analytics.total_members)} members, ${n(analytics.total_sets)} sets, ${n(analytics.total_sources)} sources…`
    : 'Search members, sets, incidents, sources…'

  return (
    <TooltipProvider delayDuration={150}>
      <div className="mx-auto max-w-6xl space-y-4">

        {/* ── Header: identity, search, create ─────────────────────────────── */}
        <header className="space-y-3">
          <div className="flex min-w-0 items-baseline gap-2">
            <h1 className="truncate text-xl font-bold tracking-tight text-white sm:text-2xl">{universe.name}</h1>
            <span className="shrink-0 font-mono text-[11px] text-zinc-500">/{universe.slug}</span>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="min-w-0 flex-1"><SearchLauncher placeholder={searchPlaceholder} /></div>
            <QuickCreate universeId={universe.id} />
          </div>
        </header>

        <JumpBackIn />

        {/* ── Metrics ─────────────────────────────────────────────────────────
            Five across at every width. They used to take a whole phone screen
            as a 2-2-1 stack of large tiles; they are a glance, not a destination. */}
        <nav aria-label="Universe totals" className="grid grid-cols-[repeat(5,minmax(0,1fr))] divide-x divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
          <Metric icon={Shield} label="Sets" value={analytics?.total_sets} to="/$universe/sets" loading={analyticsLoading} />
          <Metric icon={Network} label="Alliances" value={analytics?.total_alliances} to="/$universe/alliances" loading={analyticsLoading} />
          <Metric icon={Users} label="Members" value={analytics?.total_members} to="/$universe/members" loading={analyticsLoading} />
          <Metric icon={AlertTriangle} label="Incidents" value={analytics?.total_incidents} to="/$universe/incidents" loading={analyticsLoading} />
          <Metric icon={FileText} label="Sources" value={analytics?.total_sources} to="/$universe/sources" loading={analyticsLoading} />
        </nav>

        {/* ── Feed + history ──────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
          <Panel title="Latest incidents" hint="most recently recorded" to="/$universe/incidents">
            {incidentsLoading ? (
              <div className="space-y-0.5">
                {Array.from({ length: 6 }).map((_, i) => <RowSkeleton key={i} />)}
              </div>
            ) : recentIncidents.length === 0 ? (
              <PanelEmpty>Nothing recorded yet. Use “Incident” above to add the first one.</PanelEmpty>
            ) : (
              <div className="space-y-0.5">
                {recentIncidents.map((inc) => <IncidentRow key={inc.id} inc={inc} />)}
              </div>
            )}
          </Panel>

          <div className="grid min-w-0 gap-4">
            <WeekInHistory universeId={universe.id} />
            <Panel
              title="Roster"
              hint={analytics ? `${n(analytics.total_members)} members by status` : undefined}
              to="/$universe/members"
            >
              <ProportionBar slices={statusSlices} loading={analyticsLoading} memberLinks />
            </Panel>
          </div>
        </div>

        {/* ── Leaderboards ───────────────────────────────────────────────────
            Three ranked lists share one panel and one header. */}
        <section className="rounded-lg border border-zinc-800 bg-zinc-900/30">
          <div className="flex items-baseline gap-2 border-b border-zinc-800 px-3 py-2">
            <h2 className="text-xs font-semibold text-zinc-200">Most active</h2>
            <span className="text-[11px] text-zinc-400">by recorded involvement</span>
          </div>
          <div className="grid grid-cols-1 divide-y divide-zinc-800 md:grid-cols-[repeat(3,minmax(0,1fr))] md:divide-x md:divide-y-0">
            <LeaderColumn heading="Sets" loading={analyticsLoading} empty={topSets.length === 0}>
              {topSets.map((s, i) => (
                <LeaderRow
                  key={s.id} to="/$universe/sets/$id" params={{ id: setSlug[s.id] ?? s.id }}
                  rank={i + 1} label={s.name} count={s.incident_count} countLabel="inc."
                />
              ))}
            </LeaderColumn>
            <LeaderColumn heading="Members" loading={analyticsLoading} empty={topMembers.length === 0}>
              {topMembers.map((m, i) => (
                <LeaderRow
                  key={m.id} to="/$universe/members/$id" params={{ id: m.slug ?? m.id }}
                  rank={i + 1} label={m.display_name} count={m.incident_count} countLabel="inc."
                />
              ))}
            </LeaderColumn>
            <LeaderColumn heading="Sources" loading={analyticsLoading} empty={topSources.length === 0}>
              {topSources.map((src, i) => (
                <LeaderRow
                  key={src.id} to="/$universe/sources/$id" params={{ id: src.id }}
                  rank={i + 1} label={src.title} count={src.ref_count} countLabel="refs"
                />
              ))}
            </LeaderColumn>
          </div>
        </section>

        {/* ── Trends ─────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
          <Panel title="Incidents by year" to="/$universe/timeline">
            {analyticsLoading
              ? <Skeleton className="m-1 h-32" />
              : <IncidentsByYear months={analytics?.incidents_by_month ?? []} total={analytics?.total_incidents ?? 0} />}
          </Panel>
          <Panel
            title="Source reliability"
            hint={analytics ? `${n(analytics.total_sources)} sources` : undefined}
            to="/$universe/sources"
          >
            <ProportionBar slices={reliabilitySlices} loading={analyticsLoading} />
          </Panel>
        </div>

        <p className="hidden items-center justify-center gap-1.5 pb-2 text-[11px] text-zinc-500 lg:flex">
          <Kbd>?</Kbd> keyboard shortcuts
          <span aria-hidden>·</span>
          <Kbd>/</Kbd> search
        </p>
      </div>
    </TooltipProvider>
  )
}
