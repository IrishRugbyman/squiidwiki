import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Activity, Copy, Download, GitFork, Image as ImageIcon, ListTree, MapPin, MoreHorizontal, Pencil, Plus, Search, ShieldAlert, Swords, Trash2, UserPlus, Users, X } from 'lucide-react'
import { useEffect, useMemo, useState, lazy, Suspense } from 'react'
import { toast } from 'sonner'
import {
  useAddSetRelationship, useRemoveSetRelationship,
  useSetDetail, useDeleteSet, useUpdateSet,
  useSetMembers, useSetIncidents, useAllSets, useSetActivity,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { SetStatusBadge, MemberStatusBadge } from '@/components/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { currentAffiliations, timeAgo } from '@/lib/utils'
import { downloadText } from '@/lib/download'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Skeleton } from '@/components/ui/skeleton'
import { GangPill, SetAvatar, SetFormSheet } from './_app.sets.index'
import { TAB_KEYS, type TabKey } from './_app.sets.$id'
import { MemberFormSheet } from './_app.members.index'
import { MemberAvatar } from '@/components/members/MemberFormSheet'
import { DetailRow, IncidentRow, None, PanelHeading, RankBadge, StatStrip } from '@/components/detail/DetailParts'
import { AddMemberToSetDialog } from '@/components/AddMemberToSetDialog'
import { LineagePanel } from '@/components/sets/LineagePanel'
import { AffiliationCombobox } from '@/components/members/MemberFormSheet/pickers/AffiliationCombobox'
import { setPickerItems } from '@/lib/setPicker'
import { nonPrimaryVariantsText, variantLead } from '@/lib/setDisplay'
import { MEMBER_STATUS_CHIP_ACTIVE, MEMBER_STATUS_DOT, MEMBER_STATUS_ORDER } from '@/lib/statusColors'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'
import type { IncidentListItem, MemberListItem, MemberStatus, SetReadDetailFull } from '@/lib/types'
import { LinkifiedText } from '@/components/LinkifiedText'

export const Route = createLazyFileRoute('/_app/sets/$id')({
  component: SetDetailPage,
})

const SetRelationshipGraph = lazy(() =>
  import('@/components/graphs/SetRelationshipGraph').then((m) => ({ default: m.SetRelationshipGraph })),
)
const PhotoGallery = lazy(() =>
  import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })),
)

/**
 * Tiny year-bucketed activity strip — pure SVG, no recharts.
 * Renders one bar per year between min..max, filling gaps with zero so the
 * timeline is uniform. Designed to fit in ~64px height above an incidents table.
 */
function IncidentsYearStrip({ data }: { data: Array<{ year: number; count: number }> }) {
  if (!data.length) return null
  const minYear = data[0].year
  const maxYear = data[data.length - 1].year
  const span = maxYear - minYear + 1
  // Densify: include every year between min and max so years aren't squished.
  const counts = new Map(data.map((d) => [d.year, d.count]))
  const years = Array.from({ length: span }, (_, i) => minYear + i)
  const max = Math.max(...data.map((d) => d.count), 1)
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
      <div className="mb-1.5 flex items-baseline justify-between text-[10px] uppercase tracking-wider text-zinc-400">
        <span>Incidents per year</span>
        <span className="font-mono tabular-nums">{minYear}–{maxYear}</span>
      </div>
      <div className="flex items-end gap-0.5" style={{ height: 48 }}>
        {years.map((y) => {
          const c = counts.get(y) ?? 0
          const h = c === 0 ? 2 : Math.max(4, (c / max) * 48)
          return (
            <div
              key={y}
              title={`${y}: ${c} incident${c === 1 ? '' : 's'}`}
              className={`flex-1 rounded-md transition-colors ${c === 0 ? 'bg-zinc-800/40' : 'bg-violet-500/70 hover:bg-violet-400'}`}
              style={{ height: h }}
            />
          )
        })}
      </div>
    </div>
  )
}

/** Audit-log feed grouped by day. */
function ActivityFeed({ entries, loading, setName }: {
  entries: import('@/lib/types').SetActivityEntry[]
  loading: boolean
  setName: string
}) {
  if (loading) return <Skeleton className="h-40 w-full" />
  if (entries.length === 0) {
    return (
      <EmptyState
        icon={Activity}
        title="No activity yet"
        description={`Edits to ${setName} or any of its members will appear here.`}
      />
    )
  }
  // Group by YYYY-MM-DD (local time)
  const groups = new Map<string, typeof entries>()
  for (const e of entries) {
    const d = new Date(e.created_at)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(e)
  }
  return (
    <div className="space-y-4">
      {Array.from(groups.entries()).map(([day, items]) => {
        const date = new Date(items[0].created_at)
        const today = new Date()
        const isToday = date.toDateString() === today.toDateString()
        const yesterday = new Date(today.getTime() - 86_400_000)
        const isYesterday = date.toDateString() === yesterday.toDateString()
        const label = isToday ? 'Today' : isYesterday ? 'Yesterday' : date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
        return (
          <div key={day}>
            <h3 className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-zinc-400">{label}</h3>
            <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800 bg-zinc-900/30">
              {items.map((e) => {
                const verb = e.action === 'CREATE' ? 'created' : e.action === 'DELETE' ? 'deleted' : 'updated'
                const actor = e.actor_email ? e.actor_email.split('@')[0] : 'Someone'
                const noun = e.entity_type === 'set' ? 'set' : 'member'
                const target = e.target_label ?? '(deleted)'
                const linkTo = e.entity_type === 'set'
                  ? { to: '/sets/$id' as const, params: { id: e.target_slug ?? e.entity_id } }
                  : { to: '/members/$id' as const, params: { id: e.target_slug ?? e.entity_id } }
                const time = new Date(e.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
                // The audit listener captures every column on CREATE — too noisy
                // to display; only render diff_keys for UPDATE actions.
                const showKeys = e.action === 'UPDATE' && e.diff_keys.length > 0
                return (
                  <li key={e.id} className="flex items-start gap-3 px-4 py-2.5 text-sm">
                    <span className={`mt-1 inline-block h-1.5 w-1.5 shrink-0 rounded-full ${
                      e.action === 'CREATE' ? 'bg-emerald-500' :
                      e.action === 'DELETE' ? 'bg-red-500' : 'bg-violet-500'
                    }`} aria-hidden />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-0.5">
                        <span className="text-zinc-300">{actor}</span>
                        <span className="text-zinc-400">{verb} {noun}</span>
                        <Link {...linkTo} className="font-medium text-violet-400 hover:underline truncate">
                          {target}
                        </Link>
                        <span className="ml-auto font-mono text-[11px] tabular-nums text-zinc-400">{time}</span>
                      </div>
                      {showKeys && (
                        <div className="mt-0.5 flex flex-wrap gap-1 text-[10px] text-zinc-400">
                          {e.diff_keys.slice(0, 6).map((k) => (
                            <span key={k} className="rounded bg-zinc-800/60 px-1.5 py-0.5">{k}</span>
                          ))}
                          {e.diff_keys.length > 6 && <span className="text-zinc-400">+{e.diff_keys.length - 6}</span>}
                        </div>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        )
      })}
    </div>
  )
}

// Sortable column key from a FuzzyDate. Missing dates sort last.
const UNDATED = '\uffff'

function fuzzyDateSortKey(d: FuzzyDateValue | null | undefined): string {
  if (!d || !d.year) return UNDATED
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
        <span className="text-zinc-400" aria-hidden>
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
  set: SetReadDetailFull
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
  const aka = nonPrimaryVariantsText(set.name_variants, ', ')
  if (aka) {
    lines.push('')
    lines.push(`*a/k/a ${aka}*`)
  }
  lines.push('')

  lines.push('## Identity')
  lines.push('')
  lines.push(`- **Status:** ${set.status}`)
  if (set.gang_name) lines.push(`- **Nation:** ${set.gang_name}`)
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
      const dod = m.date_of_death ? `, died ${formatFuzzyDateText(m.date_of_death)}` : ''
      lines.push(`- ${m.display_name} (${m.status}${dod})`)
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
      const victims = inc.victim_names.length > 0 ? ` (victims: ${inc.victim_names.join(', ')})` : ''
      const by = inc.shooter_names.length > 0 ? ` by ${inc.shooter_names.join(', ')}` : ''
      lines.push(`- ${dateStr}: ${inc.type}${by}${victims}`)
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
  const { data: allSets } = useAllSets(universeId)
  const add = useAddSetRelationship(setId, universeId)
  const [targetId, setTargetId] = useState('')
  const [type, setType] = useState<'FRIEND' | 'ENEMY'>('FRIEND')
  const [error, setError] = useState<string | null>(null)

  const available = useMemo(
    () => setPickerItems(
      (allSets?.items ?? []).filter((s) => s.id !== setId && !existingIds.includes(s.id)),
    ),
    [allSets, setId, existingIds],
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
            Relationships are bilateral. The selected set will show this set as {isAlly ? 'an ally' : 'an enemy'} too.
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
                    : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-300'
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
                    : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-300'
                }`}
              >
                <Swords className="h-4 w-4" /> Enemy
              </button>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">Set</label>
            <AffiliationCombobox
              label="Set"
              value={targetId}
              onChange={setTargetId}
              items={available}
              placeholder="Select a set…"
            />
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
  /** Shown only where the graph is elsewhere; on the Relationships tab it sits beside the panel. */
  onOpenGraph?: () => void
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
          className="shrink-0 text-zinc-500 transition-all hover:text-red-400 focus-visible:opacity-100 group-hover:opacity-100 disabled:opacity-40 pointer-fine:opacity-0"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3">
      <div className="mb-2.5 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Relationships{total > 0 ? ` (${total})` : ''}
        </p>
        <div className="flex items-center gap-3">
          {total > 0 && onOpenGraph && (
            <button
              type="button"
              onClick={onOpenGraph}
              className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-violet-400 transition-colors"
            >
              <GitFork className="h-3 w-3" />Graph
            </button>
          )}
          <button
            type="button"
            onClick={onAdd}
            className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-violet-400 transition-colors"
          >
            <Plus className="h-3 w-3" />Add
          </button>
        </div>
      </div>

      {total === 0 ? (
        <p className="text-xs text-zinc-400">No relationships recorded.</p>
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

// ─── Page pieces ──────────────────────────────────────────────────────────────

const RANK_ORDER: Record<string, number> = { CEO: 0, CO_CEO: 1 }
const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

type MemberSortKey = 'name' | 'status' | 'joined' | 'date_of_death'
type IncidentSortKey = 'date' | 'type'

/** This set's spell for a member: rank and join date live on it, not on the member. */
function spellIn(m: MemberListItem, setId: string) {
  return currentAffiliations(m.affiliations).find((a) => a.set_id === setId) ?? null
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function SetDetailPage() {
  const { id } = Route.useParams()
  const search = Route.useSearch()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const [primaryOnly, setPrimaryOnly] = useState(false)
  const { data: set, isLoading, isError, refetch } = useSetDetail(id, universe?.id ?? null)
  const realId = set?.id ?? ''
  const isReserved = !!set?.is_reserved
  const { data: membersData, isLoading: membersLoading } = useSetMembers(realId, universe?.id ?? null, primaryOnly)
  const { data: incidentsData, isLoading: incidentsLoading } = useSetIncidents(realId, universe?.id ?? null)

  // System sets have no relationships or media, so their tabs, and the number
  // keys that reach them, are left out rather than opening a blank panel.
  const visibleTabs = useMemo<readonly TabKey[]>(
    () => TAB_KEYS.filter((k) => !isReserved || (k !== 'relationships' && k !== 'media')),
    [isReserved],
  )
  const tab: TabKey = search.tab && visibleTabs.includes(search.tab) ? search.tab : 'overview'
  const setTab = (next: TabKey) => navigate({ to: '/sets/$id', params: { id }, search: (s) => ({ ...s, tab: next === 'overview' ? undefined : next }), replace: true })

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      const t = e.target as HTMLElement | null
      if (t && (t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))) return
      const idx = Number(e.key) - 1
      if (!Number.isInteger(idx) || idx < 0 || idx >= visibleTabs.length) return
      e.preventDefault()
      navigate({ to: '/sets/$id', params: { id }, search: (s) => ({ ...s, tab: idx === 0 ? undefined : visibleTabs[idx] }), replace: true })
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [id, visibleTabs, navigate])

  // Lazy-load the activity feed only when the Activity tab is open.
  const { data: activityData, isLoading: activityLoading } = useSetActivity(realId, universe?.id ?? null, tab === 'activity')

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
  const [editingBio, setEditingBio] = useState(false)
  const [bioDraft, setBioDraft] = useState('')

  const [memberQuery, setMemberQuery] = useState('')
  const [memberStatusFilter, setMemberStatusFilter] = useState<MemberStatus | 'ALL'>('ALL')
  const [memberSortKey, setMemberSortKey] = useState<MemberSortKey>('name')
  const [memberSortDir, setMemberSortDir] = useState<SortDir>('asc')
  const [incSortKey, setIncSortKey] = useState<IncidentSortKey>('date')
  const [incSortDir, setIncSortDir] = useState<SortDir>('desc')

  useEditShortcut(() => set && setEditing(true))

  const setMap = useMemo(() => {
    const map: Record<string, { name: string; slug: string | null }> = {}
    for (const a of set?.allies ?? []) map[a.id] = { name: a.name, slug: a.slug }
    for (const e of set?.enemies ?? []) map[e.id] = { name: e.name, slug: e.slug }
    return map
  }, [set])
  const setName = (sid: string) => setMap[sid]?.name ?? sid

  const memberItems: MemberListItem[] = useMemo(() => membersData?.items ?? [], [membersData])
  const incidentItems: IncidentListItem[] = useMemo(() => incidentsData?.items ?? [], [incidentsData])

  const memberStatusCounts = useMemo(() => {
    const c: Partial<Record<MemberStatus, number>> = {}
    for (const m of memberItems) c[m.status] = (c[m.status] ?? 0) + 1
    return c
  }, [memberItems])

  // Leaders first, then the rest by name: the roster preview's order.
  const roster = useMemo(() => [...memberItems].sort((a, b) => {
    const ra = RANK_ORDER[spellIn(a, realId)?.rank ?? ''] ?? 9
    const rb = RANK_ORDER[spellIn(b, realId)?.rank ?? ''] ?? 9
    return ra - rb || a.display_name.localeCompare(b.display_name, undefined, { sensitivity: 'base', numeric: true })
  }), [memberItems, realId])

  const filteredMembers = useMemo(() => {
    const q = memberQuery.trim().toLowerCase()
    let rows = memberItems
    if (memberStatusFilter !== 'ALL') rows = rows.filter((m) => m.status === memberStatusFilter)
    if (q) {
      rows = rows.filter((m) =>
        m.display_name.toLowerCase().includes(q)
        || !!m.aliases?.some((a) => a.toLowerCase().includes(q)))
    }
    const dir = memberSortDir === 'asc' ? 1 : -1
    const byName = (a: MemberListItem, b: MemberListItem) =>
      a.display_name.localeCompare(b.display_name, undefined, { sensitivity: 'base', numeric: true })
    // Undated rows sink to the bottom whichever way a date column sorts.
    const byDate = (x: FuzzyDateValue | null | undefined, y: FuzzyDateValue | null | undefined) => {
      const kx = fuzzyDateSortKey(x), ky = fuzzyDateSortKey(y)
      if ((kx === UNDATED) !== (ky === UNDATED)) return kx === UNDATED ? 1 : -1
      return kx.localeCompare(ky) * dir
    }
    return [...rows].sort((a, b) => {
      switch (memberSortKey) {
        case 'status': return (MEMBER_STATUS_ORDER.indexOf(a.status) - MEMBER_STATUS_ORDER.indexOf(b.status)) * dir || byName(a, b)
        case 'joined': return byDate(spellIn(a, realId)?.from_date, spellIn(b, realId)?.from_date) || byName(a, b)
        case 'date_of_death': return byDate(a.date_of_death, b.date_of_death) || byName(a, b)
        default: return byName(a, b) * dir
      }
    })
  }, [memberItems, memberQuery, memberStatusFilter, memberSortKey, memberSortDir, realId])

  const sortedIncidents = useMemo(() => {
    const dir = incSortDir === 'asc' ? 1 : -1
    return [...incidentItems].sort((a, b) => {
      const ka = fuzzyDateSortKey(a.date), kb = fuzzyDateSortKey(b.date)
      if (incSortKey === 'type') return a.type.localeCompare(b.type) * dir || kb.localeCompare(ka)
      if ((ka === UNDATED) !== (kb === UNDATED)) return ka === UNDATED ? 1 : -1
      return ka.localeCompare(kb) * dir
    })
  }, [incidentItems, incSortKey, incSortDir])

  function toggleMemberSort(k: MemberSortKey) {
    if (memberSortKey === k) setMemberSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setMemberSortKey(k); setMemberSortDir(k === 'date_of_death' || k === 'joined' ? 'desc' : 'asc') }
  }
  function toggleIncSort(k: IncidentSortKey) {
    if (incSortKey === k) setIncSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setIncSortKey(k); setIncSortDir(k === 'date' ? 'desc' : 'asc') }
  }

  function showMembers(status: MemberStatus | 'ALL') {
    setMemberStatusFilter(status)
    setMemberQuery('')
    setTab('members')
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
    } catch {
      // The global mutation handler has already toasted the error; stay in edit mode.
    }
  }

  async function handleDelete() {
    if (!set) return
    try {
      await deleteSet.mutateAsync(set.id)
      navigate({ to: '/sets' })
    } catch {
      setDeleting(false)
    }
  }

  if (isError) return <ErrorState title="Set not found" onRetry={() => refetch()} />

  const stats = set?.stats
  const alliance = set?.alliance_id && set.alliance_name
    ? { id: set.alliance_id, name: set.alliance_name, slug: set.alliance_slug }
    : null
  const territoryNames = (set?.territories ?? []).map((t) => t.name).sort((a, b) => a.localeCompare(b))
  const founder = set?.founder_id && set.founder_display_name
    ? { id: set.founder_id, display_name: set.founder_display_name, slug: set.founder_slug }
    : null
  const relCount = set ? set.friend_ids.length + set.enemy_ids.length : 0
  const isAdmin = user?.global_role === 'ADMIN'
  const tabNumber = (k: TabKey) => visibleTabs.indexOf(k) + 1

  function handleExport() {
    if (!set) return
    const md = buildSetMarkdown({
      set,
      allianceName: alliance?.name ?? null,
      muniName: set.municipality_name,
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

  // Duplicating keeps every field but the names: the primary name gets " (copy)",
  // since a second set under the same name is refused.
  const duplicateSeed = set ? {
    ...set,
    name: `${set.name} (copy)`,
    name_variants: (set.name_variants ?? []).map((v) => {
      if (!v.is_primary) return v
      const lead = variantLead(v) ?? 'name'
      return { ...v, [lead]: `${(v[lead] ?? set.name).trim()} (copy)` }
    }),
  } : null

  return (
    <div className="space-y-5">
      <Breadcrumbs items={[{ label: 'Sets', to: '/sets' }, { label: set?.name ?? 'Set' }]} />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : set ? (
        <>
          {/* Header */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex min-w-0 items-start gap-4">
              {!isReserved && set.primary_photo_url ? (
                <button type="button" onClick={() => setTab('media')} aria-label="Open photos" className="shrink-0 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500">
                  <SetAvatar name={set.name} thumbUrl={set.primary_photo_url} size="xl" gangColor={set.gang_color} />
                </button>
              ) : (
                <SetAvatar name={set.name} thumbUrl={set.primary_photo_url} size="xl" isReserved={isReserved} gangColor={set.gang_color} />
              )}
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  {set.emojis?.length ? (
                    <span className="text-xl leading-none" title={`Signals this set: ${set.emojis.join(' ')}`} aria-label={`Emojis for this set: ${set.emojis.join(' ')}`}>
                      {set.emojis.join('')}
                    </span>
                  ) : null}
                  <h1 className="text-2xl font-bold leading-tight text-white">{set.name}</h1>
                  <CopyButton value={window.location.href} label="Copy link to this set" className="opacity-40 hover:opacity-100" />
                </div>
                {(() => {
                  const variants = set.name_variants ?? []
                  const primary = variants.find((v) => v.is_primary)
                  const others = variants.filter((v) => !v.is_primary)
                  const primaryExtras = primary
                    ? (['name', 'initials', 'number'] as const)
                        .filter((slot) => slot !== variantLead(primary) && primary[slot]?.trim())
                        .map((slot) => ({ slot, value: primary[slot]!.trim() }))
                    : []
                  if (primaryExtras.length === 0 && others.length === 0) return null
                  return (
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                      {primaryExtras.map(({ slot, value }) => (
                        <span key={slot} className="inline-flex items-center gap-1 rounded-full bg-zinc-800/70 px-2 py-0.5 text-zinc-300">
                          <span className="text-[10px] uppercase tracking-wider text-zinc-400">{slot}</span>
                          {value}
                        </span>
                      ))}
                      {others.length > 0 && <span className="ml-1 text-[10px] uppercase tracking-wider text-zinc-400">a/k/a</span>}
                      {others.map((v, i) => {
                        const lead = variantLead(v)
                        if (!lead) return null
                        const extras = (['name', 'initials', 'number'] as const)
                          .filter((slot) => slot !== lead && v[slot]?.trim())
                          .map((slot) => v[slot]!.trim())
                        return (
                          <span key={i} className="inline-flex items-center gap-1 rounded-full border border-zinc-800 bg-zinc-900/60 px-2 py-0.5 text-zinc-400">
                            <span className="text-zinc-200">{v[lead]!.trim()}</span>
                            {extras.length > 0 && <span>· {extras.join(' · ')}</span>}
                          </span>
                        )
                      })}
                    </div>
                  )
                })()}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <SetStatusBadge status={set.status} />
                  {isReserved && (
                    <span className="inline-flex items-center rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-400">System</span>
                  )}
                  {!isReserved && set.gang_name && <GangPill name={set.gang_name} />}
                  {!isReserved && alliance && (
                    <Link to="/alliances/$id" params={{ id: alliance.slug ?? alliance.id }} className="rounded-full bg-blue-950/60 px-2.5 py-0.5 text-xs font-medium text-blue-300 ring-1 ring-blue-800/50 transition-colors hover:ring-blue-600">
                      {alliance.name}
                    </Link>
                  )}
                  {!isReserved && set.municipality_id && set.municipality_name && (
                    <Link to="/municipalities/$id" params={{ id: set.municipality_id }} className="inline-flex items-center gap-1 rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-violet-300">
                      <MapPin className="h-3 w-3" />{set.municipality_name}
                    </Link>
                  )}
                  <span className="text-[11px] text-zinc-400">Updated {timeAgo(set.updated_at)}</span>
                </div>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)} title="Edit (e)">
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="outline" aria-label="More actions"><MoreHorizontal className="h-3.5 w-3.5" /></Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setAddingMember(true)}><UserPlus className="mr-2 h-3.5 w-3.5" />Add member</DropdownMenuItem>
                  {!isReserved && (
                    <DropdownMenuItem onClick={() => setAddingRel(true)}><Swords className="mr-2 h-3.5 w-3.5" />Add ally or enemy</DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  {!isReserved && (
                    <DropdownMenuItem onClick={() => setDuplicating(true)}><Copy className="mr-2 h-3.5 w-3.5" />Duplicate</DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={handleExport}><Download className="mr-2 h-3.5 w-3.5" />Export Markdown</DropdownMenuItem>
                  {isAdmin && !isReserved && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setDeleting(true)} className="text-red-400 focus:text-red-300">
                        <Trash2 className="mr-2 h-3.5 w-3.5" />Delete set
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <StatStrip cells={[
            { label: 'Members', value: memberItems.length, accent: 'text-violet-400', onClick: () => showMembers('ALL'), title: 'Current members' },
            { label: 'Locked', value: memberStatusCounts.LOCKED ?? 0, accent: 'text-orange-400', onClick: () => showMembers('LOCKED') },
            { label: 'Dead', value: memberStatusCounts.DEAD ?? 0, accent: 'text-zinc-200', onClick: () => showMembers('DEAD') },
            { label: 'Incidents', value: incidentItems.length, accent: 'text-sky-400', onClick: () => setTab('incidents'), title: 'Incidents involving its current members' },
            { label: 'Shootings', value: stats?.total_shootings ?? 0, accent: 'text-amber-400', title: 'Shootings its members are recorded as shooters in, acquittals excluded' },
            { label: 'Kills', value: stats?.total_kills ?? 0, accent: 'text-rose-400', title: 'Killings its members are recorded as shooters in, acquittals excluded' },
          ]} />

          <Tabs value={tab} onValueChange={(v) => setTab(v as TabKey)} className="w-full">
            <div className="-mx-1 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              <TabsList className="h-auto w-max bg-zinc-950/50 p-0.5">
                <TabsTrigger value="overview" title={`Overview (${tabNumber('overview')})`}><ListTree className="mr-1.5 h-3.5 w-3.5" />Overview</TabsTrigger>
                <TabsTrigger value="members" title={`Members (${tabNumber('members')})`}>
                  <Users className="mr-1.5 h-3.5 w-3.5" />Members
                  {memberItems.length > 0 && <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-[10px]">{memberItems.length}</Badge>}
                </TabsTrigger>
                <TabsTrigger value="incidents" title={`Incidents (${tabNumber('incidents')})`}>
                  <ShieldAlert className="mr-1.5 h-3.5 w-3.5" />Incidents
                  {incidentItems.length > 0 && <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-[10px]">{incidentItems.length}</Badge>}
                </TabsTrigger>
                {!isReserved && (
                  <TabsTrigger value="relationships" title={`Relationships (${tabNumber('relationships')})`}>
                    <GitFork className="mr-1.5 h-3.5 w-3.5" />Relationships
                    {relCount > 0 && <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-[10px]">{relCount}</Badge>}
                  </TabsTrigger>
                )}
                {!isReserved && (
                  <TabsTrigger value="media" title={`Media (${tabNumber('media')})`}><ImageIcon className="mr-1.5 h-3.5 w-3.5" />Media</TabsTrigger>
                )}
                <TabsTrigger value="activity" title={`Activity (${tabNumber('activity')})`}><Activity className="mr-1.5 h-3.5 w-3.5" />Activity</TabsTrigger>
              </TabsList>
            </div>

            {/* Overview: the story on the left, the facts and ties on the right. */}
            <TabsContent value="overview" className="mt-4">
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
                <div className="min-w-0 space-y-5">
                  {editingBio ? (
                    <div className="space-y-2">
                      <Textarea rows={6} value={bioDraft} onChange={(e) => setBioDraft(e.target.value)} placeholder="What this crew is about…" autoFocus />
                      <div className="flex justify-end gap-2">
                        <Button size="sm" variant="outline" onClick={() => setEditingBio(false)} disabled={updateSet.isPending}>Cancel</Button>
                        <Button size="sm" onClick={saveBio} disabled={updateSet.isPending}>{updateSet.isPending ? 'Saving…' : 'Save'}</Button>
                      </div>
                    </div>
                  ) : set.bio ? (
                    <div className="group relative rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                      <p className="whitespace-pre-wrap pr-6 text-sm leading-relaxed text-zinc-300"><LinkifiedText text={set.bio} /></p>
                      <button type="button" onClick={startBioEdit} aria-label="Edit bio"
                        className="absolute right-2 top-2 rounded p-1.5 text-zinc-400 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 focus-visible:opacity-100 group-hover:opacity-100 pointer-fine:opacity-0">
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button type="button" onClick={startBioEdit}
                      className="flex w-full items-center gap-2 rounded-lg border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200">
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

                  {/* Roster: leaders first. */}
                  <section>
                    <PanelHeading action={memberItems.length > 0 && (
                      <button type="button" onClick={() => showMembers('ALL')} className="text-xs text-zinc-400 transition-colors hover:text-violet-400">
                        View all {memberItems.length} →
                      </button>
                    )}>Roster</PanelHeading>
                    {membersLoading ? (
                      <Skeleton className="h-24 w-full" />
                    ) : roster.length === 0 ? (
                      <button type="button" onClick={() => setAddingMember(true)}
                        className="flex w-full items-center gap-2 rounded-lg border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200">
                        <UserPlus className="h-3 w-3" />No current members. Add one
                      </button>
                    ) : (
                      <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2 xl:grid-cols-3">
                        {roster.slice(0, 12).map((m, i) => {
                          const rank = spellIn(m, realId)?.rank ?? null
                          return (
                            // Six on a phone, where the cards stack one per row.
                            <Link key={m.id} to="/members/$id" params={{ id: m.slug ?? m.id }}
                              className={`${i >= 6 ? 'hidden sm:flex' : 'flex'} group min-w-0 items-center gap-2.5 rounded-lg border border-zinc-800 bg-zinc-900/30 px-2.5 py-2 transition-colors hover:border-zinc-700 hover:bg-zinc-900/60`}>
                              <MemberAvatar member={m} />
                              <span className="min-w-0 flex-1">
                                <span className="flex items-center gap-1.5">
                                  <span className="truncate text-sm font-medium text-zinc-100 group-hover:text-violet-300">{m.display_name}</span>
                                  <RankBadge rank={rank} />
                                </span>
                                <span className="flex items-center gap-1.5 text-[11px] text-zinc-400">
                                  <span className={`h-1.5 w-1.5 rounded-full ${MEMBER_STATUS_DOT[m.status]}`} aria-hidden />
                                  {titleCase(m.status)}
                                </span>
                              </span>
                            </Link>
                          )
                        })}
                      </div>
                    )}
                    {roster.length > 12 && (
                      <button type="button" onClick={() => showMembers('ALL')} className="mt-2 text-xs text-zinc-400 transition-colors hover:text-violet-400">
                        +{roster.length - 12} more
                      </button>
                    )}
                  </section>

                  <section>
                    <PanelHeading action={incidentItems.length > 5 && (
                      <button type="button" onClick={() => setTab('incidents')} className="text-xs text-zinc-400 transition-colors hover:text-violet-400">
                        View all {incidentItems.length} →
                      </button>
                    )}>Latest incidents</PanelHeading>
                    {incidentsLoading ? (
                      <Skeleton className="h-32 w-full" />
                    ) : incidentItems.length === 0 ? (
                      <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No incidents involve its current members.</p>
                    ) : (
                      <div className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                        {[...incidentItems]
                          .sort((a, b) => fuzzyDateSortKey(b.date).replace(UNDATED, '0').localeCompare(fuzzyDateSortKey(a.date).replace(UNDATED, '0')))
                          .slice(0, 5)
                          .map((inc) => <IncidentRow key={inc.id} inc={inc} />)}
                      </div>
                    )}
                  </section>
                </div>

                <aside className="min-w-0 space-y-5">
                  <section>
                    <PanelHeading>Details</PanelHeading>
                    <dl className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                      <DetailRow label="Status"><SetStatusBadge status={set.status} /></DetailRow>
                      {!isReserved && (
                        <>
                          <DetailRow label="Founder">
                            {founder ? (
                              <Link to="/members/$id" params={{ id: founder.slug ?? founder.id }} className="text-violet-400 hover:underline">{founder.display_name}</Link>
                            ) : <None />}
                          </DetailRow>
                          <DetailRow label="Gang">{set.gang_name ?? <None />}</DetailRow>
                          <DetailRow label="Alliance">
                            {alliance ? (
                              <Link to="/alliances/$id" params={{ id: alliance.slug ?? alliance.id }} className="text-blue-400 hover:underline">{alliance.name}</Link>
                            ) : <None />}
                          </DetailRow>
                          <DetailRow label="Municipality">
                            {set.municipality_id && set.municipality_name ? (
                              <Link to="/municipalities/$id" params={{ id: set.municipality_id }} className="text-violet-400 hover:underline">{set.municipality_name}</Link>
                            ) : <None />}
                          </DetailRow>
                          <DetailRow label="Territory">
                            {territoryNames.length > 0 ? territoryNames.join(', ') : <None />}
                          </DetailRow>
                          <DetailRow label="Active years">
                            {stats?.first_incident_year
                              ? stats.first_incident_year === stats.last_incident_year
                                ? String(stats.first_incident_year)
                                : `${stats.first_incident_year} to ${stats.last_incident_year}`
                              : <None />}
                          </DetailRow>
                        </>
                      )}
                      <DetailRow label="Added"><span className="text-zinc-400">{timeAgo(set.created_at)}</span></DetailRow>
                    </dl>
                  </section>

                  {!isReserved && (
                    <RelationshipsPanel
                      friendIds={set.friend_ids}
                      enemyIds={set.enemy_ids}
                      setMap={setMap}
                      onAdd={() => setAddingRel(true)}
                      onOpenGraph={() => setTab('relationships')}
                      onRemove={(sid) => removeRel.mutate(sid)}
                      removingId={removeRel.isPending ? (removeRel.variables as string | undefined) ?? null : null}
                    />
                  )}
                  {/* Lineage stands on its own: it used to render only beside a
                      relationship graph, so a set with lineage and no allies or
                      enemies showed none of it. */}
                  {!isReserved && universe && <LineagePanel setId={set.id} setName={set.name} universeId={universe.id} />}
                </aside>
              </div>
            </TabsContent>

            {/* Members */}
            <TabsContent value="members" className="mt-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                {memberItems.length > 5 && (
                  <div className="relative min-w-[180px] max-w-xs flex-1">
                    <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
                    <Input className="h-8 pl-8 text-sm" placeholder="Filter by name or alias…" aria-label="Filter members" value={memberQuery} onChange={(e) => setMemberQuery(e.target.value)} />
                  </div>
                )}
                {memberItems.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1">
                    {(['ALL', ...MEMBER_STATUS_ORDER] as const)
                      .filter((s) => s === 'ALL' || (memberStatusCounts[s] ?? 0) > 0 || memberStatusFilter === s)
                      .map((s) => {
                        const active = memberStatusFilter === s
                        const n = s === 'ALL' ? memberItems.length : (memberStatusCounts[s] ?? 0)
                        return (
                          <button key={s} type="button" onClick={() => setMemberStatusFilter(s)} aria-pressed={active}
                            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                              active
                                ? s === 'ALL' ? 'border-violet-500/60 bg-violet-500/10 text-violet-200' : MEMBER_STATUS_CHIP_ACTIVE[s]
                                : 'border-zinc-800 bg-zinc-900/40 text-zinc-400 hover:text-zinc-300'
                            }`}>
                            {s !== 'ALL' && <span className={`h-1.5 w-1.5 rounded-full ${MEMBER_STATUS_DOT[s]}`} aria-hidden />}
                            {s === 'ALL' ? 'All' : titleCase(s)}
                            <span className="tabular-nums opacity-70">{n}</span>
                          </button>
                        )
                      })}
                  </div>
                )}
                <div className="ml-auto flex items-center gap-2">
                  <button type="button" onClick={() => setPrimaryOnly((v) => !v)} aria-pressed={primaryOnly}
                    title="Only members for whom this is their main set"
                    className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors ${primaryOnly ? 'border-violet-500/60 bg-violet-500/10 text-violet-200' : 'border-zinc-800 bg-zinc-900/40 text-zinc-400 hover:text-zinc-300'}`}>
                    Primary only
                  </button>
                  <Button size="sm" variant="outline" onClick={() => setAddingMember(true)}>
                    <Plus className="mr-1.5 h-3.5 w-3.5" />Add member
                  </Button>
                </div>
              </div>
              {membersLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : memberItems.length === 0 ? (
                <EmptyState icon={Users} title="No members in this set" description="Add an existing member, or create a new one."
                  action={<Button size="sm" onClick={() => setAddingMember(true)}><Plus className="mr-1.5 h-4 w-4" />Add the first member</Button>} />
              ) : filteredMembers.length === 0 ? (
                <EmptyState icon={Search} title="No members match" description="Try another name, alias or status."
                  action={<Button size="sm" variant="outline" onClick={() => { setMemberQuery(''); setMemberStatusFilter('ALL') }}>Clear filters</Button>} />
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full table-fixed text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900">
                        <SortHeader<MemberSortKey> label="Member" col="name" sortKey={memberSortKey} sortDir={memberSortDir} onSort={toggleMemberSort} />
                        <SortHeader<MemberSortKey> label="Status" col="status" className="w-28" sortKey={memberSortKey} sortDir={memberSortDir} onSort={toggleMemberSort} />
                        <SortHeader<MemberSortKey> label="Joined" col="joined" className="hidden w-32 md:table-cell" sortKey={memberSortKey} sortDir={memberSortDir} onSort={toggleMemberSort} />
                        <SortHeader<MemberSortKey> label="Died" col="date_of_death" className="hidden w-32 md:table-cell" sortKey={memberSortKey} sortDir={memberSortDir} onSort={toggleMemberSort} />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/60">
                      {filteredMembers.map((m) => {
                        const linkId = m.slug ?? m.id
                        const spell = spellIn(m, realId)
                        return (
                          <tr key={m.id} className="group transition-colors hover:bg-zinc-900/50">
                            <td className="p-0">
                              <Link to="/members/$id" params={{ id: linkId }} className="flex items-center gap-3 px-3 py-2">
                                <MemberAvatar member={m} />
                                <span className="min-w-0">
                                  <span className="flex items-center gap-1.5">
                                    <span className="truncate font-medium text-white group-hover:text-violet-300">{m.display_name}</span>
                                    <RankBadge rank={spell?.rank ?? null} />
                                  </span>
                                  {m.aliases && m.aliases.length > 0 && (
                                    <span className="block truncate text-[11px] text-zinc-500">{m.aliases.slice(0, 3).join(' · ')}</span>
                                  )}
                                </span>
                              </Link>
                            </td>
                            <td className="px-3 py-2"><MemberStatusBadge status={m.status} /></td>
                            <td className="hidden px-3 py-2 text-xs text-zinc-400 md:table-cell">
                              {spell?.from_date ? <FuzzyDate value={spell.from_date} /> : <None />}
                            </td>
                            <td className="hidden px-3 py-2 text-xs text-zinc-400 md:table-cell">
                              {m.date_of_death ? <FuzzyDate value={m.date_of_death} /> : <None />}
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
            <TabsContent value="incidents" className="mt-4 space-y-3">
              {incidentsLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : incidentItems.length === 0 ? (
                <EmptyState icon={ShieldAlert} title="No incidents recorded" description="Incidents involving members of this set appear here." />
              ) : (
                <>
                  <IncidentsYearStrip data={set.incidents_per_year} />
                  <div className="flex items-center gap-3 text-xs text-zinc-400">
                    <span>Sort</span>
                    {(['date', 'type'] as const).map((k) => (
                      <button key={k} type="button" onClick={() => toggleIncSort(k)} aria-pressed={incSortKey === k}
                        className={`transition-colors hover:text-white ${incSortKey === k ? 'text-zinc-200' : ''}`}>
                        {k === 'date' ? 'Date' : 'Type'} {incSortKey === k ? (incSortDir === 'asc' ? '↑' : '↓') : ''}
                      </button>
                    ))}
                  </div>
                  <div className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {sortedIncidents.map((inc) => <IncidentRow key={inc.id} inc={inc} />)}
                  </div>
                </>
              )}
            </TabsContent>

            {/* Relationships: graph beside the lists; lineage whether or not there are ties. */}
            {!isReserved && (
              <TabsContent value="relationships" className="mt-4">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
                  {relCount === 0 ? (
                    <EmptyState icon={GitFork} title="No allies or enemies yet" description="Mark allied or rival sets to draw the network."
                      action={<Button size="sm" onClick={() => setAddingRel(true)}><Plus className="mr-1.5 h-4 w-4" />Add the first one</Button>} />
                  ) : (
                    <div className="min-w-0 rounded-lg border border-zinc-800 bg-zinc-900/30">
                      <Suspense fallback={<Skeleton className="h-[420px] w-full" />}>
                        <SetRelationshipGraph input={{ centerSetId: set.id, centerSetName: set.name, friendIds: set.friend_ids, enemyIds: set.enemy_ids, sets: [...set.allies, ...set.enemies] }} />
                      </Suspense>
                    </div>
                  )}
                  <div className="min-w-0 space-y-4">
                    <RelationshipsPanel
                      friendIds={set.friend_ids}
                      enemyIds={set.enemy_ids}
                      setMap={setMap}
                      onAdd={() => setAddingRel(true)}
                      onRemove={(sid) => removeRel.mutate(sid)}
                      removingId={removeRel.isPending ? (removeRel.variables as string | undefined) ?? null : null}
                    />
                    {universe && <LineagePanel setId={set.id} setName={set.name} universeId={universe.id} />}
                  </div>
                </div>
              </TabsContent>
            )}

            {!isReserved && universe && (
              <TabsContent value="media" className="mt-4">
                <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                  <PhotoGallery entityType="set" entityId={set.id} universeId={universe.id} />
                </Suspense>
              </TabsContent>
            )}

            <TabsContent value="activity" className="mt-4">
              <ActivityFeed entries={activityData ?? []} loading={activityLoading} setName={set.name} />
            </TabsContent>
          </Tabs>

          {universe && <SetFormSheet universeId={universe.id} open={editing} onClose={() => setEditing(false)} initial={set} />}
          {universe && duplicating && duplicateSeed && (
            <SetFormSheet universeId={universe.id} open={duplicating} onClose={() => setDuplicating(false)} copyFrom={duplicateSeed} />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Set"
            description={`Permanently delete "${set.name}"? This cannot be undone.`}
            impact={(() => {
              // Incidents are not touched: they hang off members, who stay.
              const parts: string[] = []
              if (memberItems.length) parts.push(`${memberItems.length} current member${memberItems.length === 1 ? '' : 's'} lose this affiliation`)
              if (relCount) parts.push(`${relCount} ally and enemy link${relCount === 1 ? '' : 's'} are removed`)
              return parts.length ? <span>{parts.join('; ')}.</span> : null
            })()}
            confirmLabel="Delete"
            destructive
            pending={deleteSet.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />

          {!isReserved && universe && (
            <AddRelationshipDialog setId={set.id} universeId={universe.id} open={addingRel} onClose={() => setAddingRel(false)} existingIds={[...set.friend_ids, ...set.enemy_ids]} />
          )}
          {universe && (
            <AddMemberToSetDialog setId={set.id} setName={set.name} universeId={universe.id} open={addingMember}
              onClose={() => setAddingMember(false)} onCreateNew={() => { setAddingMember(false); setCreatingMember(true) }} />
          )}
          {universe && (
            <MemberFormSheet universeId={universe.id} open={creatingMember} onClose={() => setCreatingMember(false)} defaultSetId={set.id} />
          )}
        </>
      ) : null}
    </div>
  )
}
