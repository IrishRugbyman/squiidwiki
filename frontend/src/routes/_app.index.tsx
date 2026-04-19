import { createFileRoute, Link } from '@tanstack/react-router'
import { AlertTriangle, FileText, Network, Shield, Users } from 'lucide-react'
import { useAlliances } from '@/lib/queries'
import { useIncidents } from '@/lib/queries'
import { useMembers } from '@/lib/queries'
import { useSets } from '@/lib/queries'
import { useSources } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { NoUniverse } from '@/components/NoUniverse'
import { Skeleton } from '@/components/ui/skeleton'

export const Route = createFileRoute('/_app/')({
  component: Dashboard,
})

function StatCard({
  icon: Icon,
  label,
  value,
  to,
  loading,
}: {
  icon: typeof Shield
  label: string
  value: number | null | undefined
  to: string
  loading: boolean
}) {
  return (
    <Link
      to={to}
      className="group flex items-center gap-4 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 transition-colors hover:border-zinc-700 hover:bg-zinc-900"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-zinc-800 text-violet-400 group-hover:bg-zinc-700">
        <Icon className="h-5 w-5" />
      </div>
      <div>
        {loading ? (
          <Skeleton className="mb-1 h-6 w-12" />
        ) : (
          <p className="text-xl font-bold text-white">{value ?? '—'}</p>
        )}
        <p className="text-xs text-zinc-400">{label}</p>
      </div>
    </Link>
  )
}

function Dashboard() {
  const universe = useUniverseStore((s) => s.activeUniverse)

  const { data: sets, isLoading: setsLoading } = useSets(universe?.id ?? null)
  const { data: members, isLoading: membersLoading } = useMembers(universe?.id ?? null)
  const { data: incidents, isLoading: incidentsLoading } = useIncidents(universe?.id ?? null)
  const { data: alliances, isLoading: alliancesLoading } = useAlliances(universe?.id ?? null)
  const { data: sources, isLoading: sourcesLoading } = useSources(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">{universe.name}</h1>
        <p className="text-sm text-zinc-500">/{universe.slug}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard icon={Shield} label="Sets" value={sets?.total} to="/sets" loading={setsLoading} />
        <StatCard icon={Network} label="Alliances" value={alliances?.total} to="/alliances" loading={alliancesLoading} />
        <StatCard icon={Users} label="Members" value={members?.total ?? null} to="/members" loading={membersLoading} />
        <StatCard icon={AlertTriangle} label="Incidents" value={incidents?.total ?? null} to="/incidents" loading={incidentsLoading} />
        <StatCard icon={FileText} label="Sources" value={sources?.total} to="/sources" loading={sourcesLoading} />
      </div>
    </div>
  )
}
