import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { AlertTriangle, ChevronRight, MapPin, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { useMunicipality, useMunicipalities, useDeleteMunicipality, useIncidentsByMunicipality } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { MunicipalityFormSheet } from './_app.municipalities.index'

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

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const allItems = allMunicipalities?.items ?? []
  const parent = municipality?.parent_id
    ? allItems.find((m) => m.id === municipality.parent_id)
    : null
  const children = allItems.filter((m) => m.parent_id === id)
  const incidents = incidentData?.items ?? []

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

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-sm text-zinc-500">
        <Link to="/municipalities" className="hover:text-white transition-colors">Municipalities</Link>
        {parent && (
          <>
            <ChevronRight className="h-3.5 w-3.5" />
            <Link to="/municipalities/$id" params={{ id: parent.id }} className="hover:text-white transition-colors">
              {parent.name}
            </Link>
          </>
        )}
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-zinc-300">{municipality?.name ?? '…'}</span>
      </div>

      {/* Header */}
      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      ) : municipality ? (
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-zinc-800/80 p-3">
              <MapPin className="h-6 w-6 text-zinc-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{municipality.name}</h1>
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
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
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

      {/* Sub-districts */}
      {children.length > 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
          <div className="border-b border-zinc-800 px-4 py-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Sub-districts</h2>
          </div>
          <div className="divide-y divide-zinc-800/60">
            {children.map((child) => (
              <Link
                key={child.id}
                to="/municipalities/$id"
                params={{ id: child.id }}
                className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-zinc-800/40"
              >
                <MapPin className="h-3.5 w-3.5 shrink-0 text-zinc-600" />
                <span className="flex-1 text-sm text-zinc-300 hover:text-white">{child.name}</span>
                <span className={`text-xs tabular-nums ${child.incident_count > 0 ? 'text-amber-400' : 'text-zinc-600'}`}>
                  {child.incident_count} incidents
                </span>
                <ChevronRight className="h-3.5 w-3.5 text-zinc-700" />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Incidents */}
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
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-10 w-full rounded-md" />)}
            </div>
          ) : incidents.length === 0 ? (
            <p className="px-4 py-6 text-sm text-zinc-600">No incidents recorded in {municipality?.name}.</p>
          ) : (
            incidents.map((inc) => (
              <Link
                key={inc.id}
                to="/incidents/$id"
                params={{ id: inc.id }}
                className="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-zinc-800/40"
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
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" title="Verified" />
                )}
              </Link>
            ))
          )}
        </div>
      </div>

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

      <ConfirmDialog
        open={deleting}
        title="Delete Municipality"
        description={`Permanently delete "${municipality?.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        destructive
        pending={deleteMunicipality.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleting(false)}
      />
    </div>
  )
}
