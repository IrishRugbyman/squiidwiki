import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowLeft, MapPin } from 'lucide-react'
import { ErrorState } from '@/components/ErrorState'
import { Skeleton } from '@/components/ui/skeleton'
import { useMunicipality, useMunicipalities } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/municipalities/$id')({
  component: MunicipalityDetailPage,
})

function MunicipalityDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data: municipality, isLoading, isError, refetch } = useMunicipality(id, universe?.id ?? null)
  const { data: allMunicipalities } = useMunicipalities(universe?.id ?? null)

  if (isError) return <ErrorState title="Municipality not found" onRetry={() => refetch()} />

  const parentName = municipality?.parent_id
    ? (allMunicipalities?.items.find((m) => m.id === municipality.parent_id)?.name ?? municipality.parent_id)
    : null

  return (
    <div>
      <Link to="/municipalities" className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Municipalities
      </Link>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-24" />
        </div>
      ) : municipality ? (
        <div className="mb-6 flex items-center gap-3">
          <MapPin className="h-6 w-6 shrink-0 text-zinc-500" />
          <div>
            <h1 className="text-2xl font-bold text-white">{municipality.name}</h1>
            {parentName && <p className="text-sm text-zinc-400">Part of {parentName}</p>}
          </div>
        </div>
      ) : null}
    </div>
  )
}
