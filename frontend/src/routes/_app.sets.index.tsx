import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Pencil, Plus, Search, Shield } from 'lucide-react'
import { useMemo, useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { SetStatusBadge } from '@/components/StatusBadge'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useAlliances, useCreateSet, useSet, useSets, useSetSearch, useUpdateSet } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import type { SetRead, SetStatus } from '@/lib/types'

export const Route = createFileRoute('/_app/sets/')({
  component: SetsPage,
})

// ─── Set avatar ───────────────────────────────────────────────────────────────

const SET_COLORS = [
  'bg-violet-900/60 text-violet-300',
  'bg-blue-900/60 text-blue-300',
  'bg-emerald-900/60 text-emerald-300',
  'bg-amber-900/60 text-amber-300',
  'bg-rose-900/60 text-rose-300',
  'bg-cyan-900/60 text-cyan-300',
  'bg-orange-900/60 text-orange-300',
  'bg-pink-900/60 text-pink-300',
]

function setColor(name: string) {
  let h = 0
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) & 0xffff
  return SET_COLORS[h % SET_COLORS.length]
}

function SetAvatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' }) {
  const sz = size === 'sm' ? 'h-7 w-7 text-xs' : 'h-8 w-8 text-sm'
  return (
    <div className={`${sz} ${setColor(name)} shrink-0 rounded-md flex items-center justify-center font-bold`}>
      {name.slice(0, 2).toUpperCase()}
    </div>
  )
}

// ─── Form sheet ───────────────────────────────────────────────────────────────

interface SetFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: SetRead
  onSaved?: (data: SetRead) => void
}

export function SetFormSheet({ universeId, open, onClose, initial, onSaved }: SetFormProps) {
  const create = useCreateSet()
  const update = useUpdateSet(initial?.id ?? '')
  const isEdit = !!initial

  const [name, setName] = useState(initial?.name ?? '')
  const [alias, setAlias] = useState(initial?.alias ?? '')
  const [bio, setBio] = useState(initial?.bio ?? '')
  const [status, setStatus] = useState<SetStatus>(initial?.status ?? 'ACTIVE')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      if (isEdit) {
        const updated = await update.mutateAsync({ universe_id: universeId, name, alias: alias || null, bio: bio || null, status })
        onSaved?.(updated)
      } else {
        await create.mutateAsync({ universe_id: universeId, name, alias: alias || null, bio: bio || null, status })
        setName(''); setAlias(''); setBio(''); setStatus('ACTIVE')
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} set`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Set' : 'Add Set'}
        description={isEdit ? 'Update this gang set' : 'Create a new gang set in this universe'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="set-name">Name *</Label>
            <Input id="set-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Terror Town" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="set-alias">Alias</Label>
            <Input id="set-alias" value={alias} onChange={(e) => setAlias(e.target.value)} placeholder="Known also as…" />
          </div>
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as SetStatus)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="EXTINCT">Extinct</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="set-bio">Bio</Label>
            <Textarea id="set-bio" value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Background info…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Set'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}

// ─── Lazy edit sheet (fetches full set on open) ───────────────────────────────

function EditSetSheet({ setId, universeId, open, onClose }: {
  setId: string; universeId: string; open: boolean; onClose: () => void
}) {
  const { data: set } = useSet(setId, universeId)
  if (!set) {
    return (
      <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
        <SheetContent title="Edit Set" description="Loading…">
          <div className="space-y-3 pt-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        </SheetContent>
      </Sheet>
    )
  }
  return <SetFormSheet universeId={universeId} open={open} onClose={onClose} initial={set} />
}

// ─── Status filter ────────────────────────────────────────────────────────────

type StatusFilter = 'ALL' | 'ACTIVE' | 'EXTINCT'

function StatusTabs({ value, onChange, counts }: {
  value: StatusFilter
  onChange: (v: StatusFilter) => void
  counts: Record<StatusFilter, number>
}) {
  const tabs: { key: StatusFilter; label: string }[] = [
    { key: 'ALL', label: 'All' },
    { key: 'ACTIVE', label: 'Active' },
    { key: 'EXTINCT', label: 'Extinct' },
  ]
  return (
    <div className="flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1">
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
            value === key
              ? 'bg-zinc-700 text-white'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {label}
          <span className={`tabular-nums ${value === key ? 'text-zinc-300' : 'text-zinc-600'}`}>
            {counts[key]}
          </span>
        </button>
      ))}
    </div>
  )
}

// ─── Sort header ──────────────────────────────────────────────────────────────

type SortKey = 'name' | 'status'

function SortHeader({ label, col, sortKey, sortDir, onSort }: {
  label: string; col: SortKey; sortKey: SortKey | null; sortDir: 'asc' | 'desc'; onSort: (k: SortKey) => void
}) {
  return (
    <th className="px-4 py-2.5 text-left">
      <button
        onClick={() => onSort(col)}
        className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors"
      >
        {label}
        <span className="text-zinc-600">
          {sortKey === col ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
        </span>
      </button>
    </th>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function SetsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')
  const [allianceFilter, setAllianceFilter] = useState<string>('ALL')
  const [sortKey, setSortKey] = useState<SortKey | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const PAGE = 20

  const { data, isLoading } = useSets(universe?.id ?? null, offset)
  const { data: searchResults } = useSetSearch(universe?.id ?? null, q)
  const { data: alliancesData } = useAlliances(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  const allianceMap: Record<string, { name: string; slug: string | null }> = {}
  for (const a of alliancesData?.items ?? []) allianceMap[a.id] = { name: a.name, slug: a.slug }

  const rawItems = q.length >= 2 ? (searchResults ?? []) : (data?.items ?? [])
  const total = data?.total ?? 0

  // Status counts over all loaded items (not filtered)
  const allItems = data?.items ?? []
  const statusCounts: Record<StatusFilter, number> = {
    ALL: allItems.length,
    ACTIVE: allItems.filter((s) => s.status === 'ACTIVE').length,
    EXTINCT: allItems.filter((s) => s.status === 'EXTINCT').length,
  }

  // Unique alliances present in the list
  const alliancesInList = Array.from(
    new Set(allItems.map((s) => s.alliance_id).filter(Boolean) as string[])
  )

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const items = useMemo(() => {
    let filtered = rawItems
    if (statusFilter !== 'ALL') filtered = filtered.filter((s) => s.status === statusFilter)
    if (allianceFilter !== 'ALL') filtered = filtered.filter((s) =>
      allianceFilter === 'NONE' ? !s.alliance_id : s.alliance_id === allianceFilter
    )
    if (!sortKey) return filtered
    return [...filtered].sort((a, b) => {
      const av = String(a[sortKey] ?? '')
      const bv = String(b[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [rawItems, statusFilter, allianceFilter, sortKey, sortDir])

  const activeCount = allItems.filter((s) => s.status === 'ACTIVE').length
  const extinctCount = allItems.filter((s) => s.status === 'EXTINCT').length

  return (
    <div>
      <PageHeader
        title="Sets"
        description={
          isLoading ? undefined :
          total === 0 ? 'No sets yet' :
          [activeCount > 0 && `${activeCount} active`, extinctCount > 0 && `${extinctCount} extinct`]
            .filter(Boolean).join(' · ') || `${total} total`
        }
        action={
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus className="mr-1.5 h-4 w-4" />Add Set
          </Button>
        }
      />

      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input
            className="pl-8"
            placeholder="Search sets…"
            value={q}
            onChange={(e) => { setQ(e.target.value); setOffset(0) }}
          />
        </div>

        {!q && <StatusTabs value={statusFilter} onChange={setStatusFilter} counts={statusCounts} />}

        {!q && alliancesInList.length > 0 && (
          <Select value={allianceFilter} onValueChange={setAllianceFilter}>
            <SelectTrigger className="h-8 w-auto min-w-32 text-xs">
              <SelectValue placeholder="Alliance" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All alliances</SelectItem>
              <SelectItem value="NONE">No alliance</SelectItem>
              {alliancesInList.map((id) => (
                <SelectItem key={id} value={id}>{allianceMap[id]?.name ?? id}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        <Button
          variant="outline" size="sm" className="ml-auto"
          onClick={() => downloadCsv(`/sets/?universe_id=${universe.id}&format=csv`, 'sets.csv')}
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-zinc-900/90 backdrop-blur">
            <tr className="border-b border-zinc-800">
              <SortHeader label="Set" col="name" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
              <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Alliance</th>
              <SortHeader label="Status" col="status" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
              <th className="w-8" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading && !q
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={4}>
                      <div className="flex items-center gap-3">
                        <Skeleton className="h-8 w-8 rounded-md" />
                        <Skeleton className="h-4 w-40" />
                      </div>
                    </td>
                  </tr>
                ))
              : items.map((set) => {
                  const linkId = set.slug ?? set.id
                  const alliance = set.alliance_id ? allianceMap[set.alliance_id] : null
                  return (
                    <tr key={set.id} className="group hover:bg-zinc-900/50 transition-colors">
                      {/* Name + alias */}
                      <td className="p-0">
                        <Link
                          to="/sets/$id"
                          params={{ id: linkId }}
                          className="flex items-center gap-3 px-4 py-3"
                        >
                          <SetAvatar name={set.name} />
                          <div>
                            <p className="font-medium text-white group-hover:text-violet-400 transition-colors">
                              {set.name}
                            </p>
                            {set.alias && (
                              <p className="text-xs text-zinc-500">{set.alias}</p>
                            )}
                          </div>
                        </Link>
                      </td>

                      {/* Alliance */}
                      <td className="px-4 py-3">
                        {alliance ? (
                          <Link
                            to="/alliances/$id"
                            params={{ id: alliance.slug ?? set.alliance_id! }}
                            className="inline-flex items-center rounded-full bg-blue-950/60 px-2.5 py-0.5 text-xs font-medium text-blue-300 ring-1 ring-blue-800/50 hover:ring-blue-600 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {alliance.name}
                          </Link>
                        ) : (
                          <span className="text-xs text-zinc-700">—</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3">
                        <SetStatusBadge status={set.status} />
                      </td>

                      {/* Quick edit */}
                      <td className="pr-3 py-3">
                        <button
                          onClick={() => setEditingId(set.id)}
                          className="invisible group-hover:visible rounded p-1 text-zinc-600 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                          title="Edit"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <div className="flex flex-col items-center py-12 text-center">
                    <Shield className="mb-3 h-8 w-8 text-zinc-700" />
                    <p className="text-sm text-zinc-500">
                      {q
                        ? `No sets match "${q}"`
                        : statusFilter !== 'ALL'
                        ? `No ${statusFilter.toLowerCase()} sets`
                        : 'No sets yet'}
                    </p>
                    {!q && statusFilter === 'ALL' && (
                      <button
                        onClick={() => setCreating(true)}
                        className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors"
                      >
                        Create the first set →
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {!q && total > PAGE && (
        <div className="mt-4 flex items-center justify-between text-sm text-zinc-400">
          <span>Showing {offset + 1}–{Math.min(offset + PAGE, total)} of {total}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Prev</Button>
            <Button variant="outline" size="sm" disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>Next</Button>
          </div>
        </div>
      )}

      <SetFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingId && (
        <EditSetSheet
          setId={editingId}
          universeId={universe.id}
          open={!!editingId}
          onClose={() => setEditingId(null)}
        />
      )}
    </div>
  )
}
