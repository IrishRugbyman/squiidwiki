import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Copy, MapPin, Pencil, Plus, Search, ShieldAlert, Swords, Trash2, Users, X } from 'lucide-react'
import { useMemo, useState, lazy, Suspense } from 'react'
import { toast } from 'sonner'
import {
  useSet, useSetStats, useSets, useDeleteSet,
  useAddSetRelationship, useRemoveSetRelationship,
  useSetMembers, useSetIncidents, useAlliances, useMunicipalities,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { SetStatusBadge, MemberStatusBadge } from '@/components/StatusBadge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { timeAgo } from '@/lib/utils'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Skeleton } from '@/components/ui/skeleton'
import { SetAvatar, SetFormSheet } from './_app.sets.index'
import { MemberAvatar, MemberFormSheet } from './_app.members.index'
import { AddMemberToSetDialog } from '@/components/AddMemberToSetDialog'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'
import { INCIDENT_TYPE_CHIP } from '@/lib/incidentColors'
import type { IncidentListItem, MemberListItem } from '@/lib/types'

const SetRelationshipGraph = lazy(() =>
  import('@/components/graphs/SetRelationshipGraph').then((m) => ({ default: m.SetRelationshipGraph })),
)
const PhotoGallery = lazy(() =>
  import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })),
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

// Sortable column key from a FuzzyDate. Missing dates sort last.
function fuzzyDateSortKey(d: FuzzyDateValue | null | undefined): string {
  if (!d || !d.year) return '￿'
  const y = String(d.year).padStart(4, '0')
  const m = String(d.month ?? 1).padStart(2, '0')
  const day = String(d.day ?? 1).padStart(2, '0')
  return `${y}-${m}-${day}`
}

type SortDir = 'asc' | 'desc'

function SortHeader<K extends string>({
  label, col, sortKey, sortDir, onSort, className,
}: {
  label: string
  col: K
  sortKey: K
  sortDir: SortDir
  onSort: (k: K) => void
  className?: string
}) {
  const sorted = sortKey === col
  return (
    <th
      scope="col"
      aria-sort={sorted ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
      className={`px-4 py-2.5 text-left ${className ?? ''}`}
    >
      <button
        type="button"
        onClick={() => onSort(col)}
        className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white"
      >
        {label}
        <span className="text-zinc-600" aria-hidden>
          {sorted ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
        </span>
      </button>
    </th>
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
  const { data: munisData } = useMunicipalities(universe?.id ?? null)

  useRecordRecent(set ? { type: 'set', id: set.id, slug: set.slug, label: set.name } : null)

  const deleteSet = useDeleteSet(universe?.id ?? '')
  const removeRel = useRemoveSetRelationship(realId, universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [duplicating, setDuplicating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [addingRel, setAddingRel] = useState(false)
  const [addingMember, setAddingMember] = useState(false)
  const [creatingMember, setCreatingMember] = useState(false)

  // Members tab state
  const [memberQuery, setMemberQuery] = useState('')
  const [memberSortKey, setMemberSortKey] = useState<'name' | 'status' | 'date_of_death'>('name')
  const [memberSortDir, setMemberSortDir] = useState<SortDir>('asc')

  // Incidents tab state
  const [incSortKey, setIncSortKey] = useState<'date' | 'type'>('date')
  const [incSortDir, setIncSortDir] = useState<SortDir>('desc')

  useEditShortcut(() => set && setEditing(true))

  const muniMap: Record<string, { name: string }> = {}
  for (const m of munisData?.items ?? []) muniMap[m.id] = { name: m.name }

  const setMap: Record<string, { name: string; slug: string | null }> = {}
  for (const s of allSets?.items ?? []) setMap[s.id] = { name: s.name, slug: s.slug }
  const setName = (sid: string) => setMap[sid]?.name ?? sid

  const alliance = set?.alliance_id
    ? (alliancesData?.items ?? []).find((a) => a.id === set.alliance_id) ?? null
    : null
  const muni = set?.municipality_id ? muniMap[set.municipality_id] : null
  const territoryNames = (set?.territory_ids ?? [])
    .map((tid) => muniMap[tid]?.name)
    .filter((n): n is string => !!n)
    .sort((a, b) => a.localeCompare(b))

  const allRelIds = set ? [...set.friend_ids, ...set.enemy_ids] : []
  const hasRelationships = set ? set.friend_ids.length + set.enemy_ids.length > 0 : false

  const memberItems: MemberListItem[] = membersData?.items ?? []
  const incidentItems: IncidentListItem[] = incidentsData?.items ?? []

  // Filter + sort members. Default = alphabetical by display_name.
  const filteredMembers = useMemo(() => {
    const q = memberQuery.trim().toLowerCase()
    let rows = memberItems
    if (q) {
      rows = rows.filter((m) => {
        if (m.display_name.toLowerCase().includes(q)) return true
        if (m.aliases?.some((a) => a.toLowerCase().includes(q))) return true
        return false
      })
    }
    const dir = memberSortDir === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      let cmp = 0
      if (memberSortKey === 'name') {
        cmp = a.display_name.localeCompare(b.display_name)
      } else if (memberSortKey === 'status') {
        cmp = a.status.localeCompare(b.status)
      } else {
        cmp = fuzzyDateSortKey(a.date_of_death).localeCompare(fuzzyDateSortKey(b.date_of_death))
      }
      if (cmp === 0) cmp = a.display_name.localeCompare(b.display_name)
      return cmp * dir
    })
  }, [memberItems, memberQuery, memberSortKey, memberSortDir])

  // Sort incidents. Default = most recent first.
  const sortedIncidents = useMemo(() => {
    const dir = incSortDir === 'asc' ? 1 : -1
    return [...incidentItems].sort((a, b) => {
      let cmp = 0
      if (incSortKey === 'date') {
        cmp = fuzzyDateSortKey(a.date).localeCompare(fuzzyDateSortKey(b.date))
      } else {
        cmp = a.type.localeCompare(b.type)
      }
      if (cmp === 0) cmp = fuzzyDateSortKey(a.date).localeCompare(fuzzyDateSortKey(b.date))
      return cmp * dir
    })
  }, [incidentItems, incSortKey, incSortDir])

  function toggleMemberSort(k: 'name' | 'status' | 'date_of_death') {
    if (memberSortKey === k) setMemberSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setMemberSortKey(k); setMemberSortDir(k === 'date_of_death' ? 'desc' : 'asc') }
  }
  function toggleIncSort(k: 'date' | 'type') {
    if (incSortKey === k) setIncSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setIncSortKey(k); setIncSortDir(k === 'date' ? 'desc' : 'asc') }
  }

  // Sorted relationships (alphabetical by name, unknown ids last)
  const sortedFriendIds = (set?.friend_ids ?? [])
    .slice()
    .sort((a, b) => setName(a).localeCompare(setName(b)))
  const sortedEnemyIds = (set?.enemy_ids ?? [])
    .slice()
    .sort((a, b) => setName(a).localeCompare(setName(b)))

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
              <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} size="md" isReserved={set.is_reserved} />
              <div>
                <div className="flex items-center gap-1.5">
                  <h1 className="text-2xl font-bold text-white">{set.name}</h1>
                  <CopyButton value={window.location.href} label="Copy link to this set" className="opacity-60 hover:opacity-100" />
                </div>
                {set.aliases && set.aliases.length > 0 && (
                  <p className="text-sm text-zinc-400">a/k/a {set.aliases.join(', ')}</p>
                )}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <SetStatusBadge status={set.status} />
                  {set.is_reserved && (
                    <span className="inline-flex items-center rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-400">
                      System
                    </span>
                  )}
                  {!set.is_reserved && alliance && (
                    <Link
                      to="/alliances/$id"
                      params={{ id: alliance.slug ?? alliance.id }}
                      className="inline-flex items-center gap-1 rounded-full border border-violet-700/50 bg-violet-950/30 px-2 py-0.5 text-xs font-medium text-violet-300 hover:text-violet-200 transition-colors"
                    >
                      {alliance.name}
                    </Link>
                  )}
                  {!set.is_reserved && muni && set.municipality_id && (
                    <Link
                      to="/municipalities/$id"
                      params={{ id: set.municipality_id }}
                      className="inline-flex items-center gap-1 rounded-full border border-zinc-800 bg-zinc-900/50 px-2 py-0.5 text-xs text-zinc-400 hover:border-zinc-700 hover:text-zinc-200 transition-colors"
                    >
                      <MapPin className="h-3 w-3" />
                      {muni.name}
                    </Link>
                  )}
                  {!set.is_reserved && territoryNames.length > 0 && (
                    <span
                      className="inline-flex items-center gap-1 rounded-full border border-zinc-800 bg-zinc-900/50 px-2 py-0.5 text-xs text-zinc-500"
                      title={territoryNames.join(', ')}
                    >
                      {territoryNames.length} sub-district{territoryNames.length === 1 ? '' : 's'}
                    </span>
                  )}
                  <span className="text-[11px] text-zinc-600">Updated {timeAgo(set.updated_at)}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
              </Button>
              {!set.is_reserved && (
                <Button size="sm" variant="outline" onClick={() => setDuplicating(true)}>
                  <Copy className="mr-1.5 h-3.5 w-3.5" />Duplicate
                </Button>
              )}
              {user?.global_role === 'ADMIN' && !set.is_reserved && (
                <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
                </Button>
              )}
            </div>
          </div>

          {set.bio && (
            <p className="mb-4 text-sm text-zinc-400 leading-relaxed max-w-2xl">{set.bio}</p>
          )}

          {set.is_reserved && (
            <div className="mb-4 rounded-lg border border-zinc-700 bg-zinc-900/50 px-4 py-3 text-sm text-zinc-400">
              <span className="font-medium text-zinc-300">System set.</span>{' '}
              Used for incident attribution when the actor is a {set.name.toLowerCase()} (not a real crew).
              Only the bio can be edited; this set cannot be renamed, reassigned, or deleted.
            </div>
          )}

          {!set.is_reserved && stats && (
            <div className="mb-6 grid grid-cols-5 gap-2">
              <StatPill label="Members" value={stats.member_count} />
              <StatPill label="Dead" value={stats.dead_members} accent="text-zinc-400" />
              <StatPill label="Shootings" value={stats.total_shootings} accent="text-amber-400" />
              <StatPill label="Assists" value={stats.total_assists} accent="text-violet-400" />
              <StatPill label="Kills" value={stats.total_kills} accent="text-rose-400" />
            </div>
          )}

          <Tabs defaultValue={set.is_reserved ? 'incidents' : 'members'}>
            <TabsList>
              {!set.is_reserved && (
                <TabsTrigger value="members">
                  Members
                  {membersData && membersData.items.length > 0 && (
                    <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{membersData.items.length}</Badge>
                  )}
                </TabsTrigger>
              )}
              <TabsTrigger value="incidents">
                Incidents
                {incidentsData && incidentsData.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incidentsData.items.length}</Badge>
                )}
              </TabsTrigger>
              {!set.is_reserved && (
                <TabsTrigger value="relationships">
                  Relationships
                  {hasRelationships && (
                    <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">
                      {set.friend_ids.length + set.enemy_ids.length}
                    </Badge>
                  )}
                </TabsTrigger>
              )}
              {!set.is_reserved && <TabsTrigger value="photos">Photos</TabsTrigger>}
            </TabsList>

            {!set.is_reserved && <TabsContent value="members" className="mt-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                {memberItems.length > 5 && (
                  <div className="relative max-w-xs flex-1">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
                    <Input
                      className="h-8 pl-8 text-sm"
                      placeholder="Filter by name or alias…"
                      value={memberQuery}
                      onChange={(e) => setMemberQuery(e.target.value)}
                    />
                  </div>
                )}
                <span className="text-xs text-zinc-500 tabular-nums">
                  {filteredMembers.length === memberItems.length
                    ? `${memberItems.length} member${memberItems.length === 1 ? '' : 's'}`
                    : `${filteredMembers.length} of ${memberItems.length}`}
                </span>
                <Button size="sm" variant="outline" className="ml-auto" onClick={() => setAddingMember(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Member
                </Button>
              </div>
              {memberItems.length === 0 ? (
                <EmptyState
                  icon={Users}
                  title="No members in this set"
                  description="Add an existing member, or create a new one to get started."
                  action={
                    <Button size="sm" onClick={() => setAddingMember(true)}>
                      <Plus className="mr-1.5 h-4 w-4" /> Add the first member
                    </Button>
                  }
                />
              ) : filteredMembers.length === 0 ? (
                <EmptyState
                  icon={Search}
                  title={`No members match "${memberQuery}"`}
                  description="Try a different name or alias."
                />
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th scope="col" className="w-10 px-3 py-2.5" aria-label="Photo" />
                        <SortHeader<'name' | 'status' | 'date_of_death'>
                          label="Name" col="name"
                          sortKey={memberSortKey} sortDir={memberSortDir} onSort={toggleMemberSort}
                        />
                        <SortHeader<'name' | 'status' | 'date_of_death'>
                          label="Status" col="status"
                          sortKey={memberSortKey} sortDir={memberSortDir} onSort={toggleMemberSort}
                        />
                        <SortHeader<'name' | 'status' | 'date_of_death'>
                          label="Date of Death" col="date_of_death"
                          className="hidden md:table-cell"
                          sortKey={memberSortKey} sortDir={memberSortDir} onSort={toggleMemberSort}
                        />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {filteredMembers.map((m) => {
                        const isDead = m.status === 'DEAD'
                        const linkId = m.slug ?? m.id
                        return (
                          <tr key={m.id} className={`group hover:bg-zinc-900/50 transition-colors ${isDead ? 'opacity-60' : ''}`}>
                            <td className="px-3 py-3"><MemberAvatar member={m} /></td>
                            <td className="p-0">
                              <Link
                                to="/members/$id"
                                params={{ id: linkId }}
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
                            <td className="p-0">
                              <Link to="/members/$id" params={{ id: linkId }} className="block px-4 py-3" tabIndex={-1}>
                                <MemberStatusBadge status={m.status} />
                              </Link>
                            </td>
                            <td className="hidden p-0 md:table-cell">
                              <Link to="/members/$id" params={{ id: linkId }} className="block px-4 py-3 text-xs text-zinc-500" tabIndex={-1}>
                                {m.date_of_death ? <FuzzyDate value={m.date_of_death} /> : <span className="text-zinc-700">—</span>}
                              </Link>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>}

            <TabsContent value="incidents" className="mt-4">
              {incidentItems.length === 0 ? (
                <EmptyState
                  icon={ShieldAlert}
                  title="No incidents recorded"
                  description="Incidents involving members of this set will appear here."
                />
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <SortHeader<'date' | 'type'>
                          label="Type" col="type"
                          sortKey={incSortKey} sortDir={incSortDir} onSort={toggleIncSort}
                        />
                        <SortHeader<'date' | 'type'>
                          label="Date" col="date"
                          sortKey={incSortKey} sortDir={incSortDir} onSort={toggleIncSort}
                        />
                        <th scope="col" className="hidden px-4 py-2.5 text-left text-xs font-medium text-zinc-400 md:table-cell">Location</th>
                        <th scope="col" className="hidden px-4 py-2.5 text-left text-xs font-medium text-zinc-400 lg:table-cell">Victims</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {sortedIncidents.map((inc) => {
                        const muniName = inc.municipality_id ? muniMap[inc.municipality_id]?.name : null
                        return (
                          <tr key={inc.id} className="group hover:bg-zinc-900/50 transition-colors">
                            <td className="p-0">
                              <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3">
                                <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${INCIDENT_TYPE_CHIP[inc.type]}`}>
                                  {inc.type}
                                </span>
                              </Link>
                            </td>
                            <td className="p-0">
                              <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 font-mono text-xs text-zinc-400 tabular-nums" tabIndex={-1}>
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

            {!set.is_reserved && <TabsContent value="relationships" className="mt-4">
              <div className="mb-3 flex justify-end">
                <Button size="sm" variant="outline" onClick={() => setAddingRel(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Relationship
                </Button>
              </div>
              {!hasRelationships ? (
                <p className="text-sm text-zinc-600">No relationships recorded.</p>
              ) : (
                <div className="space-y-4">
                  {sortedFriendIds.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                        <Users className="h-3.5 w-3.5" /> Allies ({sortedFriendIds.length})
                      </div>
                      <div className="space-y-1">
                        {sortedFriendIds.map((sid) => (
                          <div key={sid} className="flex items-center justify-between rounded px-2 py-1 hover:bg-zinc-800/50">
                            <Link to="/sets/$id" params={{ id: setMap[sid]?.slug ?? sid }} className="text-sm text-zinc-300 hover:text-violet-400">
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
                  {sortedEnemyIds.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-red-400">
                        <Swords className="h-3.5 w-3.5" /> Enemies ({sortedEnemyIds.length})
                      </div>
                      <div className="space-y-1">
                        {sortedEnemyIds.map((sid) => (
                          <div key={sid} className="flex items-center justify-between rounded px-2 py-1 hover:bg-zinc-800/50">
                            <Link to="/sets/$id" params={{ id: setMap[sid]?.slug ?? sid }} className="text-sm text-zinc-300 hover:text-violet-400">
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
            </TabsContent>}

            {!set.is_reserved && (
              <TabsContent value="photos" className="mt-4">
                {universe && (
                  <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                    <PhotoGallery entityType="set" entityId={set.id} universeId={universe.id} />
                  </Suspense>
                )}
              </TabsContent>
            )}
          </Tabs>

          {universe && (
            <SetFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={set}
            />
          )}

          {universe && duplicating && (
            <SetFormSheet
              key={`dup-${set.id}`}
              universeId={universe.id}
              open={duplicating}
              onClose={() => setDuplicating(false)}
              copyFrom={{ ...set, name: `${set.name} (copy)` }}
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

          {!set.is_reserved && universe && (
            <AddRelationshipDialog
              setId={set.id}
              universeId={universe.id}
              open={addingRel}
              onClose={() => setAddingRel(false)}
              existingIds={allRelIds}
            />
          )}

          {!set.is_reserved && universe && (
            <AddMemberToSetDialog
              setId={set.id}
              setName={set.name}
              universeId={universe.id}
              open={addingMember}
              onClose={() => setAddingMember(false)}
              onCreateNew={() => { setAddingMember(false); setCreatingMember(true) }}
            />
          )}

          {!set.is_reserved && universe && (
            <MemberFormSheet
              universeId={universe.id}
              open={creatingMember}
              onClose={() => setCreatingMember(false)}
              defaultSetId={set.id}
            />
          )}
        </>
      ) : null}
    </div>
  )
}
