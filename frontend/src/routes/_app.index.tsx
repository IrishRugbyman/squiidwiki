import { createFileRoute, Link } from '@tanstack/react-router'
import {
  AlertTriangle, CheckCircle2, ChevronRight, FileText,
  Network, Shield, Skull, User, Users,
} from 'lucide-react'
import { lazy, Suspense } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { ListItemSkeleton } from '@/components/skeletons'

const IncidentsOverTime = lazy(() =>
  import('@/components/charts/IncidentsOverTime').then((m) => ({ default: m.IncidentsOverTime })),
)
const ReliabilityDonut = lazy(() =>
  import('@/components/charts/ReliabilityDonut').then((m) => ({ default: m.ReliabilityDonut })),
)
import { useIncidents, useSets, useUniverseAnalytics } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { NoUniverse } from '@/components/NoUniverse'
import { MEMBER_STATUS_HEX, MEMBER_STATUS_CHIP, MEMBER_STATUS_ORDER, MEMBER_STATUS_DESCRIPTION } from '@/lib/statusColors'
import { BRAND_INACTIVE } from '@/lib/brand'
import type { MemberStatus } from '@/lib/types'

export const Route = createFileRoute('/_app/')({
  component: Dashboard,
})

/* ────────────────────────────────────────────────────────────────────────────
   The dashboard is composed of six deliberately DISTINCT layout families:
   metric strip, distribution band, incident feed, chip cloud, three-column
   leaderboard, chart pair. The previous version was seven identical bordered
   cards in a symmetric two-column grid, so every block read with the same
   weight and the eye had nowhere to land first.

   One accent throughout (violet, which is now the brand ramp). The old version
   tinted each of the five stat tiles a different hue (violet/blue/emerald/
   amber/sky), implying a categorical distinction that does not exist — the
   five counts are all the same kind of thing. Member status colours below ARE
   categorical and keep their palette. Spending colour there only works if it
   is not also spent on decoration.
   ──────────────────────────────────────────────────────────────────────── */

// ─── Metric strip ─────────────────────────────────────────────────────────────

function Stat({
  icon: Icon, label, value, to, loading, className,
}: {
  icon: typeof Shield
  label: string
  value: number | null | undefined
  to: string
  loading?: boolean
  className?: string
}) {
  return (
    <Link
      to={to}
      className={`group flex min-w-0 flex-col gap-1 px-3 py-2.5 transition-colors hover:bg-zinc-900 active:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500 ${className ?? ''}`}
    >
      <span className="flex items-center gap-1.5 text-[11px] text-zinc-400">
        <Icon className="h-3 w-3 shrink-0 transition-colors group-hover:text-violet-400" />
        <span className="truncate">{label}</span>
      </span>
      {loading
        ? <Skeleton className="h-6 w-10" />
        : <span className="text-2xl font-semibold leading-none tabular-nums text-white">{value ?? '—'}</span>}
    </Link>
  )
}

// ─── Panel ────────────────────────────────────────────────────────────────────

/**
 * The panel header IS the navigation.
 *
 * The previous dashboard carried a separate "View all →" / "All sets →" /
 * "All members →" / "All incidents →" / "All sources →" link in five panels:
 * five different labels for one intent, each a second clickable target for the
 * destination the title already names.
 */
function Panel({
  title, hint, to, children,
}: {
  title: string
  hint?: string
  to?: string
  children: React.ReactNode
}) {
  const heading = (
    <>
      <h2 className="text-xs font-semibold text-zinc-300">{title}</h2>
      {hint && <span className="text-[10px] text-zinc-400">{hint}</span>}
    </>
  )
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/30">
      <div className="border-b border-zinc-800">
        {to ? (
          <Link
            to={to}
            className="group flex items-baseline gap-2 px-3 py-1.5 transition-colors hover:bg-zinc-800/40 active:bg-zinc-800/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500"
          >
            {heading}
            <ChevronRight className="ml-auto h-3.5 w-3.5 self-center text-zinc-500 transition-colors group-hover:text-violet-400" />
          </Link>
        ) : (
          <div className="flex items-baseline gap-2 px-3 py-1.5">{heading}</div>
        )}
      </div>
      <div className="p-3">{children}</div>
    </section>
  )
}

/** Compact in-panel empty. `EmptyState` is py-16 and belongs on full list pages. */
function PanelEmpty({ children }: { children: React.ReactNode }) {
  return <p className="py-2 text-center text-xs text-zinc-400">{children}</p>
}

// ─── Leaderboard column ───────────────────────────────────────────────────────

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
        <div className="space-y-2.5 px-2">
          {Array.from({ length: 3 }).map((_, i) => <ListItemSkeleton key={i} />)}
        </div>
      ) : empty ? (
        <PanelEmpty>Nothing ranked yet.</PanelEmpty>
      ) : (
        <div className="space-y-0.5">{children}</div>
      )}
    </div>
  )
}

function LeaderRow({
  to, params, rank, icon: Icon, label, count, countLabel,
}: {
  to: string
  params: Record<string, string>
  rank: number
  icon: typeof User
  label: string
  count: number
  countLabel?: string
}) {
  return (
    <Link
      to={to}
      params={params}
      className="group flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-zinc-800/60 active:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500"
    >
      <span className="w-3 shrink-0 text-right font-mono text-[11px] text-zinc-500">{rank}</span>
      <Icon className="h-3 w-3 shrink-0 text-zinc-500 transition-colors group-hover:text-violet-400" />
      <span className="min-w-0 flex-1 truncate text-sm text-zinc-300 transition-colors group-hover:text-white">{label}</span>
      <span className="shrink-0 rounded-full bg-zinc-800 px-2 py-0.5 text-[11px] font-medium tabular-nums text-zinc-300">
        {count}{countLabel ? ` ${countLabel}` : ''}
      </span>
    </Link>
  )
}

function statusLabelColor(status: string): string {
  const memberStatus = status as MemberStatus
  return MEMBER_STATUS_CHIP[memberStatus]?.split(' ').find((c) => c.startsWith('text-')) ?? 'text-zinc-400'
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

function Dashboard() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data: analytics, isLoading: analyticsLoading } = useUniverseAnalytics(universe?.id ?? null)
  const { data: incidentData, isLoading: incidentsLoading } = useIncidents(universe?.id ?? null)
  const { data: setsData } = useSets(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  const recentIncidents = (incidentData?.items ?? []).slice(0, 6)
  const statusEntries = Object.entries(analytics?.member_by_status ?? {})
    .sort((a, b) => MEMBER_STATUS_ORDER.indexOf(a[0] as MemberStatus) - MEMBER_STATUS_ORDER.indexOf(b[0] as MemberStatus))
  const totalMembers = statusEntries.reduce((s, [, n]) => s + n, 0)
  const setMap: Record<string, string | null> = {}
  for (const s of setsData?.items ?? []) setMap[s.id] = s.slug

  const topSets = analytics?.top_sets_by_incidents ?? []
  const topMembers = analytics?.top_members_by_incidents ?? []
  const topSources = analytics?.top_sources_by_references ?? []
  const incidentTypes = Object.entries(analytics?.incident_by_type ?? {})
  const hasCharts = !!analytics
    && (analytics.incidents_by_month.length > 0 || Object.keys(analytics.source_by_reliability).length > 0)

  return (
    <TooltipProvider delayDuration={150}>
      <div className="space-y-3">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <Skull className="h-5 w-5 shrink-0 text-violet-500" />
            <h1 className="truncate text-lg font-bold leading-none text-white">{universe.name}</h1>
            <span className="shrink-0 font-mono text-[11px] leading-none text-zinc-400">/{universe.slug}</span>
          </div>
          <Link
            to="/incidents"
            className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-violet-600 px-3 py-1.5 text-xs font-medium text-white transition-[color,background-color,transform] duration-150 hover:bg-violet-500 active:scale-[0.98] active:bg-violet-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
          >
            <AlertTriangle className="h-3 w-3" />
            Record incident
          </Link>
        </div>

        {/* ── Metric strip ───────────────────────────────────────────────────
            One hairline-divided panel rather than five floating cards. The
            tracks are minmax(0,1fr), not `1fr`: bare 1fr resolves to
            minmax(auto,1fr), and a long label would then refuse to truncate
            and push the strip past the viewport.

            Two breakpoints, not three: five cells never divide evenly into
            three columns, so a `sm:grid-cols-3` step would leave an orphan
            empty cell in the second row. Below md the strip is 2-up with the
            fifth cell spanning the full width; at md and above it is a single
            row of five. Every cell is filled at every width. */}
        <div className="grid grid-cols-[repeat(2,minmax(0,1fr))] divide-x divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30 md:grid-cols-[repeat(5,minmax(0,1fr))] md:divide-y-0">
          <Stat icon={Shield} label="Sets" value={analytics?.total_sets} to="/sets" loading={analyticsLoading} />
          <Stat icon={Network} label="Alliances" value={analytics?.total_alliances} to="/alliances" loading={analyticsLoading} />
          <Stat icon={Users} label="Members" value={analytics?.total_members} to="/members" loading={analyticsLoading} />
          <Stat icon={AlertTriangle} label="Incidents" value={analytics?.total_incidents} to="/incidents" loading={analyticsLoading} />
          <Stat
            icon={FileText} label="Sources" value={analytics?.total_sources} to="/sources"
            loading={analyticsLoading} className="col-span-2 md:col-span-1"
          />
        </div>

        {/* ── Roster distribution ────────────────────────────────────────────
            Full width on purpose: a stacked bar is read by proportion, and
            proportion needs horizontal room. Boxed into a half-width card the
            small statuses collapsed to a couple of pixels. */}
        <Panel title="Roster by status" hint={totalMembers > 0 ? `${totalMembers} tracked` : undefined} to="/members">
          {analyticsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-2.5 w-full rounded-full" />
              <div className="flex gap-3">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-3 w-16" />)}
              </div>
            </div>
          ) : totalMembers === 0 ? (
            <PanelEmpty>No members recorded yet.</PanelEmpty>
          ) : (
            <>
              <div className="mb-3 flex h-2.5 w-full overflow-hidden rounded-full bg-zinc-800">
                {statusEntries.map(([status, count]) => {
                  const pct = (count / totalMembers) * 100
                  return (
                    <Tooltip key={status}>
                      <TooltipTrigger asChild>
                        <div
                          className="transition-[filter] hover:brightness-125"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: MEMBER_STATUS_HEX[status as MemberStatus] ?? BRAND_INACTIVE,
                          }}
                        />
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <div className="flex flex-col gap-0.5">
                          <span className="font-semibold">{status}: {count} ({pct.toFixed(1)}%)</span>
                          <span className="text-zinc-300">{MEMBER_STATUS_DESCRIPTION[status as MemberStatus]}</span>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  )
                })}
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                {statusEntries.map(([status, count]) => (
                  <Link
                    key={status}
                    to="/members"
                    className="flex items-center gap-1.5 rounded-md px-1 py-0.5 text-xs transition-opacity hover:opacity-80 active:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
                  >
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ backgroundColor: MEMBER_STATUS_HEX[status as MemberStatus] ?? BRAND_INACTIVE }}
                    />
                    <span className={statusLabelColor(status)}>{status}</span>
                    <span className="font-medium tabular-nums text-zinc-300">{count}</span>
                  </Link>
                ))}
              </div>
            </>
          )}
        </Panel>

        {/* ── Feed + chip cloud ──────────────────────────────────────────── */}
        {/* items-start, not the default stretch: the chip cloud is content-height
            and would otherwise be padded out to match the feed, leaving a large
            dead panel next to it. */}
        <div className="grid grid-cols-1 items-start gap-3 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <Panel title="Recent incidents" hint="latest 6" to="/incidents">
            {incidentsLoading ? (
              <div className="space-y-2.5">
                {Array.from({ length: 4 }).map((_, i) => <ListItemSkeleton key={i} />)}
              </div>
            ) : recentIncidents.length === 0 ? (
              <PanelEmpty>Nothing recorded yet. Open Incidents to add the first one.</PanelEmpty>
            ) : (
              <div className="space-y-0.5">
                {recentIncidents.map((inc) => (
                  <Link
                    key={inc.id}
                    to="/incidents/$id"
                    params={{ id: inc.id }}
                    className="group flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-zinc-800/60 active:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-violet-500"
                  >
                    <AlertTriangle className={`h-3.5 w-3.5 shrink-0 ${inc.verified ? 'text-amber-500' : 'text-zinc-500'}`} />
                    <span className="min-w-0 truncate text-sm font-medium text-zinc-300 transition-colors group-hover:text-white">
                      {inc.type}
                    </span>
                    {inc.verified && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
                        </TooltipTrigger>
                        <TooltipContent side="top">Verified incident</TooltipContent>
                      </Tooltip>
                    )}
                    <span className="ml-auto shrink-0 text-xs tabular-nums text-zinc-400">
                      {inc.date ? <FuzzyDate value={inc.date} /> : 'Undated'}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Incident types">
            {incidentTypes.length === 0 ? (
              <PanelEmpty>No incidents to break down.</PanelEmpty>
            ) : (
              <div className="flex flex-wrap gap-2">
                {incidentTypes.map(([type, count]) => (
                  <Link
                    key={type}
                    to="/incidents"
                    className="flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-800/60 px-2.5 py-1 text-xs transition-colors hover:border-violet-500/50 hover:bg-zinc-800 active:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
                  >
                    <span className="text-zinc-300">{type}</span>
                    <span className="font-semibold tabular-nums text-white">{count}</span>
                  </Link>
                ))}
              </div>
            )}
          </Panel>
        </div>

        {/* ── Leaderboards ───────────────────────────────────────────────────
            Three ranked lists share ONE panel and one header instead of three
            separate cards repeating the same chrome three times over. */}
        <section className="rounded-lg border border-zinc-800 bg-zinc-900/30">
          <div className="flex items-baseline gap-2 border-b border-zinc-800 px-3 py-1.5">
            <h2 className="text-xs font-semibold text-zinc-300">Most active</h2>
            <span className="text-[10px] text-zinc-400">by recorded involvement</span>
          </div>
          <div className="grid grid-cols-1 divide-y divide-zinc-800 md:grid-cols-[repeat(3,minmax(0,1fr))] md:divide-x md:divide-y-0">
            <LeaderColumn heading="Sets" loading={analyticsLoading} empty={topSets.length === 0}>
              {topSets.map((s, i) => (
                <LeaderRow
                  key={s.id} to="/sets/$id" params={{ id: setMap[s.id] ?? s.id }}
                  rank={i + 1} icon={Shield} label={s.name} count={s.incident_count}
                />
              ))}
            </LeaderColumn>

            <LeaderColumn heading="Members" loading={analyticsLoading} empty={topMembers.length === 0}>
              {topMembers.map((m, i) => (
                <LeaderRow
                  key={m.id} to="/members/$id" params={{ id: m.slug ?? m.id }}
                  rank={i + 1} icon={User} label={m.display_name} count={m.incident_count}
                />
              ))}
            </LeaderColumn>

            <LeaderColumn heading="Sources" loading={analyticsLoading} empty={topSources.length === 0}>
              {topSources.map((src, i) => (
                <LeaderRow
                  key={src.id} to="/sources/$id" params={{ id: src.id }}
                  rank={i + 1} icon={FileText} label={src.title} count={src.ref_count} countLabel="refs"
                />
              ))}
            </LeaderColumn>
          </div>
        </section>

        {/* ── Charts ─────────────────────────────────────────────────────── */}
        {hasCharts && (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-[repeat(2,minmax(0,1fr))]">
            {analytics.incidents_by_month.length > 0 && (
              <Panel title="Incidents over time" hint="monthly">
                <Suspense fallback={<Skeleton className="h-28 w-full" />}>
                  <IncidentsOverTime data={analytics.incidents_by_month} />
                </Suspense>
              </Panel>
            )}
            {Object.keys(analytics.source_by_reliability).length > 0 && (
              <Panel title="Source reliability" hint="by reference count">
                <Suspense fallback={<Skeleton className="h-28 w-full" />}>
                  <ReliabilityDonut counts={analytics.source_by_reliability} />
                </Suspense>
              </Panel>
            )}
          </div>
        )}
      </div>
    </TooltipProvider>
  )
}
