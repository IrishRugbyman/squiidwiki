import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { AllianceStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAlliance, useSets, useDeleteAlliance } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { AllianceFormSheet } from './_app.alliances.index'

export const Route = createFileRoute('/_app/alliances/$id')({
  component: AllianceDetailPage,
})

function AllianceDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: alliance, isLoading, isError, refetch } = useAlliance(id, universe?.id ?? null)
  const { data: allSets } = useSets(universe?.id ?? null)
  const deleteAlliance = useDeleteAlliance(universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const setName = (sid: string) => allSets?.items.find((s) => s.id === sid)?.name ?? sid
  const setSlug = (sid: string) => allSets?.items.find((s) => s.id === sid)?.slug ?? sid

  async function handleDelete() {
    if (!alliance) return
    try {
      await deleteAlliance.mutateAsync(alliance.id)
      navigate({ to: '/alliances' })
    } catch {
      setDeleting(false)
    }
  }

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
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">{alliance.name}</h1>
              <div className="mt-2 flex items-center gap-2">
                <AllianceStatusBadge status={alliance.status} />
                {alliance.founded_at && (
                  <span className="text-xs text-zinc-500">Founded <FuzzyDate value={alliance.founded_at} /></span>
                )}
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

          {alliance.description && (
            <p className="mb-6 text-sm text-zinc-300 leading-relaxed">{alliance.description}</p>
          )}

          {alliance.set_ids.length > 0 ? (
            <div>
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">Member Sets ({alliance.set_ids.length})</h2>
              <div className="flex flex-wrap gap-2">
                {alliance.set_ids.map((sid) => (
                  <Link key={sid} to="/sets/$id" params={{ id: setSlug(sid) }}>
                    <Badge variant="secondary" className="hover:bg-zinc-700 cursor-pointer">{setName(sid)}</Badge>
                  </Link>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-zinc-600">No member sets.</p>
          )}

          {universe && (
            <AllianceFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={alliance}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Alliance"
            description={`Permanently delete "${alliance.name}"? This cannot be undone.`}
            confirmLabel="Delete"
            destructive
            pending={deleteAlliance.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
