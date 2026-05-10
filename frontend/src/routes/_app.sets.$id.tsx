import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Activity, Copy, Crosshair, Download, GitFork, Image as ImageIcon, ListTree, MapPin, MoreHorizontal, Pencil, Plus, Search, ShieldAlert, Skull, Swords, Trash2, Users, X } from 'lucide-react'
import { useEffect, useMemo, useState, lazy, Suspense } from 'react'
import { toast } from 'sonner'
import {
  useSetDetail, useDeleteSet, useUpdateSet,
  useAddSetRelationship, useRemoveSetRelationship,
  useSetMembers, useSetIncidents, useSets, useSetActivity,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { StatCard } from '@/components/StatCard'
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
import { SetAvatar, SetFormSheet } from './_app.sets.index'
import { MemberAvatar, MemberFormSheet } from './_app.members.index'
import { AddMemberToSetDialog } from '@/components/AddMemberToSetDialog'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'
import { INCIDENT_TYPE_CHIP } from '@/lib/incidentColors'
import type { IncidentListItem, MemberListItem, NameVariant, SetReadDetailFull } from '@/lib/types'

function variantLead(v: NameVariant): 'name' | 'initials' | 'number' | null {
  if (v.lead && v[v.lead]?.trim()) return v.lead
  if (v.name?.trim()) return 'name'
  if (v.initials?.trim()) return 'initials'
  if (v.number?.trim()) return 'number'
  return null
}

function formatNameVariant(v: NameVariant): string {
  const lead = variantLead(v)
  if (!lead) return ''
  const head = (v[lead] ?? '').trim()
  const extras: string[] = []
  for (const slot of ['name', 'initials', 'number'] as const) {
    if (slot === lead) continue
    const val = v[slot]?.trim()
    if (val) extras.push(val)
  }
  return extras.length > 0 ? `${head} (${extras.join(' · ')})` : head
}

function nonPrimaryVariantStrings(variants?: NameVariant[] | null): string[] {
  return (variants ?? []).filter((v) => !v.is_primary).map(formatNameVariant).filter(Boolean)
}

const SetRelationshipGraph = lazy(() =>
  import('@/components/graphs/SetRelationshipGraph').then((m) => ({ default: m.SetRelationshipGraph })),
)
const PhotoGallery = lazy(() =>
  import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })),
)

const TAB_KEYS = ['overview', 'members', 'incidents', 'relationships', 'media', 'activity'] as const
type TabKey = typeof TAB_KEYS[number]

interface SetSearch {
  tab?: TabKey
}

export const Route = createFileRoute('/_app/sets/$id')({
  validateSearch: (s: Record<string, unknown>): SetSearch => ({
    tab: typeof s.tab === 'string' && (TAB_KEYS as readonly string[]).includes(s.tab) ? (s.tab as TabKey) : undefined,
  }),
  component: SetDetailPage,
})

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
      <div className="mb-1.5 flex items-baseline justify-between text-[10px] uppercase tracking-wider text-zinc-600">
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
              className={`flex-1 rounded-sm transition-colors ${c === 0 ? 'bg-zinc-800/40' : 'bg-violet-500/70 hover:bg-violet-400'}`}
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
            <h3 className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-zinc-500">{label}</h3>
            <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-900/30">
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
                        <span className="text-zinc-500">{verb} {noun}</span>
                        <Link {...linkTo} className="font-medium text-violet-400 hover:underline truncate">
                          {target}
                        </Link>
                        <span className="ml-auto font-mono text-[11px] tabular-nums text-zinc-600">{time}</span>
                      </div>
                      {showKeys && (
                        <div className="mt-0.5 flex flex-wrap gap-1 text-[10px] text-zinc-500">
                          {e.diff_keys.slice(0, 6).map((k) => (
                            <span key={k} className="rounded bg-zinc-800/60 px-1.5 py-0.5">{k}</span>
                          ))}
                          {e.diff_keys.length > 6 && <span className="text-zinc-600">+{e.diff_keys.length - 6}</span>}
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
  const akaList = nonPrimaryVariantStrings(set.name_variants)
  if (akaList.length > 0) {
    lines.push('')
    lines.push(`*a/k/a ${akaList.join(', ')}*`)
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
  const search = Route.useSearch()
  const tab: TabKey = search.tab ?? 'overview'
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const setTab = (next: TabKey) => navigate({ to: '/sets/$id', params: { id }, search: (s) => ({ ...s, tab: next === 'overview' ? undefined : next }), replace: true })

  // 1–6 keyboard shortcuts to switch tabs (ignored when typing).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      const t = e.target as HTMLElement | null
      if (t && (t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))) return
      const idx = '123456'.indexOf(e.key)
      if (idx === -1) return
      e.preventDefault()
      setTab(TAB_KEYS[idx])
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const { data: set, isLoading, isError, refetch } = useSetDetail(id, universe?.id ?? null)
  const realId = set?.id ?? ''
  const stats = set?.stats
  const { data: membersData } = useSetMembers(realId, universe?.id ?? null)
  const { data: incidentsData } = useSetIncidents(realId, universe?.id ?? null)
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

  // Members section state
  const [memberQuery, setMemberQuery] = useState('')
  const [memberStatusFilter, setMemberStatusFilter] = useState<string>('ALL')
  const [memberSortKey, setMemberSortKey] = useState<'name' | 'status' | 'date_of_death'>('name')
  const [memberSortDir, setMemberSortDir] = useState<SortDir>('asc')
  const [memberDense, setMemberDense] = useState<boolean>(() => {
    if (typeof localStorage === 'undefined') return false
    return localStorage.getItem('sw:set-members-dense') === '1'
  })
  useEffect(() => {
    if (typeof localStorage === 'undefined') return
    localStorage.setItem('sw:set-members-dense', memberDense ? '1' : '0')
  }, [memberDense])

  // Incidents section state
  const [incSortKey, setIncSortKey] = useState<'date' | 'type'>('date')
  const [incSortDir, setIncSortDir] = useState<SortDir>('desc')

  useEditShortcut(() => set && setEditing(true))

  // Derive everything from the denormalized detail payload — no extra queries.
  const setMap: Record<string, { name: string; slug: string | null }> = {}
  for (const a of set?.allies ?? []) setMap[a.id] = { name: a.name, slug: a.slug }
  for (const e of set?.enemies ?? []) setMap[e.id] = { name: e.name, slug: e.slug }
  const setName = (sid: string) => setMap[sid]?.name ?? sid

  const alliance = set?.alliance_id && set.alliance_name
    ? { id: set.alliance_id, name: set.alliance_name, slug: set.alliance_slug }
    : null
  const muni = set?.municipality_name ? { name: set.municipality_name } : null
  const territoryNames = (set?.territories ?? [])
    .map((t) => t.name)
    .sort((a, b) => a.localeCompare(b))

  const founder = set?.founder_id && set.founder_display_name
    ? { id: set.founder_id, display_name: set.founder_display_name, slug: set.founder_slug }
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

  const memberStatusCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const m of memberItems) c[m.status] = (c[m.status] ?? 0) + 1
    return c
  }, [memberItems])

  const filteredMembers = useMemo(() => {
    const q = memberQuery.trim().toLowerCase()
    let rows = memberItems
    if (memberStatusFilter !== 'ALL') {
      rows = rows.filter((m) => m.status === memberStatusFilter)
    }
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
  }, [memberItems, memberQuery, memberStatusFilter, memberSortKey, memberSortDir])

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
              <SetAvatar
                name={set.name}
                thumbUrl={set.primary_photo_url}
                size="xl"
                isReserved={isReserved}
              />
              {/* Wrap text column so the avatar grid still works */}
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold leading-none text-white">{set.name}</h1>
                  <CopyButton value={window.location.href} label="Copy link to this set" className="opacity-40 hover:opacity-100" />
                </div>
                {(() => {
                  const variants = set.name_variants ?? []
                  const primary = variants.find((v) => v.is_primary)
                  const others = variants.filter((v) => !v.is_primary)
                  if (!primary && others.length === 0) return null
                  const primaryExtras = primary
                    ? (['name', 'initials', 'number'] as const)
                        .filter((slot) => slot !== variantLead(primary) && primary[slot]?.trim())
                        .map((slot) => ({ slot, value: primary[slot]!.trim() }))
                    : []
                  return (
                    <div className="mt-1 space-y-1">
                      {primaryExtras.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 text-xs">
                          {primaryExtras.map(({ slot, value }) => (
                            <span
                              key={slot}
                              className="inline-flex items-center gap-1 rounded-full bg-zinc-800/70 px-2 py-0.5 text-zinc-300"
                            >
                              <span className="text-[10px] uppercase tracking-wider text-zinc-500">{slot}</span>
                              {value}
                            </span>
                          ))}
                        </div>
                      )}
                      {others.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 text-xs">
                          <span className="text-[10px] uppercase tracking-wider text-zinc-600">a/k/a</span>
                          {others.map((v, i) => {
                            const lead = variantLead(v)
                            if (!lead) return null
                            const head = v[lead]!.trim()
                            const extras = (['name', 'initials', 'number'] as const)
                              .filter((slot) => slot !== lead && v[slot]?.trim())
                              .map((slot) => v[slot]!.trim())
                            return (
                              <span
                                key={i}
                                className="inline-flex items-center gap-1 rounded-full border border-zinc-800 bg-zinc-900/60 px-2 py-0.5 text-zinc-400"
                              >
                                <span className="text-zinc-200">{head}</span>
                                {extras.length > 0 && (
                                  <span className="text-zinc-600">· {extras.join(' · ')}</span>
                                )}
                              </span>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )
                })()}
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
              <Button size="sm" variant="outline" onClick={() => setEditing(true)} title="Edit (e)">
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="outline" aria-label="More actions">
                    <MoreHorizontal className="h-3.5 w-3.5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {!isReserved && (
                    <DropdownMenuItem onClick={() => setDuplicating(true)}>
                      <Copy className="mr-2 h-3.5 w-3.5" />Duplicate
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={handleExport}>
                    <Download className="mr-2 h-3.5 w-3.5" />Export Markdown
                  </DropdownMenuItem>
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

          {/* KPI grouping — primary 3-up cards, secondary inline strip. */}
          {stats && !allStatsZero && (
            <div className="space-y-2">
              <div className="grid grid-cols-3 gap-2">
                <StatCard icon={Users} label="Members" value={stats.member_count} accent="violet" />
                <StatCard icon={Crosshair} label="Shootings" value={stats.total_shootings} accent="amber" />
                <StatCard icon={Skull} label="Kills" value={stats.total_kills} accent="red" />
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-xs text-zinc-500">
                <span><span className="text-zinc-300 tabular-nums">{stats.active_member_count}</span> active</span>
                <span><span className="text-zinc-300 tabular-nums">{stats.dead_members}</span> dead</span>
                <span><span className="text-zinc-300 tabular-nums">{stats.total_assists}</span> assists</span>
                <span>
                  Last incident{' '}
                  <span className="text-zinc-300 tabular-nums">{stats.last_incident_year ?? '—'}</span>
                  {stats.first_incident_year && stats.first_incident_year !== stats.last_incident_year && (
                    <span className="text-zinc-600"> (since {stats.first_incident_year})</span>
                  )}
                </span>
              </div>
            </div>
          )}

          <Tabs value={tab} onValueChange={(v) => setTab(v as TabKey)} className="w-full">
            <TabsList className="h-auto flex-wrap bg-zinc-950/50 p-0.5">
              <TabsTrigger value="overview" title="Overview (1)"><ListTree className="mr-1.5 h-3.5 w-3.5" />Overview</TabsTrigger>
              <TabsTrigger value="members" title="Members (2)">
                <Users className="mr-1.5 h-3.5 w-3.5" />Members
                {memberItems.length > 0 && <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-[10px]">{memberItems.length}</Badge>}
              </TabsTrigger>
              <TabsTrigger value="incidents" title="Incidents (3)">
                <ShieldAlert className="mr-1.5 h-3.5 w-3.5" />Incidents
                {incidentCount > 0 && <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-[10px]">{incidentCount}</Badge>}
              </TabsTrigger>
              {!isReserved && (
                <TabsTrigger value="relationships" title="Relationships (4)">
                  <GitFork className="mr-1.5 h-3.5 w-3.5" />Relationships
                  {(set.friend_ids.length + set.enemy_ids.length) > 0 && (
                    <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-[10px]">
                      {set.friend_ids.length + set.enemy_ids.length}
                    </Badge>
                  )}
                </TabsTrigger>
              )}
              {!isReserved && (
                <TabsTrigger value="media" title="Media (5)"><ImageIcon className="mr-1.5 h-3.5 w-3.5" />Media</TabsTrigger>
              )}
              <TabsTrigger value="activity" title="Activity (6)"><Activity className="mr-1.5 h-3.5 w-3.5" />Activity</TabsTrigger>
            </TabsList>

            {/* Overview: facts + ally/enemy strip + latest incidents + top members */}
            <TabsContent value="overview" className="mt-4 space-y-4">
              {/* Bio — saved bio renders as a card; empty state is a quiet CTA. */}
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
              ) : !isReserved ? (
                <button type="button" onClick={startBioEdit}
                  className="flex w-full items-center gap-2 rounded-xl border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-600 hover:border-zinc-700 hover:text-zinc-400 transition-colors">
                  <Pencil className="h-3 w-3" />Add bio
                </button>
              ) : null}

              {isReserved && (
                <div className="rounded-lg border border-zinc-700 bg-zinc-900/50 px-4 py-3 text-sm text-zinc-400">
                  <span className="font-medium text-zinc-300">System set.</span>{' '}
                  Used for incident attribution when the actor is a {set.name.toLowerCase()} (not a real crew).
                  Only the bio can be edited; this set cannot be renamed, reassigned, or deleted.
                </div>
              )}

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

              {/* Top-3 latest incidents — quick digest */}
              {incidentItems.length > 0 && (
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Latest incidents</h3>
                    <button type="button" onClick={() => setTab('incidents')} className="text-xs text-zinc-500 hover:text-violet-400">
                      View all {incidentItems.length} →
                    </button>
                  </div>
                  <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-900/30">
                    {sortedIncidents.slice(0, 3).map((inc) => (
                      <li key={inc.id}>
                        <Link to="/incidents/$id" params={{ id: inc.id }} className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-zinc-900/60">
                          <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${INCIDENT_TYPE_CHIP[inc.type]}`}>{inc.type}</span>
                          <span className="font-mono text-xs text-zinc-400 tabular-nums">
                            {inc.date ? <FuzzyDate value={inc.date} /> : 'Unknown'}
                          </span>
                          {inc.victim_names.length > 0 && (
                            <span className="truncate text-xs text-zinc-500">
                              {inc.victim_names.slice(0, 3).join(', ')}{inc.victim_names.length > 3 && ` +${inc.victim_names.length - 3}`}
                            </span>
                          )}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </TabsContent>

            {/* Members tab — existing table */}
            <TabsContent value="members" className="mt-4"><section>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-1 flex-wrap items-center gap-2">
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
                {memberItems.length > 0 && Object.keys(memberStatusCounts).length > 1 && (
                  <div className="flex flex-wrap items-center gap-1">
                    {(['ALL', 'FREE', 'LOCKED', 'DEAD', 'UNKNOWN', 'ESCAPEE', 'ABSCONDER'] as const)
                      .filter((s) => s === 'ALL' || (memberStatusCounts[s] ?? 0) > 0)
                      .map((s) => {
                        const active = memberStatusFilter === s
                        const n = s === 'ALL' ? memberItems.length : (memberStatusCounts[s] ?? 0)
                        return (
                          <button
                            key={s}
                            type="button"
                            onClick={() => setMemberStatusFilter(s)}
                            aria-pressed={active}
                            className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                              active
                                ? 'border-violet-500/60 bg-violet-500/10 text-violet-200'
                                : 'border-zinc-800 bg-zinc-900/40 text-zinc-500 hover:text-zinc-300'
                            }`}
                          >
                            {s === 'ALL' ? 'All' : s.charAt(0) + s.slice(1).toLowerCase()}
                            <span className="ml-1 tabular-nums opacity-60">{n}</span>
                          </button>
                        )
                      })}
                  </div>
                )}
                {(memberQuery || memberStatusFilter !== 'ALL') && filteredMembers.length !== memberItems.length && (
                  <span className="text-xs text-zinc-500 tabular-nums">
                    {filteredMembers.length} of {memberItems.length}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setMemberDense((d) => !d)}
                  title={memberDense ? 'Comfortable rows' : 'Dense rows'}
                  className="rounded-md border border-zinc-800 bg-zinc-900/40 px-2 py-1 text-[11px] text-zinc-400 hover:text-zinc-200"
                >
                  {memberDense ? 'Comfortable' : 'Dense'}
                </button>
                <Button size="sm" variant="outline" onClick={() => setAddingMember(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Member
                </Button>
              </div>
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
                  <thead className="sticky top-0 z-10">
                    <tr className="border-b border-zinc-800 bg-zinc-900">
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
                      const cellPad = memberDense ? 'py-1.5' : 'py-3'
                      return (
                        <tr key={m.id} className={`group hover:bg-zinc-900/50 transition-colors ${isDead ? 'opacity-60' : ''}`}>
                          <td className={`px-3 ${cellPad}`}><MemberAvatar member={m} /></td>
                          <td className="p-0">
                            <Link
                              to="/members/$id"
                              params={{ id: linkId }}
                              className={`block px-3 ${cellPad} transition-colors group-hover:text-violet-400`}
                            >
                              <span className="inline-flex items-center gap-1.5">
                                <span className={`font-medium ${isDead ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'}`}>
                                  {m.display_name}
                                </span>
                                {m.set_rank === 'CEO' && (
                                  <span
                                    title="CEO"
                                    className="inline-flex items-center rounded-md border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-300"
                                  >
                                    CEO
                                  </span>
                                )}
                                {m.set_rank === 'CO_CEO' && (
                                  <span
                                    title="Co-CEO"
                                    className="inline-flex items-center rounded-md border border-amber-600/30 bg-amber-600/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-400"
                                  >
                                    Co-CEO
                                  </span>
                                )}
                              </span>
                              {m.aliases && m.aliases.length > 0 && (
                                <span className="mt-0.5 block text-[11px] text-zinc-600 group-hover:text-zinc-500 transition-colors">
                                  {m.aliases.slice(0, 3).join(' · ')}
                                </span>
                              )}
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/members/$id" params={{ id: linkId }} className={`block px-4 ${cellPad}`} tabIndex={-1}>
                              <MemberStatusBadge status={m.status} />
                            </Link>
                          </td>
                          <td className="hidden p-0 md:table-cell">
                            <Link to="/members/$id" params={{ id: linkId }} className={`block px-4 ${cellPad} text-xs text-zinc-500`} tabIndex={-1}>
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
          </section></TabsContent>

          {/* Incidents tab — existing table */}
          <TabsContent value="incidents" className="mt-4"><section className="space-y-3">
            {incidentCount === 0 ? (
              <EmptyState
                icon={ShieldAlert}
                title="No incidents recorded"
                description="Incidents involving members of this set will appear here."
              />
            ) : (
              <>
                <IncidentsYearStrip data={set.incidents_per_year} />
                <div className="overflow-hidden rounded-xl border border-zinc-800">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 z-10">
                    <tr className="border-b border-zinc-800 bg-zinc-900">
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
                      const muniName = inc.municipality_name
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
              </>
            )}
          </section></TabsContent>

          {/* Relationships tab — full-width inline graph + add controls */}
          {!isReserved && (
            <TabsContent value="relationships" className="mt-4 space-y-4">
              <div className="flex items-center justify-end">
                <Button size="sm" variant="outline" onClick={() => setAddingRel(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Relationship
                </Button>
              </div>
              {(set.friend_ids.length + set.enemy_ids.length) === 0 ? (
                <EmptyState
                  icon={GitFork}
                  title="No relationships yet"
                  description="Mark allied or rival sets to power the network graph."
                  action={
                    <Button size="sm" onClick={() => setAddingRel(true)}>
                      <Plus className="mr-1.5 h-4 w-4" />Add the first relationship
                    </Button>
                  }
                />
              ) : (
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_280px]">
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
                    <Suspense fallback={<Skeleton className="h-[420px] w-full" />}>
                      <SetRelationshipGraph
                        input={{
                          centerSetId: set.id,
                          centerSetName: set.name,
                          friendIds: set.friend_ids,
                          enemyIds: set.enemy_ids,
                          sets: [...set.allies, ...set.enemies],
                        }}
                      />
                    </Suspense>
                  </div>
                  <RelationshipsPanel
                    friendIds={set.friend_ids}
                    enemyIds={set.enemy_ids}
                    setMap={setMap}
                    onAdd={() => setAddingRel(true)}
                    onOpenGraph={() => { /* graph already inline */ }}
                    onRemove={(sid) => removeRel.mutate(sid)}
                    removingId={removeRel.isPending ? (removeRel.variables as string | undefined) ?? null : null}
                  />
                </div>
              )}
            </TabsContent>
          )}

          {/* Media tab — existing PhotoGallery */}
          {!isReserved && universe && (
            <TabsContent value="media" className="mt-4">
              <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                <PhotoGallery entityType="set" entityId={set.id} universeId={universe.id} />
              </Suspense>
            </TabsContent>
          )}

          {/* Activity tab — audit feed scoped to set + its members, lazy-loaded */}
          <TabsContent value="activity" className="mt-4">
            <ActivityFeed
              entries={activityData ?? []}
              loading={activityLoading}
              setName={set.name}
            />
          </TabsContent>
          </Tabs>

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
