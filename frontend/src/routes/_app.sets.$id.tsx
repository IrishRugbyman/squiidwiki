import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Pencil, Plus, Swords, Trash2, Users, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import {
  useSet, useSetStats, useSets, useDeleteSet,
  useAddSetRelationship, useRemoveSetRelationship,
  useSetMembers, useSetIncidents, useAlliances,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { SetStatusBadge, MemberStatusBadge } from '@/components/StatusBadge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { lazy, Suspense } from 'react'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Skeleton } from '@/components/ui/skeleton'
import { SetAvatar, SetFormSheet } from './_app.sets.index'

const SetRelationshipGraph = lazy(() =>
  import('@/components/graphs/SetRelationshipGraph').then((m) => ({ default: m.SetRelationshipGraph })),
)

export const Route = createFileRoute('/_app/sets/$id')({
  component: SetDetailPage,
})

function StatPill({ label, value, accent = 'text-white' }: { label: string; value: number; accent?: string }) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <span className={`text-2xl font-bold tabular-nums ${accent}`}>{value}</span>
      <span className="mt-0.5 text-xs text-zinc-500">{label}</span>
    </div>
  )
}

function AddRelationshipDialog({
  setId, universeId, open, onClose, existingIds,
}: { setId: string; universeId: string; open: boolean; onClose: () => void; existingIds: string[] }) {
  const { data: allSets } = useSets(universeId)
  const add = useAddSetRelationship(setId, universeId)
  const [targetId, setTargetId] = useState('')
  const [type, setType] = useState<'FRIEND' | 'ENEMY'>('FRIEND')
  const [error, setError] = useState<string | null>(null)

  const available = (allSets?.items ?? []).filter(
    (s) => s.id !== setId && !existingIds.includes(s.id)
  )

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!targetId) return
    setError(null)
    try {
      await add.mutateAsync({ target_id: targetId, type })
      setTargetId(''); setType('FRIEND')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add relationship')
    }
  }

  const isAlly = type === 'FRIEND'

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isAlly ? <Users className="h-4 w-4 text-emerald-400" /> : <Swords className="h-4 w-4 text-red-400" />}
            Add {isAlly ? 'Ally' : 'Enemy'}
          </DialogTitle>
          <DialogDescription>
            Relationships are bilateral — the selected set will show this set as {isAlly ? 'an ally' : 'an enemy'} too.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">Relationship type</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setType('FRIEND')}
                className={`flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
                  isAlly
                    ? 'border-emerald-600 bg-emerald-950/40 text-emerald-300'
                    : 'border-zinc-800 bg-zinc-900/50 text-zinc-500 hover:text-zinc-300'
                }`}
              >
                <Users className="h-4 w-4" /> Ally
              </button>
              <button
                type="button"
                onClick={() => setType('ENEMY')}
                className={`flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
                  !isAlly
                    ? 'border-red-700 bg-red-950/40 text-red-300'
                    : 'border-zinc-800 bg-zinc-900/50 text-zinc-500 hover:text-zinc-300'
                }`}
              >
                <Swords className="h-4 w-4" /> Enemy
              </button>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">Set</label>
            <Select value={targetId} onValueChange={setTargetId}>
              <SelectTrigger><SelectValue placeholder="Select a set…" /></SelectTrigger>
              <SelectContent>
                {available.length === 0 ? (
                  <div className="px-2 py-4 text-center text-xs text-zinc-500">No available sets to link.</div>
                ) : (
                  available.map((s) => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 justify-end">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={!targetId || add.isPending}>
              {add.isPending ? 'Adding…' : `Add ${isAlly ? 'Ally' : 'Enemy'}`}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function SetDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: set, isLoading, isError, refetch } = useSet(id, universe?.id ?? null)
  const realId = set?.id ?? ''
  const { data: stats } = useSetStats(realId, universe?.id ?? null)
  const { data: allSets } = useSets(universe?.id ?? null)
  const { data: alliancesData } = useAlliances(universe?.id ?? null)
  const { data: membersData } = useSetMembers(realId, universe?.id ?? null)
  const { data: incidentsData } = useSetIncidents(realId, universe?.id ?? null)

  const deleteSet = useDeleteSet(universe?.id ?? '')
  const removeRel = useRemoveSetRelationship(realId, universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [addingRel, setAddingRel] = useState(false)

  const setName = (sid: string) => allSets?.items.find((s) => s.id === sid)?.name ?? sid
  const alliance = set?.alliance_id
    ? (alliancesData?.items ?? []).find((a) => a.id === set.alliance_id) ?? null
    : null

  const allRelIds = set ? [...set.friend_ids, ...set.enemy_ids] : []
  const hasRelationships = set ? set.friend_ids.length + set.enemy_ids.length > 0 : false

  async function handleDelete() {
    if (!set) return
    try {
      await deleteSet.mutateAsync(set.id)
      navigate({ to: '/sets' })
    } catch (err) {
      setDeleting(false)
      toast.error(err instanceof Error ? err.message : 'Failed to delete set')
    }
  }

  if (isError) return <ErrorState title="Set not found" onRetry={() => refetch()} />

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Sets', to: '/sets' },
          { label: set?.name ?? 'Set' },
        ]}
      />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : set ? (
        <>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <SetAvatar name={set.name} size="md" />
              <div>
                <div className="flex items-center gap-1.5">
                  <h1 className="text-2xl font-bold text-white">{set.name}</h1>
                  <CopyButton value={window.location.href} label="Copy link to this set" className="opacity-60 hover:opacity-100" />
                </div>
                {set.alias && <p className="text-sm text-zinc-400">a/k/a {set.alias}</p>}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <SetStatusBadge status={set.status} />
                  {alliance && (
                    <Link
                      to="/alliances/$id"
                      params={{ id: alliance.slug ?? alliance.id }}
                      className="inline-flex items-center gap-1 rounded-full border border-violet-700/50 bg-violet-950/30 px-2 py-0.5 text-xs font-medium text-violet-300 hover:text-violet-200 transition-colors"
                    >
                      {alliance.name}
                    </Link>
                  )}
                </div>
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

          {set.bio && (
            <p className="mb-4 text-sm text-zinc-400 leading-relaxed max-w-2xl">{set.bio}</p>
          )}

          {stats && (
            <div className="mb-6 grid grid-cols-5 gap-2">
              <StatPill label="Members" value={stats.member_count} />
              <StatPill label="Dead" value={stats.dead_members} accent="text-zinc-400" />
              <StatPill label="Shootings" value={stats.total_shootings} accent="text-amber-400" />
              <StatPill label="Assists" value={stats.total_assists} accent="text-violet-400" />
              <StatPill label="Kills" value={stats.total_kills} accent="text-rose-400" />
            </div>
          )}

          <Tabs defaultValue="members">
            <TabsList>
              <TabsTrigger value="members">
                Members
                {membersData && membersData.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{membersData.items.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="incidents">
                Incidents
                {incidentsData && incidentsData.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incidentsData.items.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="relationships">
                Relationships
                {hasRelationships && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">
                    {set.friend_ids.length + set.enemy_ids.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="members" className="mt-4">
              {!membersData || membersData.items.length === 0 ? (
                <p className="text-sm text-zinc-600">No members in this set.</p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Name</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {membersData.items.map((m) => (
                        <tr key={m.id} className="hover:bg-zinc-900/50">
                          <td className="p-0">
                            <Link to="/members/$id" params={{ id: m.id }} className="block px-4 py-3 font-medium text-white hover:text-violet-400 transition-colors">
                              {m.display_name}
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/members/$id" params={{ id: m.id }} className="block px-4 py-3" tabIndex={-1}>
                              <MemberStatusBadge status={m.status} />
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="incidents" className="mt-4">
              {!incidentsData || incidentsData.items.length === 0 ? (
                <p className="text-sm text-zinc-600">No incidents recorded.</p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Date</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Type</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Location</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {incidentsData.items.map((inc) => (
                        <tr key={inc.id} className="hover:bg-zinc-900/50">
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-zinc-300 hover:text-violet-400">
                              {inc.date ? <FuzzyDate value={inc.date} /> : '—'}
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3" tabIndex={-1}>
                              <Badge variant="outline" className="text-xs">{inc.type}</Badge>
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-zinc-400" tabIndex={-1}>
                              {inc.municipality_id ?? '—'}
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="relationships" className="mt-4">
              <div className="mb-3 flex justify-end">
                <Button size="sm" variant="outline" onClick={() => setAddingRel(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Relationship
                </Button>
              </div>
              {!hasRelationships ? (
                <p className="text-sm text-zinc-600">No relationships recorded.</p>
              ) : (
                <div className="space-y-4">
                  {set.friend_ids.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                        <Users className="h-3.5 w-3.5" /> Allies ({set.friend_ids.length})
                      </div>
                      <div className="space-y-1">
                        {set.friend_ids.map((sid) => (
                          <div key={sid} className="flex items-center justify-between rounded px-2 py-1 hover:bg-zinc-800/50">
                            <Link to="/sets/$id" params={{ id: allSets?.items.find((s) => s.id === sid)?.slug ?? sid }} className="text-sm text-zinc-300 hover:text-violet-400">
                              {setName(sid)}
                            </Link>
                            <Button
                              size="sm" variant="ghost"
                              aria-label={`Remove relationship with ${setName(sid)}`}
                              className="h-6 w-6 p-0 text-zinc-500 hover:text-red-400"
                              onClick={() => removeRel.mutate(sid)}
                            >
                              <X className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {set.enemy_ids.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-red-400">
                        <Swords className="h-3.5 w-3.5" /> Enemies ({set.enemy_ids.length})
                      </div>
                      <div className="space-y-1">
                        {set.enemy_ids.map((sid) => (
                          <div key={sid} className="flex items-center justify-between rounded px-2 py-1 hover:bg-zinc-800/50">
                            <Link to="/sets/$id" params={{ id: allSets?.items.find((s) => s.id === sid)?.slug ?? sid }} className="text-sm text-zinc-300 hover:text-violet-400">
                              {setName(sid)}
                            </Link>
                            <Button
                              size="sm" variant="ghost"
                              aria-label={`Remove relationship with ${setName(sid)}`}
                              className="h-6 w-6 p-0 text-zinc-500 hover:text-red-400"
                              onClick={() => removeRel.mutate(sid)}
                            >
                              <X className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-2 border-t border-zinc-800">
                    <p className="mb-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Network</p>
                    <Suspense fallback={<Skeleton className="h-[420px] w-full" />}>
                      <SetRelationshipGraph
                        input={{
                          centerSetId: set.id,
                          centerSetName: set.name,
                          friendIds: set.friend_ids,
                          enemyIds: set.enemy_ids,
                          sets: allSets?.items ?? [],
                        }}
                      />
                    </Suspense>
                    <p className="mt-2 text-center text-[11px] text-zinc-600">
                      Click a set to open it. Pan with drag, zoom with the controls.
                    </p>
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>

          {universe && (
            <SetFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={set}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Set"
            description={`Permanently delete "${set.name}"? This cannot be undone.`}
            impact={(() => {
              const memberCount = membersData?.items.length ?? 0
              const incidentCount = incidentsData?.items.length ?? 0
              const relCount = set.friend_ids.length + set.enemy_ids.length
              if (!memberCount && !incidentCount && !relCount) return null
              const parts: string[] = []
              if (memberCount) parts.push(`${memberCount} member${memberCount === 1 ? '' : 's'}`)
              if (incidentCount) parts.push(`${incidentCount} incident${incidentCount === 1 ? '' : 's'}`)
              if (relCount) parts.push(`${relCount} relationship${relCount === 1 ? '' : 's'}`)
              return <span>{parts.join(', ')} will be unlinked from this set.</span>
            })()}
            confirmLabel="Delete"
            destructive
            pending={deleteSet.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />

          {universe && (
            <AddRelationshipDialog
              setId={set.id}
              universeId={universe.id}
              open={addingRel}
              onClose={() => setAddingRel(false)}
              existingIds={allRelIds}
            />
          )}
        </>
      ) : null}
    </div>
  )
}
