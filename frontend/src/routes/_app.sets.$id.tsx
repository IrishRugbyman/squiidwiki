import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Copy, Download, GitFork, MapPin, Pencil, Plus, Search, ShieldAlert, Swords, Trash2, Users, X } from 'lucide-react'
import { useMemo, useState, lazy, Suspense } from 'react'
import { toast } from 'sonner'
import {
  useSet, useSetStats, useSets, useDeleteSet, useUpdateSet,
  useAddSetRelationship, useRemoveSetRelationship,
  useSetMembers, useSetIncidents, useAlliances, useMunicipalities,
  useAllMembers,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { SetStatusBadge, MemberStatusBadge } from '@/components/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { timeAgo } from '@/lib/utils'
import { downloadText } from '@/lib/download'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Skeleton } from '@/components/ui/skeleton'
import { SetFormSheet } from './_app.sets.index'
import { MemberAvatar, MemberFormSheet } from './_app.members.index'
import { AddMemberToSetDialog } from '@/components/AddMemberToSetDialog'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'
import { INCIDENT_TYPE_CHIP } from '@/lib/incidentColors'
import type { IncidentListItem, MemberListItem, SetReadDetail } from '@/lib/types'

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
    <div className="flex flex-col items-center rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <span className={`text-2xl font-bold tabular-nums ${accent}`}>{value}</span>
      <span className="mt-0.5 text-[11px] text-zinc-500">{label}</span>
    </div>
  )
}

function DetailRow({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-4 border-b border-zinc-800/70 py-2.5 last:border-0">
      <span className="w-32 shrink-0 text-xs text-zinc-500">{label}</span>
      <span className="text-sm text-zinc-200">{children}</span>
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

const MD_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatFuzzyDateText(value: FuzzyDateValue | null | undefined, fallback = 'Unknown'): string {
  if (!value || value.precision === 'UNKNOWN') return fallback
  const prefix = value.approx ? 'c. ' : ''
  if (value.precision === 'YMD' && value.year && value.month && value.day)
    return `${prefix}${MD_MONTHS[value.month - 1]} ${value.day}, ${value.year}`
  if (value.precision === 'YM' && value.year && value.month)
    return `${prefix}${MD_MONTHS[value.month - 1]} ${value.year}`
  if (value.precision === 'Y' && value.year)
    return `${prefix}${value.year}`
  return fallback
}

function buildSetMarkdown({
  set, allianceName, muniName, founderName, territoryNames, members, incidents, friends, enemies,
}: {
  set: SetReadDetail
  allianceName: string | null
  muniName: string | null
  founderName: string | null
  territoryNames: string[]
  members: MemberListItem[]
  incidents: IncidentListItem[]
  friends: string[]
  enemies: string[]
}): string {
  const lines: string[] = []
  lines.push(`# ${set.name}`)
  if (set.aliases && set.aliases.length > 0) {
    lines.push('')
    lines.push(`*a/k/a ${set.aliases.join(', ')}*`)
  }
  lines.push('')

  lines.push('## Identity')
  lines.push('')
  lines.push(`- **Status:** ${set.status}`)
  if (allianceName) lines.push(`- **Alliance:** ${allianceName}`)
  if (muniName) lines.push(`- **Municipality:** ${muniName}`)
  if (founderName) lines.push(`- **Founder:** ${founderName}`)
  if (territoryNames.length > 0) lines.push(`- **Territories:** ${territoryNames.join(', ')}`)
  lines.push(`- **Created:** ${new Date(set.created_at).toISOString().slice(0, 10)}`)
  lines.push(`- **Updated:** ${new Date(set.updated_at).toISOString().slice(0, 10)}`)
  lines.push('')

  if (set.bio) {
    lines.push('## Biography')
    lines.push('')
    lines.push(set.bio)
    lines.push('')
  }

  if (members.length > 0) {
    lines.push(`## Members (${members.length})`)
    lines.push('')
    for (const m of members) {
      const dod = m.date_of_death ? ` — †${formatFuzzyDateText(m.date_of_death)}` : ''
      lines.push(`- ${m.display_name} (${m.status})${dod}`)
    }
    lines.push('')
  }

  if (incidents.length > 0) {
    const recent = [...incidents]
      .sort((a, b) => fuzzyDateSortKey(b.date).localeCompare(fuzzyDateSortKey(a.date)))
      .slice(0, 10)
    lines.push(`## Recent Incidents (${recent.length} of ${incidents.length})`)
    lines.push('')
    for (const inc of recent) {
      const dateStr = formatFuzzyDateText(inc.date, 'Date unknown')
      const victims = inc.victim_names.length > 0 ? ` — Victims: ${inc.victim_names.join(', ')}` : ''
      lines.push(`- ${dateStr} — ${inc.type}${victims}`)
    }
    lines.push('')
  }

  if (friends.length > 0) {
    lines.push(`## Allies (${friends.length})`)
    lines.push('')
    for (const name of friends) lines.push(`- ${name}`)
    lines.push('')
  }
  if (enemies.length > 0) {
    lines.push(`## Enemies (${enemies.length})`)
    lines.push('')
    for (const name of enemies) lines.push(`- ${name}`)
    lines.push('')
  }

  return lines.join('\n').trimEnd() + '\n'
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

// ─── Relationships side panel ─────────────────────────────────────────────────

function RelationshipsPanel({
  friendIds, enemyIds, setMap, onAdd, onOpenGraph, onRemove, removingId,
}: {
  friendIds: string[]
  enemyIds: string[]
  setMap: Record<string, { name: string; slug: string | null }>
  onAdd: () => void
  onOpenGraph: () => void
  onRemove: (id: string) => void
  removingId: string | null
}) {
  const total = friendIds.length + enemyIds.length
  const setName = (sid: string) => setMap[sid]?.name ?? sid
  const sortedFriendIds = [...friendIds].sort((a, b) => setName(a).localeCompare(setName(b)))
  const sortedEnemyIds = [...enemyIds].sort((a, b) => setName(a).localeCompare(setName(b)))

  function renderRow(sid: string, kind: 'ally' | 'enemy') {
    const dot = kind === 'ally' ? 'bg-emerald-500' : 'bg-red-500'
    return (
      <div key={sid} className="group flex items-center justify-between gap-2 rounded px-1.5 py-1 hover:bg-zinc-800/50">
        <Link
          to="/sets/$id"
          params={{ id: setMap[sid]?.slug ?? sid }}
          className="flex min-w-0 items-center gap-2 text-sm text-zinc-300 hover:text-violet-400"
        >
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
          <span className="truncate">{setName(sid)}</span>
        </Link>
        <button
          type="button"
          aria-label={`Remove relationship with ${setName(sid)}`}
          disabled={removingId === sid}
          onClick={() => onRemove(sid)}
          className="shrink-0 text-zinc-700 opacity-0 transition-all hover:text-red-400 group-hover:opacity-100 disabled:opacity-40"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-3">
      <div className="mb-2.5 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Relationships{total > 0 ? ` (${total})` : ''}
        </p>
        <div className="flex items-center gap-3">
          {total > 0 && (
            <button
              type="button"
              onClick={onOpenGraph}
              className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-violet-400 transition-colors"
            >
              <GitFork className="h-3 w-3" />Graph
            </button>
          )}
          <button
            type="button"
            onClick={onAdd}
            className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-violet-400 transition-colors"
          >
            <Plus className="h-3 w-3" />Add
          </button>
        </div>
      </div>

      {total === 0 ? (
        <p className="text-xs text-zinc-600">No relationships recorded.</p>
      ) : (
        <div className="space-y-3">
          {sortedFriendIds.length > 0 && (
            <div>
              <div className="mb-1 flex items-center gap-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400">
                  Allies ({sortedFriendIds.length})
                </span>
              </div>
              <div className="space-y-0.5">
                {sortedFriendIds.map((sid) => renderRow(sid, 'ally'))}
              </div>
            </div>
          )}
          {sortedEnemyIds.length > 0 && (
            <div>
              <div className="mb-1 flex items-center gap-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-red-400">
                  Enemies ({sortedEnemyIds.length})
                </span>
              </div>
              <div className="space-y-0.5">
                {sortedEnemyIds.map((sid) => renderRow(sid, 'enemy'))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

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
  const { data: allMembers } = useAllMembers(universe?.id ?? null)

  useRecordRecent(set ? { type: 'set', id: set.id, slug: set.slug, label: set.name } : null)

  const deleteSet = useDeleteSet(universe?.id ?? '')
  const removeRel = useRemoveSetRelationship(realId, universe?.id ?? '')
  const updateSet = useUpdateSet(realId)

  const [editing, setEditing] = useState(false)
  const [duplicating, setDuplicating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [addingRel, setAddingRel] = useState(false)
  const [addingMember, setAddingMember] = useState(false)
  const [creatingMember, setCreatingMember] = useState(false)
  const [graphOpen, setGraphOpen] = useState(false)
  const [editingBio, setEditingBio] = useState(false)
  const [bioDraft, setBioDraft] = useState('')

  // Members section state
  const [memberQuery, setMemberQuery] = useState('')
  const [memberSortKey, setMemberSortKey] = useState<'name' | 'status' | 'date_of_death'>('name')
  const [memberSortDir, setMemberSortDir] = useState<SortDir>('asc')

  // Incidents section state
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

  const founder = set?.founder_id
    ? (allMembers?.items ?? []).find((m) => m.id === set.founder_id) ?? null
    : null

  const allRelIds = set ? [...set.friend_ids, ...set.enemy_ids] : []
  const memberItems: MemberListItem[] = membersData?.items ?? []
  const incidentItems: IncidentListItem[] = incidentsData?.items ?? []

  const allStatsZero = !stats || (
    stats.member_count === 0 &&
    stats.dead_members === 0 &&
    stats.total_shootings === 0 &&
    stats.total_assists === 0 &&
    stats.total_kills === 0
  )

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

  function startBioEdit() {
    setBioDraft(set?.bio ?? '')
    setEditingBio(true)
  }

  async function saveBio() {
    if (!set || !universe) return
    try {
      await updateSet.mutateAsync({ universe_id: universe.id, bio: bioDraft })
      toast.success('Bio updated')
      setEditingBio(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save bio')
    }
  }

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

  function handleExport() {
    if (!set) return
    const md = buildSetMarkdown({
      set,
      allianceName: alliance?.name ?? null,
      muniName: muni?.name ?? null,
      founderName: founder?.display_name ?? null,
      territoryNames,
      members: memberItems,
      incidents: incidentItems,
      friends: set.friend_ids.map(setName).sort((a, b) => a.localeCompare(b)),
      enemies: set.enemy_ids.map(setName).sort((a, b) => a.localeCompare(b)),
    })
    const safeName = set.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'set'
    downloadText(md, `${safeName}.md`, 'text/markdown;charset=utf-8')
  }

  const isAdmin = user?.global_role === 'ADMIN'
  const isReserved = !!set?.is_reserved
  const incidentCount = incidentItems.length

  if (isError) return <ErrorState title="Set not found" onRetry={() => refetch()} />

  return (
    <div className="space-y-5">
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
          {/* Hero header */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="shrink-0">
                {set.primary_photo_url ? (
                  <img
                    src={set.primary_photo_url}
                    alt={`Photo of ${set.name}`}
                    loading="lazy"
                    decoding="async"
                    className="h-20 w-20 rounded-xl object-cover ring-1 ring-zinc-600/80 shadow-lg shadow-black/30"
                  />
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-zinc-800 text-2xl font-bold text-zinc-400 ring-1 ring-zinc-700">
                    {set.name.slice(0, 2).toUpperCase()}
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold leading-none text-white">{set.name}</h1>
                  <CopyButton value={window.location.href} label="Copy link to this set" className="opacity-40 hover:opacity-100" />
                </div>
                {set.aliases && set.aliases.length > 0 && (
                  <p className="mt-1 text-sm text-zinc-500">a/k/a {set.aliases.join(' · ')}</p>
                )}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <SetStatusBadge status={set.status} />
                  {isReserved && (
                    <span className="inline-flex items-center rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-400">
                      System
                    </span>
                  )}
                  {!isReserved && alliance && (
                    <Link
                      to="/alliances/$id"
                      params={{ id: alliance.slug ?? alliance.id }}
                      className="rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-blue-400 transition-colors"
                    >
                      {alliance.name}
                    </Link>
                  )}
                  {!isReserved && muni && set.municipality_id && (
                    <Link
                      to="/municipalities/$id"
                      params={{ id: set.municipality_id }}
                      className="inline-flex items-center gap-1 rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors"
                    >
                      <MapPin className="h-3 w-3" />
                      {muni.name}
                    </Link>
                  )}
                  <span className="text-[11px] text-zinc-600">Updated {timeAgo(set.updated_at)}</span>
                </div>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
              </Button>
              {!isReserved && (
                <Button size="sm" variant="outline" onClick={() => setDuplicating(true)}>
                  <Copy className="mr-1.5 h-3.5 w-3.5" />Duplicate
                </Button>
              )}
              <Button size="sm" variant="outline" onClick={handleExport}>
                <Download className="mr-1.5 h-3.5 w-3.5" />Export
              </Button>
              {isAdmin && !isReserved && (
                <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
                </Button>
              )}
            </div>
          </div>

          {/* Biography — inline under hero */}
          {editingBio ? (
            <div className="space-y-2">
              <Textarea
                rows={6}
                value={bioDraft}
                onChange={(e) => setBioDraft(e.target.value)}
                placeholder="What this crew is about…"
                autoFocus
              />
              <div className="flex justify-end gap-2">
                <Button size="sm" variant="outline" onClick={() => setEditingBio(false)} disabled={updateSet.isPending}>Cancel</Button>
                <Button size="sm" onClick={saveBio} disabled={updateSet.isPending}>
                  {updateSet.isPending ? 'Saving…' : 'Save'}
                </Button>
              </div>
            </div>
          ) : set.bio ? (
            <div className="group relative rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
              <p className="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap">{set.bio}</p>
              <button type="button" onClick={startBioEdit} aria-label="Edit bio"
                className="absolute right-2 top-2 rounded p-1.5 text-zinc-500 opacity-0 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 focus-visible:opacity-100 group-hover:opacity-100">
                <Pencil className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button type="button" onClick={startBioEdit}
              className="flex w-full items-center gap-2 rounded-xl border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-600 hover:border-zinc-700 hover:text-zinc-400 transition-colors">
              <Pencil className="h-3 w-3" />Add bio
            </button>
          )}

          {isReserved && (
            <div className="rounded-lg border border-zinc-700 bg-zinc-900/50 px-4 py-3 text-sm text-zinc-400">
              <span className="font-medium text-zinc-300">System set.</span>{' '}
              Used for incident attribution when the actor is a {set.name.toLowerCase()} (not a real crew).
              Only the bio can be edited; this set cannot be renamed, reassigned, or deleted.
            </div>
          )}

          {/* Stats row — hidden when all zero */}
          {stats && !allStatsZero && (
            <div className="grid grid-cols-5 gap-2">
              <StatPill label="Members" value={stats.member_count} />
              <StatPill label="Dead" value={stats.dead_members} accent="text-zinc-400" />
              <StatPill label="Shootings" value={stats.total_shootings} accent="text-amber-400" />
              <StatPill label="Assists" value={stats.total_assists} accent="text-violet-400" />
              <StatPill label="Kills" value={stats.total_kills} accent="text-rose-400" />
            </div>
          )}

          {/* Two-column wiki layout: identity facts + side panels */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_280px]">
            {/* Left: identity facts */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-1">
              <DetailRow label="Founder">
                {founder ? (
                  <Link to="/members/$id" params={{ id: founder.slug ?? founder.id }} className="text-violet-400 hover:underline">
                    {founder.display_name}
                  </Link>
                ) : <span className="text-zinc-600">—</span>}
              </DetailRow>
              <DetailRow label="Alliance">
                {alliance ? (
                  <Link to="/alliances/$id" params={{ id: alliance.slug ?? alliance.id }} className="text-blue-400 hover:underline">
                    {alliance.name}
                  </Link>
                ) : <span className="text-zinc-600">—</span>}
              </DetailRow>
              <DetailRow label="Municipality">
                {muni && set.municipality_id ? (
                  <Link to="/municipalities/$id" params={{ id: set.municipality_id }} className="text-violet-400 hover:underline">
                    {muni.name}
                  </Link>
                ) : <span className="text-zinc-600">—</span>}
              </DetailRow>
              <DetailRow label="Territories">
                {territoryNames.length > 0 ? (
                  <span title={territoryNames.join(', ')}>
                    {territoryNames.length} sub-district{territoryNames.length === 1 ? '' : 's'}
                  </span>
                ) : <span className="text-zinc-600">—</span>}
              </DetailRow>
              <DetailRow label="Created">
                <span className="text-zinc-400">{timeAgo(set.created_at)}</span>
              </DetailRow>
            </div>

            {/* Right: relationships */}
            {!isReserved && (
              <RelationshipsPanel
                friendIds={set.friend_ids}
                enemyIds={set.enemy_ids}
                setMap={setMap}
                onAdd={() => setAddingRel(true)}
                onOpenGraph={() => setGraphOpen(true)}
                onRemove={(sid) => removeRel.mutate(sid)}
                removingId={removeRel.isPending ? (removeRel.variables as string | undefined) ?? null : null}
              />
            )}
          </div>

          {/* Members section */}
          <section>
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Members</h2>
                {memberItems.length > 0 && (
                  <Badge variant="secondary" className="px-1.5 py-0 text-xs">{memberItems.length}</Badge>
                )}
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
                {memberQuery && filteredMembers.length !== memberItems.length && (
                  <span className="text-xs text-zinc-500 tabular-nums">
                    {filteredMembers.length} of {memberItems.length}
                  </span>
                )}
              </div>
              <Button size="sm" variant="outline" onClick={() => setAddingMember(true)}>
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
              <div className="overflow-hidden rounded-xl border border-zinc-800">
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
          </section>

          {/* Incidents section */}
          <section>
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Incidents</h2>
                {incidentCount > 0 && (
                  <Badge variant="secondary" className="px-1.5 py-0 text-xs">{incidentCount}</Badge>
                )}
              </div>
            </div>
            {incidentCount === 0 ? (
              <EmptyState
                icon={ShieldAlert}
                title="No incidents recorded"
                description="Incidents involving members of this set will appear here."
              />
            ) : (
              <div className="overflow-hidden rounded-xl border border-zinc-800">
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
          </section>

          {/* Photos section */}
          {!isReserved && universe && (
            <section>
              <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Photos</h2>
              <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                <PhotoGallery entityType="set" entityId={set.id} universeId={universe.id} />
              </Suspense>
            </section>
          )}

          {/* Relationship graph dialog */}
          {!isReserved && (
            <Dialog open={graphOpen} onOpenChange={setGraphOpen}>
              <DialogContent className="max-w-3xl">
                <DialogHeader>
                  <DialogTitle>{set.name} — Relationship Network</DialogTitle>
                  <DialogDescription>Click a set to open it. Pan with drag, zoom with the controls.</DialogDescription>
                </DialogHeader>
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
              </DialogContent>
            </Dialog>
          )}

          {/* Dialogs */}
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
              const incCount = incidentsData?.items.length ?? 0
              const relCount = set.friend_ids.length + set.enemy_ids.length
              if (!memberCount && !incCount && !relCount) return null
              const parts: string[] = []
              if (memberCount) parts.push(`${memberCount} member${memberCount === 1 ? '' : 's'}`)
              if (incCount) parts.push(`${incCount} incident${incCount === 1 ? '' : 's'}`)
              if (relCount) parts.push(`${relCount} relationship${relCount === 1 ? '' : 's'}`)
              return <span>{parts.join(', ')} will be unlinked from this set.</span>
            })()}
            confirmLabel="Delete"
            destructive
            pending={deleteSet.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />

          {!isReserved && universe && (
            <AddRelationshipDialog
              setId={set.id}
              universeId={universe.id}
              open={addingRel}
              onClose={() => setAddingRel(false)}
              existingIds={allRelIds}
            />
          )}

          {universe && (
            <AddMemberToSetDialog
              setId={set.id}
              setName={set.name}
              universeId={universe.id}
              open={addingMember}
              onClose={() => setAddingMember(false)}
              onCreateNew={() => { setAddingMember(false); setCreatingMember(true) }}
            />
          )}

          {universe && (
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
