import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { AllianceStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { useAlliance } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/alliances/$id')({
  component: AllianceDetailPage,
})

function AllianceDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data: alliance, isLoading, isError, refetch } = useAlliance(id, universe?.id ?? null)

  if (isError) return <ErrorState title="Alliance not found" onRetry={() => refetch()} />

  return (
    <div>
      <Link to="/alliances" className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Alliances
      </Link>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-24" />
        </div>
      ) : alliance ? (
        <>
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white">{alliance.name}</h1>
            <div className="mt-2 flex items-center gap-2">
              <AllianceStatusBadge status={alliance.status} />
              {alliance.founded_at && (
                <span className="text-xs text-zinc-500">Founded <FuzzyDate value={alliance.founded_at} /></span>
              )}
            </div>
          </div>

          {alliance.description && (
            <p className="mb-6 text-sm text-zinc-300 leading-relaxed">{alliance.description}</p>
          )}

          {alliance.set_ids.length > 0 && (
            <div>
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">Member Sets ({alliance.set_ids.length})</h2>
              <div className="flex flex-wrap gap-2">
                {alliance.set_ids.map((sid) => (
                  <Link key={sid} to="/sets/$id" params={{ id: sid }}>
                    <Badge variant="secondary" className="hover:bg-zinc-700 cursor-pointer">{sid}</Badge>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  )
}
