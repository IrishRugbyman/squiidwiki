import { createFileRoute, Link } from '@tanstack/react-router'
import {
  AlertTriangle, ArrowRight, CheckCircle2, FileText,
  Network, Shield, Skull, User, Users,
} from 'lucide-react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useIncidents, useSets, useUniverseAnalytics } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { NoUniverse } from '@/components/NoUniverse'
import type { MemberStatus } from '@/lib/types'

export const Route = createFileRoute('/_app/')({
  component: Dashboard,
})

// ─── Status colours (mirrored from members page) ─────────────────────────────

const STATUS_BAR: Record<string, string> = {
  FREE: 'bg-emerald-500',
  LOCKED: 'bg-orange-500',
  DEAD: 'bg-zinc-500',
  UNKNOWN: 'bg-zinc-700',
  ESCAPEE: 'bg-amber-500',
  ABSCONDER: 'bg-yellow-500',
}

const STATUS_LABEL: Record<string, string> = {
  FREE: 'text-emerald-400',
  LOCKED: 'text-orange-400',
  DEAD: 'text-zinc-400',
  UNKNOWN: 'text-zinc-500',
  ESCAPEE: 'text-amber-400',
  ABSCONDER: 'text-yellow-400',
}

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  to,
  accent = 'text-violet-400',
  loading,
}: {
  icon: typeof Shield
  label: string
  value: number | null | undefined
  to: string
  accent?: string
  loading?: boolean
}) {
  return (
    <Link
      to={to}
      className="group relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 transition-all hover:border-zinc-700 hover:bg-zinc-900"
    >
      <div className={`mb-3 inline-flex rounded-md bg-zinc-800/80 p-2 ${accent} group-hover:bg-zinc-800`}>
        <Icon className="h-4 w-4" />
      </div>
      {loading ? (
        <Skeleton className="mb-1 h-7 w-10" />
      ) : (
        <p className="text-2xl font-bold tabular-nums text-white">{value ?? '—'}</p>
      )}
      <p className="mt-0.5 text-xs text-zinc-500">{label}</p>
      <ArrowRight className="absolute right-3 top-3 h-3.5 w-3.5 text-zinc-700 opacity-0 transition-opacity group-hover:opacity-100" />
    </Link>
  )
}

// ─── Section card wrapper ─────────────────────────────────────────────────────

function Card({ title, action, children }: { title: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{title}</h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  )
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
    .sort((a, b) => b[1] - a[1])
  const totalMembers = statusEntries.reduce((s, [, n]) => s + n, 0)
  const setMap: Record<string, string | null> = {}
  for (const s of setsData?.items ?? []) setMap[s.id] = s.slug

  return (
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
        <Link to="/incidents" className="inline-flex items-center gap-1.5 rounded-md bg-violet-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-violet-500">
          <AlertTriangle className="h-3 w-3" />
          Record Incident
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard icon={Shield} label="Sets" value={analytics?.total_sets} to="/sets" accent="text-violet-400" loading={analyticsLoading} />
        <StatCard icon={Network} label="Alliances" value={analytics?.total_alliances} to="/alliances" accent="text-blue-400" loading={analyticsLoading} />
        <StatCard icon={Users} label="Members" value={analytics?.total_members} to="/members" accent="text-emerald-400" loading={analyticsLoading} />
        <StatCard icon={AlertTriangle} label="Incidents" value={analytics?.total_incidents} to="/incidents" accent="text-amber-400" loading={analyticsLoading} />
        <StatCard icon={FileText} label="Sources" value={analytics?.total_sources} to="/sources" accent="text-sky-400" loading={analyticsLoading} />
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
                <Skeleton className="h-2.5 w-full rounded-full" />
                <div className="flex gap-3">
                  {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-3 w-14" />)}
                </div>
              </div>
            ) : totalMembers === 0 ? (
              <p className="text-sm text-zinc-600">No members yet.</p>
            ) : (
              <>
                {/* Stacked bar */}
                <div className="mb-3 flex h-2.5 w-full overflow-hidden rounded-full bg-zinc-800">
                  {statusEntries.map(([status, count]) => (
                    <div
                      key={status}
                      className={`${STATUS_BAR[status] ?? 'bg-zinc-600'} transition-all`}
                      style={{ width: `${(count / totalMembers) * 100}%` }}
                      title={`${status}: ${count}`}
                    />
                  ))}
                </div>
                {/* Legend */}
                <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                  {statusEntries.map(([status, count]) => (
                    <Link
                      key={status}
                      to="/members"
                      className="flex items-center gap-1.5 text-xs hover:opacity-80 transition-opacity"
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${STATUS_BAR[status] ?? 'bg-zinc-600'}`} />
                      <span className={STATUS_LABEL[status as MemberStatus] ?? 'text-zinc-400'}>
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
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <Skeleton className="h-3 w-3" />
                    <Skeleton className="h-3 flex-1" />
                    <Skeleton className="h-4 w-6" />
                  </div>
                ))}
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
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <Skeleton className="h-3 w-3" />
                    <Skeleton className="h-3 flex-1" />
                    <Skeleton className="h-4 w-6" />
                  </div>
                ))}
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
            action={
              <Link to="/incidents" className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
                All incidents →
              </Link>
            }
          >
            {incidentsLoading ? (
              <div className="space-y-2.5">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full rounded-md" />)}
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
                      <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
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
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <Skeleton className="h-3 w-3" />
                    <Skeleton className="h-3 flex-1" />
                    <Skeleton className="h-4 w-6" />
                  </div>
                ))}
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
    </div>
  )
}
