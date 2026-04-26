import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { AlertTriangle, ChevronRight, CheckCircle2, Map, MapPin, Pencil, Plus, Trash2 } from 'lucide-react'
import { lazy, Suspense, useState } from 'react'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  useMunicipality, useMunicipalities, useDeleteMunicipality,
  useIncidentsByMunicipality, useMunicipalityGeoJSON,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { MunicipalityFormSheet } from './_app.municipalities.index'
import type { MunicipalityListItem } from '@/lib/types'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'

const MunicipalityMap = lazy(() => import('@/components/maps/MunicipalityMap'))

export const Route = createFileRoute('/_app/municipalities/$id')({
  component: MunicipalityDetailPage,
})

function MunicipalityDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const { data: municipality, isLoading, isError, refetch } = useMunicipality(id, universe?.id ?? null)
  const { data: allMunicipalities } = useMunicipalities(universe?.id ?? null)
  const { data: incidentData, isLoading: incidentsLoading } = useIncidentsByMunicipality(id, universe?.id ?? null)
  const deleteMunicipality = useDeleteMunicipality(universe?.id ?? '')

  useRecordRecent(municipality ? { type: 'municipality', id: municipality.id, slug: null, label: municipality.name } : null)

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEditShortcut(() => municipality && setEditing(true))

  const allItems = allMunicipalities?.items ?? []
  const parent = municipality?.parent_id
    ? allItems.find((m) => m.id === municipality.parent_id)
    : null
  const children = allItems.filter((m) => m.parent_id === id)
  const childrenWithGeometry = children.filter((c) => c.has_geometry)
  const incidents = incidentData?.items ?? []

  // GeoJSON for this municipality's children. Only fetched when there are
  // mappable children, so detail pages without districts pay no cost.
  const { data: childrenGeoJSON } = useMunicipalityGeoJSON(
    childrenWithGeometry.length > 0 ? universe?.id ?? null : null,
    childrenWithGeometry.length > 0 ? id : undefined,
  )

  const [creatingChild, setCreatingChild] = useState(false)

  async function handleDelete() {
    if (!municipality) return
    try {
      await deleteMunicipality.mutateAsync(municipality.id)
      navigate({ to: '/municipalities' })
    } catch {
      setDeleting(false)
    }
  }

  if (isError) return <ErrorState title="Municipality not found" onRetry={() => refetch()} />

  const breadcrumbItems = [
    { label: 'Municipalities', to: '/municipalities' },
    ...(parent ? [{ label: parent.name, to: `/municipalities/${parent.id}` }] : []),
    { label: municipality?.name ?? 'Municipality' },
  ]

  return (
    <div className="space-y-6">
      <Breadcrumbs items={breadcrumbItems} />

      {/* Header */}
      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : municipality ? (
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-zinc-800/80 p-3">
              <MapPin className="h-6 w-6 text-zinc-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-2xl font-bold text-white">{municipality.name}</h1>
                <CopyButton value={window.location.href} label="Copy link to this municipality" className="opacity-60 hover:opacity-100" />
              </div>
              {parent && (
                <p className="mt-0.5 text-sm text-zinc-500">
                  District of{' '}
                  <Link to="/municipalities/$id" params={{ id: parent.id }} className="text-zinc-400 hover:text-white transition-colors">
                    {parent.name}
                  </Link>
                </p>
              )}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {municipality.has_geometry && (
              <Link to="/map" search={{ focus: municipality.id }}>
                <Button size="sm" variant="outline">
                  <Map className="mr-1.5 h-3.5 w-3.5" />View on map
                </Button>
              </Link>
            )}
            <Button size="sm" variant="outline" onClick={() => setCreatingChild(true)}>
              <Plus className="mr-1.5 h-3.5 w-3.5" />Add sub-district
            </Button>
            <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
              <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
            </Button>
            {user?.global_role === 'ADMIN' && (
              <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
              </Button>
            )}
          </div>
        </div>
      ) : null}

      {/* Stats row */}
      {municipality && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 text-center">
            <div className="text-2xl font-bold tabular-nums text-white">{incidents.length}</div>
            <div className="mt-0.5 text-xs text-zinc-500">Incidents</div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 text-center">
            <div className="text-2xl font-bold tabular-nums text-white">{children.length}</div>
            <div className="mt-0.5 text-xs text-zinc-500">Sub-districts</div>
          </div>
        </div>
      )}

      {/* Sub-districts map — only when at least one child has geometry */}
      {childrenGeoJSON && childrenGeoJSON.features.length > 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 overflow-hidden">
          <div className="border-b border-zinc-800 px-4 py-3 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Districts map
            </h2>
            <span className="text-[11px] text-zinc-600">
              {childrenGeoJSON.features.length} of {children.length} mapped · click to zoom
            </span>
          </div>
          <div className="h-[420px] relative">
            <Suspense fallback={
              <div className="flex h-full items-center justify-center bg-zinc-900">
                <div className="flex flex-col items-center gap-2 text-zinc-500">
                  <MapPin className="h-8 w-8 animate-pulse" />
                  <span className="text-sm">Loading map…</span>
                </div>
              </div>
            }>
              <MunicipalityMap geojson={childrenGeoJSON} />
            </Suspense>
          </div>
        </div>
      )}

      {/* Sub-districts */}
      {children.length > 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
          <div className="border-b border-zinc-800 px-4 py-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Sub-districts ({children.length})</h2>
          </div>
          <div className="grid grid-cols-1 gap-1 p-2 sm:grid-cols-2 lg:grid-cols-3">
            {children.map((child) => (
              <Link
                key={child.id}
                to="/municipalities/$id"
                params={{ id: child.id }}
                className="group flex items-center gap-2 rounded-md border border-transparent px-3 py-2 transition-colors hover:border-zinc-700 hover:bg-zinc-800/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
              >
                <MapPin className="h-3.5 w-3.5 shrink-0 text-zinc-600 group-hover:text-zinc-400" />
                <span className="flex-1 truncate text-sm text-zinc-300 group-hover:text-white">{child.name}</span>
                <span className={`text-xs tabular-nums ${child.incident_count > 0 ? 'text-amber-400' : 'text-zinc-600'}`}>
                  {child.incident_count}
                </span>
                <ChevronRight className="h-3.5 w-3.5 text-zinc-700 group-hover:text-zinc-500" />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Incidents */}
      <TooltipProvider delayDuration={250}>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
          <div className="border-b border-zinc-800 px-4 py-3 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Incidents</h2>
            <Link to="/incidents" className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
              All incidents →
            </Link>
          </div>
          <div className="divide-y divide-zinc-800/60">
            {incidentsLoading ? (
              <div className="space-y-1 p-4">
                {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-10 w-full animate-pulse rounded-md bg-zinc-800" />)}
              </div>
            ) : incidents.length === 0 ? (
              <p className="px-4 py-6 text-sm text-zinc-600">No incidents recorded in {municipality?.name}.</p>
            ) : (
              incidents.map((inc) => (
                <Link
                  key={inc.id}
                  to="/incidents/$id"
                  params={{ id: inc.id }}
                  className="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-zinc-800/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
                >
                  <AlertTriangle className={`h-3.5 w-3.5 shrink-0 ${inc.type === 'MURDER' ? 'text-rose-500' : 'text-amber-500'}`} />
                  <span className="text-sm font-medium text-zinc-300 group-hover:text-white">{inc.type}</span>
                  {inc.victim_names.length > 0 && (
                    <span className="text-sm text-zinc-500">— {inc.victim_names.slice(0, 2).join(', ')}{inc.victim_names.length > 2 ? ` +${inc.victim_names.length - 2}` : ''}</span>
                  )}
                  <span className="ml-auto text-xs text-zinc-600">
                    {inc.date ? <FuzzyDate value={inc.date} /> : 'Unknown date'}
                  </span>
                  {inc.verified && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
                      </TooltipTrigger>
                      <TooltipContent>Verified incident</TooltipContent>
                    </Tooltip>
                  )}
                </Link>
              ))
            )}
          </div>
        </div>
      </TooltipProvider>

      {/* Sheets / dialogs */}
      {universe && municipality && (
        <MunicipalityFormSheet
          universeId={universe.id}
          open={editing}
          onClose={() => setEditing(false)}
          initial={municipality}
          allMunicipalities={allItems as MunicipalityListItem[]}
        />
      )}

      {universe && (
        <MunicipalityFormSheet
          universeId={universe.id}
          open={creatingChild}
          onClose={() => setCreatingChild(false)}
          defaultParentId={id}
          allMunicipalities={allItems as MunicipalityListItem[]}
        />
      )}

      <ConfirmDialog
        open={deleting}
        title="Delete Municipality"
        description={`Permanently delete "${municipality?.name}"? This cannot be undone.`}
        impact={(() => {
          const parts: string[] = []
          if (children.length) parts.push(`${children.length} sub-district${children.length === 1 ? '' : 's'} will be orphaned`)
          if (incidents.length) parts.push(`${incidents.length} incident${incidents.length === 1 ? '' : 's'} will lose this location`)
          if (!parts.length) return null
          return <span>{parts.join('. ')}.</span>
        })()}
        confirmLabel="Delete"
        destructive
        pending={deleteMunicipality.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleting(false)}
      />
    </div>
  )
}
