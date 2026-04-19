import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, MapPin, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { useMunicipality, useMunicipalities, useDeleteMunicipality } from '@/lib/queries'
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
  const deleteMunicipality = useDeleteMunicipality(universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const parentName = municipality?.parent_id
    ? (allMunicipalities?.items.find((m) => m.id === municipality.parent_id)?.name ?? municipality.parent_id)
    : null

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
        <>
          <div className="mb-6 flex items-start justify-between">
            <div className="flex items-center gap-3">
              <MapPin className="h-6 w-6 shrink-0 text-zinc-500" />
              <div>
                <h1 className="text-2xl font-bold text-white">{municipality.name}</h1>
                {parentName && <p className="text-sm text-zinc-400">Part of {parentName}</p>}
              </div>
            </div>
            <div className="flex items-center gap-2">
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

          {universe && (
            <MunicipalityFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={municipality}
              allMunicipalities={allMunicipalities?.items}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Municipality"
            description={`Permanently delete "${municipality.name}"? This cannot be undone.`}
            confirmLabel="Delete"
            destructive
            pending={deleteMunicipality.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
