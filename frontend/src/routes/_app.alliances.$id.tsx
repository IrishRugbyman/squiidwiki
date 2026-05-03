import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Network, Pencil, Plus, ShieldAlert, Skull, Trash2, Users, X } from 'lucide-react'
import { lazy, Suspense, useMemo, useState } from 'react'
import { Skeleton } from '@/components/ui/skeleton'

const AllianceRelationshipGraph = lazy(() =>
  import('@/components/graphs/AllianceRelationshipGraph').then((m) => ({ default: m.AllianceRelationshipGraph })),
)
const PhotoGallery = lazy(() =>
  import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })),
)
import { toast } from 'sonner'
import { FuzzyDate } from '@/components/FuzzyDate'
import { AllianceStatusBadge, MemberStatusBadge, SetStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { timeAgo } from '@/lib/utils'
import { EmptyState } from '@/components/EmptyState'
import { StatCard } from '@/components/StatCard'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  useAlliance, useSets, useDeleteAlliance, useAllianceMembers,
  useAllianceIncidents, useUpdateSet, useMunicipalities,
} from '@/lib/queries'
import type { SetListItem } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { AllianceFormSheet } from './_app.alliances.index'
import { SetAvatar, SetFormSheet } from './_app.sets.index'
import { MemberAvatar, MemberFormSheet } from './_app.members.index'
import { AddSetToAllianceDialog } from '@/components/AddSetToAllianceDialog'
import { AddMemberToAllianceDialog } from '@/components/AddMemberToAllianceDialog'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'

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
  const { data: munis } = useMunicipalities(universe?.id ?? null)
  const deleteAlliance = useDeleteAlliance(universe?.id ?? '')

  useRecordRecent(alliance ? { type: 'alliance', id: alliance.id, slug: alliance.slug, label: alliance.name } : null)

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [addingSet, setAddingSet] = useState(false)
  const [creatingSet, setCreatingSet] = useState(false)
  const [addingMember, setAddingMember] = useState(false)
  const [creatingMember, setCreatingMember] = useState(false)
  const [removingSetId, setRemovingSetId] = useState<string | null>(null)
  const [setsView, setSetsView] = useState<'list' | 'graph'>('list')

  useEditShortcut(() => alliance && setEditing(true))

  const muniMap: Record<string, string> = {}
  for (const m of munis?.items ?? []) muniMap[m.id] = m.name

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

  const setIds = alliance?.set_ids ?? []
  const allianceSets: SetListItem[] = (allSets?.items ?? []).filter((s) => setIds.includes(s.id))
  const memberItems = members?.items ?? []
  const incidentItems = incidents?.items ?? []
  const deadCount = memberItems.filter((m) => m.status === 'DEAD').length
  const memberCountBySetId = useMemo(() => {
    const m: Record<string, number> = {}
    for (const x of memberItems) {
      if (x.set_id) m[x.set_id] = (m[x.set_id] ?? 0) + 1
    }
    return m
  }, [memberItems])
  const removingSet = removingSetId ? allianceSets.find((s) => s.id === removingSetId) : null

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
          {/* Hero */}
          <div className="mb-5 flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="shrink-0">
                {alliance.primary_photo_url ? (
                  <img
                    src={alliance.primary_photo_url}
                    alt={`Photo of ${alliance.name}`}
                    loading="lazy"
                    decoding="async"
                    className="h-20 w-20 rounded-xl object-cover ring-1 ring-zinc-600/80 shadow-lg shadow-black/30"
                  />
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-zinc-800 text-2xl font-bold text-zinc-400 ring-1 ring-zinc-700">
                    {alliance.name.slice(0, 2).toUpperCase()}
                  </div>
                )}
              </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h1 className="text-2xl font-bold text-white">{alliance.name}</h1>
                <CopyButton value={window.location.href} label="Copy link to this alliance" className="opacity-60 hover:opacity-100" />
              </div>
              {alliance.aliases && alliance.aliases.length > 0 && (
                <p className="text-sm text-zinc-400">a/k/a {alliance.aliases.join(', ')}</p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <AllianceStatusBadge status={alliance.status} />
                {alliance.founded_at && (
                  <span className="inline-flex items-center rounded-full border border-zinc-800 bg-zinc-900/50 px-2 py-0.5 text-[11px] text-zinc-400">
                    Founded&nbsp;<FuzzyDate value={alliance.founded_at} />
                  </span>
                )}
                <span className="text-[11px] text-zinc-600">Updated {timeAgo(alliance.updated_at)}</span>
              </div>
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

          {/* Stat strip */}
          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard icon={Network} label="Sets" value={setIds.length} accent="violet" />
            <StatCard icon={Users} label="Members" value={memberItems.length} accent="default" />
            <StatCard icon={Skull} label="Dead" value={deadCount} accent="red" />
            <StatCard icon={ShieldAlert} label="Incidents" value={incidentItems.length} accent="amber" />
          </div>

          {/* Description */}
          {alliance.description && (
            <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-950 p-4">
              <p className="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap">{alliance.description}</p>
            </div>
          )}

          <Tabs defaultValue="sets">
            <TabsList>
              <TabsTrigger value="sets">
                Sets
                {setIds.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{setIds.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="members">
                Members
                {memberItems.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{memberItems.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="incidents">
                Incidents
                {incidentItems.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incidentItems.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="photos">Photos</TabsTrigger>
            </TabsList>

            {/* Sets */}
            <TabsContent value="sets" className="mt-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <div className="flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-900/60 p-1">
                  {(['list', 'graph'] as const).map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => setSetsView(v)}
                      className={`rounded px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                        setsView === v ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'
                      }`}
                    >
                      {v === 'list' ? 'List' : 'Graph'}
                    </button>
                  ))}
                </div>
                <Button size="sm" variant="outline" onClick={() => setAddingSet(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Set
                </Button>
              </div>
              {setsView === 'graph' && setIds.length > 0 && universe && (
                <Suspense fallback={<Skeleton className="h-[480px] w-full" />}>
                  <AllianceRelationshipGraph
                    allianceSets={allianceSets}
                    allSets={allSets?.items ?? []}
                    memberCountBySetId={memberCountBySetId}
                    universeId={universe.id}
                  />
                </Suspense>
              )}
              {setsView === 'list' && (setIds.length === 0 ? (
                <EmptyState
                  icon={Network}
                  title="No member sets yet"
                  description="Attach existing sets, or create one within this alliance."
                  action={
                    <Button size="sm" onClick={() => setAddingSet(true)}>
                      <Plus className="mr-1.5 h-4 w-4" /> Add the first set
                    </Button>
                  }
                />
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th scope="col" className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Set</th>
                        <th scope="col" className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Status</th>
                        <th scope="col" className="px-4 py-2.5 text-right text-xs font-medium text-zinc-400">Members</th>
                        <th scope="col" className="w-10" aria-label="Actions" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {allianceSets.map((s) => {
                        const memberCount = memberItems.filter((m) => m.set_id === s.id).length
                        return (
                          <AllianceSetRow
                            key={s.id}
                            set={s}
                            memberCount={memberCount}
                            universeId={universe!.id}
                            onRequestRemove={() => setRemovingSetId(s.id)}
                          />
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ))}
            </TabsContent>

            {/* Members */}
            <TabsContent value="members" className="mt-4">
              <div className="mb-3 flex justify-end">
                <Button size="sm" variant="outline" onClick={() => setAddingMember(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Member
                </Button>
              </div>
              {memberItems.length === 0 ? (
                <EmptyState
                  icon={Users}
                  title="No members in this alliance"
                  description="Add members directly, or attach sets above and their members will appear here."
                  action={
                    <Button size="sm" onClick={() => setAddingMember(true)}>
                      <Plus className="mr-1.5 h-4 w-4" /> Add the first member
                    </Button>
                  }
                />
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th scope="col" className="w-10 px-3 py-2.5" aria-label="Photo" />
                        <th scope="col" className="px-3 py-2.5 text-left text-xs font-medium text-zinc-400">Name</th>
                        <th scope="col" className="hidden px-3 py-2.5 text-left text-xs font-medium text-zinc-400 sm:table-cell">Set</th>
                        <th scope="col" className="px-3 py-2.5 text-left text-xs font-medium text-zinc-400">Status</th>
                        <th scope="col" className="hidden px-3 py-2.5 text-left text-xs font-medium text-zinc-400 md:table-cell">Date of Death</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {memberItems.map((m) => {
                        const setInfo = m.set_id ? allianceSets.find((s) => s.id === m.set_id) : null
                        const isDead = m.status === 'DEAD'
                        return (
                          <tr key={m.id} className={`group hover:bg-zinc-900/40 transition-colors ${isDead ? 'opacity-60' : ''}`}>
                            <td className="px-3 py-3"><MemberAvatar member={m} /></td>
                            <td className="p-0">
                              <Link
                                to="/members/$id"
                                params={{ id: m.slug ?? m.id }}
                                className="block px-3 py-3 transition-colors group-hover:text-violet-400"
                              >
                                <span className={`font-medium ${isDead ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'}`}>
                                  {m.display_name}
                                </span>
                                {m.aliases && m.aliases.length > 0 && (
                                  <span className="mt-0.5 block text-[11px] text-zinc-600 group-hover:text-zinc-500 transition-colors">
                                    {m.aliases.slice(0, 3).join(' · ')}
                                  </span>
                                )}
                              </Link>
                            </td>
                            <td className="hidden px-3 py-3 sm:table-cell">
                              {setInfo ? (
                                <Link
                                  to="/sets/$id"
                                  params={{ id: setInfo.slug ?? setInfo.id }}
                                  className="inline-flex items-center rounded-full bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors"
                                >
                                  {setInfo.name}
                                </Link>
                              ) : (
                                <span className="text-xs text-zinc-700">—</span>
                              )}
                            </td>
                            <td className="px-3 py-3"><MemberStatusBadge status={m.status} /></td>
                            <td className="hidden px-3 py-3 text-xs text-zinc-500 md:table-cell">
                              {m.date_of_death ? <FuzzyDate value={m.date_of_death} /> : <span className="text-zinc-700">—</span>}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            {/* Incidents */}
            <TabsContent value="incidents" className="mt-4">
              {incidentItems.length === 0 ? (
                <EmptyState
                  icon={ShieldAlert}
                  title="No incidents involving this alliance"
                  description="Incidents involving any member of this alliance will appear here."
                />
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th scope="col" className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Type</th>
                        <th scope="col" className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Date</th>
                        <th scope="col" className="hidden px-4 py-2.5 text-left text-xs font-medium text-zinc-400 md:table-cell">Location</th>
                        <th scope="col" className="hidden px-4 py-2.5 text-left text-xs font-medium text-zinc-400 lg:table-cell">Victims</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {incidentItems.map((inc) => {
                        const muniName = inc.municipality_id ? muniMap[inc.municipality_id] : null
                        return (
                          <tr key={inc.id} className="group hover:bg-zinc-900/40 transition-colors">
                            <td className="p-0">
                              <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3">
                                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                  inc.type === 'MURDER'
                                    ? 'bg-rose-950/60 text-rose-300 ring-1 ring-rose-800/50'
                                    : 'bg-amber-950/60 text-amber-300 ring-1 ring-amber-800/50'
                                }`}>
                                  {inc.type}
                                </span>
                              </Link>
                            </td>
                            <td className="p-0">
                              <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 font-mono text-xs text-zinc-400 tabular-nums">
                                {inc.date ? <FuzzyDate value={inc.date} /> : <span className="text-zinc-700">Unknown</span>}
                              </Link>
                            </td>
                            <td className="hidden p-0 md:table-cell">
                              <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-xs text-zinc-500" tabIndex={-1}>
                                {muniName ?? <span className="text-zinc-700">—</span>}
                              </Link>
                            </td>
                            <td className="hidden p-0 lg:table-cell">
                              <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-xs text-zinc-400" tabIndex={-1}>
                                {inc.victim_names.length > 0 ? (
                                  <span className="truncate max-w-xs inline-block align-bottom">
                                    {inc.victim_names.slice(0, 3).join(', ')}
                                    {inc.victim_names.length > 3 && ` +${inc.victim_names.length - 3}`}
                                  </span>
                                ) : (
                                  <span className="text-zinc-700">—</span>
                                )}
                              </Link>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="photos" className="mt-4">
              {universe && (
                <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                  <PhotoGallery entityType="alliance" entityId={alliance.id} universeId={universe.id} />
                </Suspense>
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

          {universe && (
            <>
              <AddSetToAllianceDialog
                allianceId={alliance.id}
                allianceName={alliance.name}
                universeId={universe.id}
                currentSetIds={setIds}
                open={addingSet}
                onClose={() => setAddingSet(false)}
                onCreateNew={() => { setAddingSet(false); setCreatingSet(true) }}
              />
              <SetFormSheet
                universeId={universe.id}
                open={creatingSet}
                onClose={() => setCreatingSet(false)}
                defaultAllianceId={alliance.id}
              />
              <AddMemberToAllianceDialog
                allianceId={alliance.id}
                allianceName={alliance.name}
                universeId={universe.id}
                open={addingMember}
                onClose={() => setAddingMember(false)}
                onCreateNew={() => { setAddingMember(false); setCreatingMember(true) }}
              />
              <MemberFormSheet
                universeId={universe.id}
                open={creatingMember}
                onClose={() => setCreatingMember(false)}
                defaultAllianceId={alliance.id}
              />
            </>
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Alliance"
            description={`Permanently delete "${alliance.name}"? This cannot be undone.`}
            impact={(() => {
              const setCount = setIds.length
              const memberCount = memberItems.length
              const incidentCount = incidentItems.length
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

          {removingSet && universe && (
            <RemoveSetConfirm
              set={removingSet}
              universeId={universe.id}
              memberCount={memberItems.filter((m) => m.set_id === removingSet.id).length}
              onClose={() => setRemovingSetId(null)}
            />
          )}
        </>
      ) : null}
    </div>
  )
}

// ─── Sub-components ──────────────────────────────────────────────────────────

interface AllianceSetRowProps {
  set: SetListItem
  memberCount: number
  universeId: string
  onRequestRemove: () => void
}

function AllianceSetRow({ set, memberCount, onRequestRemove }: AllianceSetRowProps) {
  const linkId = set.slug ?? set.id
  return (
    <tr className="group hover:bg-zinc-900/40 transition-colors">
      <td className="p-0">
        <Link
          to="/sets/$id"
          params={{ id: linkId }}
          className="flex items-center gap-3 px-4 py-3"
        >
          <SetAvatar name={set.name} size="sm" />
          <div className="min-w-0">
            <p className="font-medium text-white group-hover:text-violet-400 transition-colors">{set.name}</p>
            {set.aliases && set.aliases.length > 0 && (
              <p className="text-xs text-zinc-500">{set.aliases.join(' · ')}</p>
            )}
          </div>
        </Link>
      </td>
      <td className="px-4 py-3"><SetStatusBadge status={set.status} /></td>
      <td className="px-4 py-3 text-right text-xs text-zinc-400 tabular-nums">{memberCount}</td>
      <td className="px-2 py-3 text-right">
        <Button
          variant="ghost"
          size="sm"
          aria-label={`Remove ${set.name} from alliance`}
          className="h-7 w-7 p-0 text-zinc-500 opacity-0 hover:bg-red-950/40 hover:text-red-400 group-hover:opacity-100 focus:opacity-100"
          onClick={onRequestRemove}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </td>
    </tr>
  )
}

interface RemoveSetConfirmProps {
  set: SetListItem
  universeId: string
  memberCount: number
  onClose: () => void
}

function RemoveSetConfirm({ set, universeId, memberCount, onClose }: RemoveSetConfirmProps) {
  const update = useUpdateSet(set.id)

  async function handleConfirm() {
    try {
      await update.mutateAsync({ universe_id: universeId, alliance_id: null })
      toast.success(`Removed "${set.name}" from alliance`)
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to remove set from alliance')
    }
  }

  return (
    <ConfirmDialog
      open
      title="Remove set from alliance"
      description={`Detach "${set.name}" from this alliance? The set itself will not be deleted.`}
      impact={memberCount > 0 ? <span>{memberCount} member{memberCount === 1 ? '' : 's'} will lose the alliance link.</span> : null}
      confirmLabel="Remove"
      destructive
      pending={update.isPending}
      onConfirm={handleConfirm}
      onCancel={onClose}
    />
  )
}
