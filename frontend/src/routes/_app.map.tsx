import { createFileRoute, Link } from '@tanstack/react-router'
import { MapPin, AlertTriangle } from 'lucide-react'
import { Suspense, lazy } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { useUniverseStore } from '@/stores/universe'
import { useMunicipalitiesAll } from '@/lib/queries'
import type { UUID } from '@/lib/types'

const MunicipalityMap = lazy(() => import('@/components/maps/MunicipalityMap'))

export const Route = createFileRoute('/_app/map')({
  validateSearch: (s: Record<string, unknown>) => ({
    focus: typeof s.focus === 'string' ? (s.focus as UUID) : undefined,
  }),
  component: MapPage,
})

function MapPage() {
  const { focus } = Route.useSearch()
  const universeId = useUniverseStore((s) => s.activeUniverse?.id ?? null)
  const { data, isLoading } = useMunicipalitiesAll(universeId)

  if (!universeId) return <NoUniverse />

  const municipalities = data?.items ?? []
  const withCoords = municipalities.filter((m) => m.latitude != null && m.longitude != null)
  const withoutCoords = municipalities.filter((m) => m.latitude == null || m.longitude == null)

  return (
    <div className="flex h-[calc(100vh-3.5rem-3rem)] flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Map</h1>
          <p className="text-sm text-zinc-400">
            {withCoords.length} of {municipalities.length} municipalities pinned
          </p>
        </div>
        {withoutCoords.length > 0 && (
          <Link
            to="/municipalities"
            className="flex items-center gap-1.5 rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:border-zinc-500 hover:text-white transition-colors"
          >
            <MapPin className="h-3.5 w-3.5" />
            Add coordinates to {withoutCoords.length} municipality{withoutCoords.length !== 1 ? 'ies' : 'y'}
          </Link>
        )}
      </div>

      <div className="relative flex-1 overflow-hidden rounded-xl border border-zinc-800">
        {isLoading ? (
          <div className="flex h-full items-center justify-center bg-zinc-900">
            <div className="flex flex-col items-center gap-2 text-zinc-500">
              <MapPin className="h-8 w-8 animate-pulse" />
              <span className="text-sm">Loading map…</span>
            </div>
          </div>
        ) : withCoords.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 bg-zinc-900 text-center">
            <MapPin className="h-10 w-10 text-zinc-600" />
            <div>
              <p className="font-medium text-white">No coordinates yet</p>
              <p className="mt-1 text-sm text-zinc-500">
                Edit a municipality and set its latitude & longitude to pin it on the map.
              </p>
            </div>
            <Link
              to="/municipalities"
              className="mt-2 rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
            >
              Go to Municipalities
            </Link>
          </div>
        ) : (
          <Suspense
            fallback={
              <div className="flex h-full items-center justify-center bg-zinc-900">
                <div className="flex flex-col items-center gap-2 text-zinc-500">
                  <MapPin className="h-8 w-8 animate-pulse" />
                  <span className="text-sm">Loading map…</span>
                </div>
              </div>
            }
          >
            <MunicipalityMap municipalities={municipalities} focusId={focus} />
          </Suspense>
        )}
      </div>

      {withoutCoords.length > 0 && withCoords.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-xs text-amber-400">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            {withoutCoords.length} municipality{withoutCoords.length !== 1 ? 'ies are' : 'y is'} not shown because{' '}
            {withoutCoords.length !== 1 ? 'they have' : 'it has'} no coordinates:{' '}
            {withoutCoords.slice(0, 5).map((m, i) => (
              <span key={m.id}>
                <Link to="/municipalities/$id" params={{ id: m.id }} className="underline hover:text-amber-200">
                  {m.name}
                </Link>
                {i < Math.min(withoutCoords.length, 5) - 1 && ', '}
              </span>
            ))}
            {withoutCoords.length > 5 && ` and ${withoutCoords.length - 5} more`}
          </span>
        </div>
      )}
    </div>
  )
}
