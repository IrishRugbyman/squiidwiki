import { createFileRoute, Link } from '@tanstack/react-router'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { useUniverseAnalytics } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/stats')({
  component: StatsPage,
})

const STATUS_COLOR: Record<string, string> = {
  FREE: 'bg-emerald-600',
  LOCKED: 'bg-amber-600',
  DEAD: 'bg-zinc-600',
  UNKNOWN: 'bg-zinc-700',
  ESCAPEE: 'bg-orange-600',
  ABSCONDER: 'bg-red-700',
}

const TYPE_COLOR: Record<string, string> = {
  SHOOTING: 'bg-red-600',
  MURDER: 'bg-purple-700',
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 text-center">
      <div className="text-3xl font-bold text-white">{value.toLocaleString()}</div>
      <div className="mt-1 text-xs text-zinc-500">{label}</div>
    </div>
  )
}

function BarChart({ data, colorMap }: { data: Record<string, number>; colorMap: Record<string, string> }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  if (total === 0) return <p className="text-sm text-zinc-600">No data.</p>
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1])
  return (
    <div className="space-y-2">
      {sorted.map(([key, count]) => {
        const pct = Math.round((count / total) * 100)
        return (
          <div key={key}>
            <div className="mb-0.5 flex items-center justify-between text-xs">
              <span className="text-zinc-400">{key}</span>
              <span className="text-zinc-500">{count} ({pct}%)</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-800">
              <div
                className={`h-full rounded-full ${colorMap[key] ?? 'bg-zinc-600'} transition-all`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function StatsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data, isLoading } = useUniverseAnalytics(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  return (
    <div>
      <PageHeader title="Analytics" description={universe.name} />

      {isLoading ? (
        <div className="grid grid-cols-4 gap-3 mb-6">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)}
        </div>
      ) : data ? (
        <>
          <div className="grid grid-cols-2 gap-3 mb-6 sm:grid-cols-4">
            <StatCard label="Members" value={data.total_members} />
            <StatCard label="Sets" value={data.total_sets} />
            <StatCard label="Incidents" value={data.total_incidents} />
            <StatCard label="Sources" value={data.total_sources} />
          </div>

          <div className="grid grid-cols-1 gap-4 mb-6 sm:grid-cols-2">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">Members by Status</h2>
              <BarChart data={data.member_by_status} colorMap={STATUS_COLOR} />
            </div>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">Incidents by Type</h2>
              <BarChart data={data.incident_by_type} colorMap={TYPE_COLOR} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">Most Active Sets</h2>
              {data.top_sets_by_incidents.length === 0 ? (
                <p className="text-sm text-zinc-600">No incident data yet.</p>
              ) : (
                <ol className="space-y-2">
                  {data.top_sets_by_incidents.map((s, i) => (
                    <li key={s.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-zinc-600 w-4">{i + 1}.</span>
                        <Link to="/sets/$id" params={{ id: s.id }} className="text-sm text-white hover:text-violet-400 transition-colors">
                          {s.name}
                        </Link>
                      </div>
                      <span className="text-xs text-zinc-500">{s.incident_count} incidents</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">Most Referenced Sources</h2>
              {data.top_sources_by_references.length === 0 ? (
                <p className="text-sm text-zinc-600">No citation data yet.</p>
              ) : (
                <ol className="space-y-2">
                  {data.top_sources_by_references.map((s, i) => (
                    <li key={s.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-zinc-600 w-4">{i + 1}.</span>
                        <Link to="/sources/$id" params={{ id: s.id }} className="text-sm text-white hover:text-violet-400 transition-colors truncate max-w-[200px]">
                          {s.title}
                        </Link>
                      </div>
                      <span className="text-xs text-zinc-500 shrink-0">{s.ref_count} refs</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
