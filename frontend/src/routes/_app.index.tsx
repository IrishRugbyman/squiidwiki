import { createFileRoute, Link } from '@tanstack/react-router'
import {
  AlertTriangle, ArrowRight, CheckCircle2, FileText,
  Network, Shield, Skull, User, Users,
} from 'lucide-react'
import { lazy, Suspense } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { StatCardSkeleton, ListItemSkeleton } from '@/components/skeletons'

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
import type { MemberStatus } from '@/lib/types'

export const Route = createFileRoute('/_app/')({
  component: Dashboard,
})

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatTile({
  icon: Icon,
  label,
  value,
  to,
  accent = 'violet',
  loading,
}: {
  icon: typeof Shield
  label: string
  value: number | null | undefined
  to: string
  accent?: 'violet' | 'blue' | 'emerald' | 'amber' | 'sky'
  loading?: boolean
}) {
  if (loading) return <StatCardSkeleton />

  const accentClass: Record<string, string> = {
    violet: 'text-violet-400 group-hover:border-violet-500/40',
    blue: 'text-blue-400 group-hover:border-blue-500/40',
    emerald: 'text-emerald-400 group-hover:border-emerald-500/40',
    amber: 'text-amber-400 group-hover:border-amber-500/40',
    sky: 'text-sky-400 group-hover:border-sky-500/40',
  }

  return (
    <Link
      to={to}
      className="group relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 transition-all hover:bg-zinc-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
    >
      <div className={`mb-3 inline-flex rounded-md bg-zinc-800/80 p-2 transition-colors ${accentClass[accent]}`}>
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-2xl font-bold tabular-nums text-white">{value ?? '—'}</p>
      <p className="mt-0.5 text-xs text-zinc-500">{label}</p>
      <ArrowRight className="absolute right-3 top-3 h-3.5 w-3.5 text-zinc-700 opacity-0 transition-opacity group-hover:opacity-100" />
    </Link>
  )
}

// ─── Section card wrapper ─────────────────────────────────────────────────────

function Card({ title, hint, action, children }: { title: string; hint?: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <div className="flex items-baseline gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{title}</h2>
          {hint && <span className="text-[10px] text-zinc-600">{hint}</span>}
        </div>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
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

  const recentIncidents = incidentData?.items.slice(0, 6) ?? []
  const statusEntries = Object.entries(analytics?.member_by_status ?? {})
    .sort((a, b) => MEMBER_STATUS_ORDER.indexOf(a[0] as MemberStatus) - MEMBER_STATUS_ORDER.indexOf(b[0] as MemberStatus))
  const totalMembers = statusEntries.reduce((s, [, n]) => s + n, 0)
  const setMap: Record<string, string | null> = {}
  for (const s of setsData?.items ?? []) setMap[s.id] = s.slug

  return (
    <TooltipProvider delayDuration={150}>
      <div className="space-y-6">
        {/* Universe header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2.5">
              <Skull className="h-5 w-5 text-violet-500" />
              <h1 className="text-xl font-bold text-white">{universe.name}</h1>
            </div>
            <p className="mt-0.5 pl-7 font-mono text-xs text-zinc-600">/{universe.slug}</p>
          </div>
          <Link to="/incidents" className="inline-flex items-center gap-1.5 rounded-md bg-violet-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-violet-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400">
            <AlertTriangle className="h-3 w-3" />
            Record Incident
          </Link>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <StatTile icon={Shield} label="Sets" value={analytics?.total_sets} to="/sets" accent="violet" loading={analyticsLoading} />
          <StatTile icon={Network} label="Alliances" value={analytics?.total_alliances} to="/alliances" accent="blue" loading={analyticsLoading} />
          <StatTile icon={Users} label="Members" value={analytics?.total_members} to="/members" accent="emerald" loading={analyticsLoading} />
          <StatTile icon={AlertTriangle} label="Incidents" value={analytics?.total_incidents} to="/incidents" accent="amber" loading={analyticsLoading} />
          <StatTile icon={FileText} label="Sources" value={analytics?.total_sources} to="/sources" accent="sky" loading={analyticsLoading} />
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">

          {/* Left column */}
          <div className="space-y-4">

            {/* Member status breakdown */}
            <Card
              title="Member Status"
              action={
                <Link to="/members" className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
                  View all →
                </Link>
              }
            >
              {analyticsLoading ? (
                <div className="space-y-2">
                  <div className="h-2.5 w-full animate-pulse rounded-full bg-zinc-800" />
                  <div className="flex gap-3">
                    {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-3 w-14 animate-pulse rounded bg-zinc-800" />)}
                  </div>
                </div>
              ) : totalMembers === 0 ? (
                <p className="text-sm text-zinc-600">No members yet.</p>
              ) : (
                <>
                  {/* Stacked bar */}
                  <div className="mb-3 flex h-2.5 w-full overflow-hidden rounded-full bg-zinc-800">
                    {statusEntries.map(([status, count]) => {
                      const pct = (count / totalMembers) * 100
                      const bg = MEMBER_STATUS_HEX[status as MemberStatus] ?? '#52525b'
                      return (
                        <Tooltip key={status}>
                          <TooltipTrigger asChild>
                            <div
                              className="transition-all hover:brightness-125"
                              style={{ width: `${pct}%`, backgroundColor: bg }}
                            />
                          </TooltipTrigger>
                          <TooltipContent side="top">
                            <div className="flex flex-col gap-0.5">
                              <span className="font-semibold">{status}: {count} ({pct.toFixed(1)}%)</span>
                              <span className="text-zinc-400">{MEMBER_STATUS_DESCRIPTION[status as MemberStatus]}</span>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      )
                    })}
                  </div>
                  {/* Legend */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                    {statusEntries.map(([status, count]) => (
                      <Link
                        key={status}
                        to="/members"
                        className="flex items-center gap-1.5 text-xs hover:opacity-80 transition-opacity"
                      >
                        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: MEMBER_STATUS_HEX[status as MemberStatus] ?? '#52525b' }} />
                        <span className={statusLabelColor(status)}>
                          {status}
                        </span>
                        <span className="font-medium tabular-nums text-zinc-300">{count}</span>
                      </Link>
                    ))}
                  </div>
                </>
              )}
            </Card>

            {/* Top sets by activity */}
            <Card
              title="Most Active Sets"
              action={
                <Link to="/sets" className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
                  All sets →
                </Link>
              }
            >
              {analyticsLoading ? (
                <div className="space-y-2.5">
                  {Array.from({ length: 4 }).map((_, i) => <ListItemSkeleton key={i} />)}
                </div>
              ) : !analytics?.top_sets_by_incidents.length ? (
                <p className="text-sm text-zinc-600">No incident data yet.</p>
              ) : (
                <div className="space-y-1">
                  {analytics.top_sets_by_incidents.map((s, i) => (
                    <Link
                      key={s.id}
                      to="/sets/$id"
                      params={{ id: setMap[s.id] ?? s.id }}
                      className="group flex items-center gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-zinc-800/60"
                    >
                      <span className="w-4 text-right text-xs text-zinc-600">{i + 1}</span>
                      <span className="flex-1 truncate text-sm text-zinc-300 group-hover:text-white">
                        {s.name}
                      </span>
                      <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-medium tabular-nums text-zinc-400">
                        {s.incident_count}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </Card>

            {/* Top members by incident involvement */}
            <Card
              title="Most Active Members"
              action={
                <Link to="/members" className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
                  All members →
                </Link>
              }
            >
              {analyticsLoading ? (
                <div className="space-y-2.5">
                  {Array.from({ length: 4 }).map((_, i) => <ListItemSkeleton key={i} />)}
                </div>
              ) : !analytics?.top_members_by_incidents.length ? (
                <p className="text-sm text-zinc-600">No incident data yet.</p>
              ) : (
                <div className="space-y-1">
                  {analytics.top_members_by_incidents.map((m, i) => (
                    <Link
                      key={m.id}
                      to="/members/$id"
                      params={{ id: m.id }}
                      className="group flex items-center gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-zinc-800/60"
                    >
                      <span className="w-4 text-right text-xs text-zinc-600">{i + 1}</span>
                      <User className="h-3 w-3 shrink-0 text-zinc-600 group-hover:text-zinc-400" />
                      <span className="flex-1 truncate text-sm text-zinc-300 group-hover:text-white">
                        {m.display_name}
                      </span>
                      <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-medium tabular-nums text-zinc-400">
                        {m.incident_count}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </Card>

          </div>

          {/* Right column */}
          <div className="space-y-4">

            {/* Recent incidents */}
            <Card
              title="Recent Incidents"
              hint="latest 6"
              action={
                <Link to="/incidents" className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
                  All incidents →
                </Link>
              }
            >
              {incidentsLoading ? (
                <div className="space-y-2.5">
                  {Array.from({ length: 4 }).map((_, i) => <ListItemSkeleton key={i} />)}
                </div>
              ) : recentIncidents.length === 0 ? (
                <div className="py-4 text-center">
                  <p className="text-sm text-zinc-600">No incidents recorded yet.</p>
                  <Link to="/incidents" className="mt-1.5 inline-block text-xs text-violet-400 hover:text-violet-300 transition-colors">
                    Record the first one →
                  </Link>
                </div>
              ) : (
                <div className="space-y-1">
                  {recentIncidents.map((inc) => (
                    <Link
                      key={inc.id}
                      to="/incidents/$id"
                      params={{ id: inc.id }}
                      className="group flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-zinc-800/60"
                    >
                      <AlertTriangle className={`h-3.5 w-3.5 shrink-0 ${inc.verified ? 'text-amber-500' : 'text-zinc-600'}`} />
                      <span className="text-sm font-medium text-zinc-300 group-hover:text-white">{inc.type}</span>
                      <span className="ml-auto text-xs text-zinc-600">
                        {inc.date ? <FuzzyDate value={inc.date} /> : 'Unknown date'}
                      </span>
                      {inc.verified && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
                          </TooltipTrigger>
                          <TooltipContent side="top">Verified incident</TooltipContent>
                        </Tooltip>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </Card>

            {/* Top sources */}
            <Card
              title="Most-cited Sources"
              action={
                <Link to="/sources" className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
                  All sources →
                </Link>
              }
            >
              {analyticsLoading ? (
                <div className="space-y-2.5">
                  {Array.from({ length: 4 }).map((_, i) => <ListItemSkeleton key={i} />)}
                </div>
              ) : !analytics?.top_sources_by_references.length ? (
                <p className="text-sm text-zinc-600">No sources yet.</p>
              ) : (
                <div className="space-y-1">
                  {analytics.top_sources_by_references.map((src, i) => (
                    <Link
                      key={src.id}
                      to="/sources/$id"
                      params={{ id: src.id }}
                      className="group flex items-center gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-zinc-800/60"
                    >
                      <span className="w-4 text-right text-xs text-zinc-600">{i + 1}</span>
                      <span className="flex-1 truncate text-sm text-zinc-300 group-hover:text-white">
                        {src.title}
                      </span>
                      <Badge variant="secondary" className="shrink-0 text-[10px] tabular-nums">
                        {src.ref_count} refs
                      </Badge>
                    </Link>
                  ))}
                </div>
              )}
            </Card>

            {/* Incident types */}
            {analytics && Object.keys(analytics.incident_by_type).length > 0 && (
              <Card title="Incident Types">
                <div className="flex flex-wrap gap-2">
                  {Object.entries(analytics.incident_by_type).map(([type, count]) => (
                    <Link
                      key={type}
                      to="/incidents"
                      className="flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-800/60 px-2.5 py-1 text-xs transition-colors hover:border-zinc-600 hover:bg-zinc-800"
                    >
                      <span className="text-zinc-300">{type}</span>
                      <span className="font-bold tabular-nums text-white">{count}</span>
                    </Link>
                  ))}
                </div>
              </Card>
            )}

          </div>
        </div>

        {/* Analytics charts row */}
        {analytics && (analytics.incidents_by_month.length > 0 || Object.keys(analytics.source_by_reliability).length > 0) && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {analytics.incidents_by_month.length > 0 && (
              <Card title="Incidents Over Time" hint="monthly">
                <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                  <IncidentsOverTime data={analytics.incidents_by_month} />
                </Suspense>
              </Card>
            )}
            {Object.keys(analytics.source_by_reliability).length > 0 && (
              <Card title="Source Reliability" hint="by reference count">
                <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                  <ReliabilityDonut counts={analytics.source_by_reliability} />
                </Suspense>
              </Card>
            )}
          </div>
        )}
      </div>
    </TooltipProvider>
  )
}
