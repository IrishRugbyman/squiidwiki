import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { AllianceStatusBadge, MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAlliance, useSets, useDeleteAlliance, useAllianceMembers, useAllianceIncidents } from '@/lib/queries'
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
  const { data: members } = useAllianceMembers(id, universe?.id ?? null)
  const { data: incidents } = useAllianceIncidents(id, universe?.id ?? null)
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
      <Breadcrumbs
        items={[
          { label: 'Alliances', to: '/alliances' },
          { label: alliance?.name ?? 'Alliance' },
        ]}
      />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : alliance ? (
        <>
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-2xl font-bold text-white">{alliance.name}</h1>
                <CopyButton value={window.location.href} label="Copy link to this alliance" className="opacity-60 hover:opacity-100" />
              </div>
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

          <Tabs defaultValue="sets">
            <TabsList>
              <TabsTrigger value="sets">
                Sets
                {alliance.set_ids.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{alliance.set_ids.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="members">
                Members
                {members && members.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{members.items.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="incidents">
                Incidents
                {incidents && incidents.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incidents.items.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="sets" className="mt-4">
              {alliance.set_ids.length === 0 ? (
                <p className="text-sm text-zinc-600">No member sets.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {alliance.set_ids.map((sid) => (
                    <Link key={sid} to="/sets/$id" params={{ id: setSlug(sid) }}>
                      <Badge variant="secondary" className="hover:bg-zinc-700 cursor-pointer">{setName(sid)}</Badge>
                    </Link>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="members" className="mt-4">
              {!members || members.items.length === 0 ? (
                <p className="text-sm text-zinc-600">No members in this alliance.</p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Name</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {members.items.map((m) => (
                        <tr key={m.id} className="hover:bg-zinc-900/50">
                          <td className="p-0">
                            <Link to="/members/$id" params={{ id: m.slug ?? m.id }} className="block px-4 py-3 text-white hover:text-violet-400">
                              {m.display_name}
                            </Link>
                          </td>
                          <td className="px-4 py-3">
                            <MemberStatusBadge status={m.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="incidents" className="mt-4">
              {!incidents || incidents.items.length === 0 ? (
                <p className="text-sm text-zinc-600">No incidents involving this alliance.</p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Type</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {incidents.items.map((inc) => (
                        <tr key={inc.id} className="hover:bg-zinc-900/50">
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-white hover:text-violet-400">
                              {inc.type}
                            </Link>
                          </td>
                          <td className="px-4 py-3 text-zinc-400">
                            <FuzzyDate value={inc.date} fallback="Unknown date" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>
          </Tabs>

          {universe && (
            <AllianceFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={alliance}
              onSaved={(updated) => {
                setEditing(false)
                const newId = updated.slug ?? updated.id
                if (newId !== id) navigate({ to: '/alliances/$id', params: { id: newId } })
              }}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Alliance"
            description={`Permanently delete "${alliance.name}"? This cannot be undone.`}
            impact={(() => {
              const setCount = alliance.set_ids.length
              const memberCount = members?.items.length ?? 0
              const incidentCount = incidents?.items.length ?? 0
              if (!setCount && !memberCount && !incidentCount) return null
              const parts: string[] = []
              if (setCount) parts.push(`${setCount} set${setCount === 1 ? '' : 's'}`)
              if (memberCount) parts.push(`${memberCount} member${memberCount === 1 ? '' : 's'}`)
              if (incidentCount) parts.push(`${incidentCount} incident${incidentCount === 1 ? '' : 's'}`)
              return <span>{parts.join(', ')} will lose this alliance link.</span>
            })()}
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
