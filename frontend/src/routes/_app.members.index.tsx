import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Plus, Search, Users, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import {
  useCreateMember, useMembers, useMemberSearch, useUpdateMember,
  useSets, useAlliances, useBulkMemberStatus,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import type { MemberListItem, MemberRead, MemberStatus } from '@/lib/types'
import type { FuzzyDateValue } from '@/components/FuzzyDate'

export const Route = createFileRoute('/_app/members/')({
  component: MembersPage,
})

// ─── Status styling ───────────────────────────────────────────────────────────

const STATUS_AVATAR: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-900 text-emerald-300',
  LOCKED: 'bg-orange-900 text-orange-300',
  DEAD: 'bg-zinc-800 text-zinc-500',
  UNKNOWN: 'bg-zinc-800 text-zinc-500',
  ESCAPEE: 'bg-amber-900 text-amber-300',
  ABSCONDER: 'bg-yellow-900 text-yellow-300',
}

const STATUS_DOT: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-400',
  LOCKED: 'bg-orange-400',
  DEAD: 'bg-zinc-600',
  UNKNOWN: 'bg-zinc-600',
  ESCAPEE: 'bg-amber-400',
  ABSCONDER: 'bg-yellow-400',
}

const STATUS_CHIP_ACTIVE: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-900/60 text-emerald-300 border-emerald-700',
  LOCKED: 'bg-orange-900/60 text-orange-300 border-orange-700',
  DEAD: 'bg-zinc-800 text-zinc-400 border-zinc-600',
  UNKNOWN: 'bg-zinc-800 text-zinc-400 border-zinc-600',
  ESCAPEE: 'bg-amber-900/60 text-amber-300 border-amber-700',
  ABSCONDER: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
}

const ALL_STATUSES: MemberStatus[] = ['FREE', 'LOCKED', 'ESCAPEE', 'ABSCONDER', 'DEAD', 'UNKNOWN']

function initials(name: string) {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

// ─── Form sheet ───────────────────────────────────────────────────────────────

interface MemberFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: MemberRead
  defaultSetId?: string
}

export function MemberFormSheet({ universeId, open, onClose, initial, defaultSetId }: MemberFormProps) {
  const create = useCreateMember()
  const update = useUpdateMember(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const { data: sets } = useSets(universeId)
  const { data: alliances } = useAlliances(universeId)

  const [nickname, setNickname] = useState(initial?.nickname ?? '')
  const [legalName, setLegalName] = useState(initial?.legal_name ?? '')
  const [nicknameUnknown, setNicknameUnknown] = useState(initial?.nickname_unknown ?? false)
  const [status, setStatus] = useState<MemberStatus>(initial?.status ?? 'UNKNOWN')
  const [setId, setSetId] = useState<string>(initial?.set_id ?? defaultSetId ?? '')
  const [allianceId, setAllianceId] = useState<string>(initial?.alliance_id ?? '')
  const [biography, setBiography] = useState(initial?.biography ?? '')
  const [photoUrl, setPhotoUrl] = useState(initial?.photo_url ?? '')
  const [aliases, setAliases] = useState(initial?.aliases?.join(', ') ?? '')
  const [dateOfDeath, setDateOfDeath] = useState<FuzzyDateValue | null>(initial?.date_of_death ?? null)
  const [releaseDate, setReleaseDate] = useState<FuzzyDateValue | null>(initial?.release_date ?? null)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const aliasList = aliases.split(',').map((s) => s.trim()).filter(Boolean)
    const body: Record<string, unknown> = {
      universe_id: universeId,
      nickname: nickname || null,
      legal_name: legalName || null,
      nickname_unknown: nicknameUnknown,
      status,
      set_id: setId || null,
      alliance_id: allianceId || null,
      biography,
      photo_url: photoUrl || null,
      aliases: aliasList.length > 0 ? aliasList : null,
      date_of_death: status === 'DEAD' ? dateOfDeath : null,
      release_date: status === 'LOCKED' ? releaseDate : null,
    }
    try {
      if (isEdit) await update.mutateAsync(body)
      else await create.mutateAsync(body)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} member`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Member' : 'Add Member'}
        description={isEdit ? 'Update this member' : 'Create a new member profile'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="m-nickname">Nickname</Label>
            <Input id="m-nickname" value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="Street name" disabled={nicknameUnknown} />
          </div>
          <div className="flex items-center gap-2">
            <input id="m-nku" type="checkbox" checked={nicknameUnknown} onChange={(e) => setNicknameUnknown(e.target.checked)} className="rounded border-zinc-700 bg-zinc-900 accent-violet-600" />
            <label htmlFor="m-nku" className="text-sm text-zinc-300">Nickname unknown (use legal name as display)</label>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-legal">Legal Name</Label>
            <Input id="m-legal" value={legalName} onChange={(e) => setLegalName(e.target.value)} placeholder="Full legal name" />
          </div>
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as MemberStatus)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {ALL_STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          {status === 'DEAD' && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
              <FuzzyDateInput value={dateOfDeath} onChange={setDateOfDeath} label="Date of death" idPrefix="dod" />
            </div>
          )}
          {status === 'LOCKED' && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
              <FuzzyDateInput value={releaseDate} onChange={setReleaseDate} label="Expected release date" idPrefix="rel" />
            </div>
          )}
          <div className="space-y-1.5">
            <Label>Set</Label>
            <Select value={setId || 'none'} onValueChange={(v) => setSetId(v === 'none' ? '' : v)}>
              <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">— None —</SelectItem>
                {(sets?.items ?? []).map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Alliance</Label>
            <Select value={allianceId || 'none'} onValueChange={(v) => setAllianceId(v === 'none' ? '' : v)}>
              <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">— None —</SelectItem>
                {(alliances?.items ?? []).map((a) => <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-aliases">Aliases (comma-separated)</Label>
            <Input id="m-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. Big L, Lucky" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-photo">Photo URL</Label>
            <Input id="m-photo" type="url" value={photoUrl} onChange={(e) => setPhotoUrl(e.target.value)} placeholder="https://…" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-bio">Biography</Label>
            <Textarea id="m-bio" rows={5} value={biography} onChange={(e) => setBiography(e.target.value)} placeholder="Background notes…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Member'}
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

// ─── Main page ────────────────────────────────────────────────────────────────

function MembersPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkStatus, setBulkStatus] = useState<MemberStatus>('FREE')
  const [statusFilter, setStatusFilter] = useState<MemberStatus | null>(null)
  const [setFilter, setSetFilter] = useState<string>('')
  const [sortKey, setSortKey] = useState<'display_name' | 'status' | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const bulkUpdate = useBulkMemberStatus(universe?.id ?? '')

  const { data, isLoading } = useMembers(universe?.id ?? null, cursor)
  const { data: searchResults } = useMemberSearch(universe?.id ?? null, q)
  const { data: setsData } = useSets(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  const setMap = useMemo(() => {
    const m: Record<string, { name: string; slug: string | null }> = {}
    for (const s of setsData?.items ?? []) m[s.id] = { name: s.name, slug: s.slug }
    return m
  }, [setsData])

  const baseItems = q.length >= 2 ? (searchResults ?? []) : (data?.items ?? [])
  const total = data?.total

  // Status counts from full unfiltered list
  const statusCounts = useMemo(() => {
    const counts: Partial<Record<MemberStatus, number>> = {}
    for (const m of baseItems) counts[m.status] = (counts[m.status] ?? 0) + 1
    return counts
  }, [baseItems])

  function toggleSort(key: 'display_name' | 'status') {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const items: MemberListItem[] = useMemo(() => {
    let list = baseItems
    if (statusFilter) list = list.filter((m) => m.status === statusFilter)
    if (setFilter) list = list.filter((m) => m.set_id === setFilter)
    if (!sortKey) return list
    return [...list].sort((a, b) => {
      const av = String((a as any)[sortKey] ?? '')
      const bv = String((b as any)[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [baseItems, statusFilter, setFilter, sortKey, sortDir])

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    setSelected(selected.size === items.length ? new Set() : new Set(items.map((m) => m.id)))
  }

  async function applyBulkStatus() {
    if (selected.size === 0) return
    await bulkUpdate.mutateAsync({ member_ids: Array.from(selected), status: bulkStatus })
    setSelected(new Set())
  }

  const hasFilters = statusFilter || setFilter

  return (
    <div className="pb-20">
      {/* Header */}
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Members</h1>
          {total != null && (
            <p className="mt-0.5 text-sm text-zinc-500">{total} total</p>
          )}
        </div>
        <Button size="sm" onClick={() => setCreating(true)}>
          <Plus className="mr-1.5 h-4 w-4" />Add Member
        </Button>
      </div>

      {/* Status filter chips */}
      {!isLoading && baseItems.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-1.5">
          {ALL_STATUSES.filter((s) => (statusCounts[s] ?? 0) > 0).map((s) => {
            const active = statusFilter === s
            return (
              <button
                key={s}
                onClick={() => setStatusFilter(active ? null : s)}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all ${
                  active
                    ? STATUS_CHIP_ACTIVE[s]
                    : 'border-zinc-800 bg-zinc-900/40 text-zinc-500 hover:border-zinc-700 hover:text-zinc-300'
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[s]}`} />
                {s}
                <span className={active ? 'opacity-70' : 'opacity-50'}>{statusCounts[s]}</span>
              </button>
            )
          })}
          {hasFilters && (
            <button
              onClick={() => { setStatusFilter(null); setSetFilter('') }}
              className="flex items-center gap-1 rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-500 hover:text-white transition-colors"
            >
              <X className="h-3 w-3" /> Clear filters
            </button>
          )}
        </div>
      )}

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8 h-8 text-sm" placeholder="Search members…" value={q} onChange={(e) => { setQ(e.target.value); setCursor(undefined) }} />
        </div>

        {/* Set filter */}
        <Select value={setFilter || 'all'} onValueChange={(v) => setSetFilter(v === 'all' ? '' : v)}>
          <SelectTrigger className="h-8 w-36 text-xs"><SelectValue placeholder="All sets" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all" className="text-xs">All sets</SelectItem>
            {(setsData?.items ?? []).map((s) => (
              <SelectItem key={s.id} value={s.id} className="text-xs">{s.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button variant="outline" size="sm" className="h-8" onClick={() => downloadCsv(`/members/?universe_id=${universe.id}&format=csv`, 'members.csv')}>
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/60">
              <th className="w-10 px-3 py-2.5">
                <input
                  type="checkbox"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={toggleAll}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              <th className="px-3 py-2.5 w-8" />
              <th className="px-3 py-2.5 text-left">
                <button onClick={() => toggleSort('display_name')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors">
                  Name <span className="text-zinc-600">{sortKey === 'display_name' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
              <th className="hidden px-3 py-2.5 text-left sm:table-cell">
                <span className="text-xs font-medium text-zinc-400">Set</span>
              </th>
              <th className="px-3 py-2.5 text-left">
                <button onClick={() => toggleSort('status')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors">
                  Status <span className="text-zinc-600">{sortKey === 'status' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {isLoading && !q
              ? Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-3 py-3.5"><div className="h-4 w-4 rounded bg-zinc-800" /></td>
                    <td className="px-3 py-3.5"><div className="h-7 w-7 rounded-full bg-zinc-800" /></td>
                    <td className="px-3 py-3.5"><div className="h-3.5 w-32 rounded bg-zinc-800" /></td>
                    <td className="hidden px-3 py-3.5 sm:table-cell"><div className="h-3 w-20 rounded bg-zinc-800/60" /></td>
                    <td className="px-3 py-3.5"><div className="h-5 w-14 rounded-full bg-zinc-800/60" /></td>
                  </tr>
                ))
              : items.map((member) => {
                  const linkId = member.slug ?? member.id
                  const setInfo = member.set_id ? setMap[member.set_id] : null
                  const isDead = member.status === 'DEAD'
                  return (
                    <tr
                      key={member.id}
                      className={`group transition-colors hover:bg-zinc-900/40 ${selected.has(member.id) ? 'bg-violet-950/20' : ''} ${isDead ? 'opacity-60' : ''}`}
                    >
                      <td className="px-3 py-3.5">
                        <input
                          type="checkbox"
                          checked={selected.has(member.id)}
                          onChange={() => toggleSelect(member.id)}
                          className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                        />
                      </td>
                      {/* Avatar */}
                      <td className="px-3 py-3.5">
                        <div className={`flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-bold ${STATUS_AVATAR[member.status]}`}>
                          {initials(member.display_name)}
                        </div>
                      </td>
                      {/* Name */}
                      <td className="p-0">
                        <Link
                          to="/members/$id"
                          params={{ id: linkId }}
                          className={`block px-3 py-3.5 font-medium transition-colors group-hover:text-violet-400 ${isDead ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'}`}
                        >
                          {member.display_name}
                        </Link>
                      </td>
                      {/* Set */}
                      <td className="hidden px-3 py-3.5 sm:table-cell">
                        {setInfo ? (
                          <Link
                            to="/sets/$id"
                            params={{ id: setInfo.slug ?? member.set_id! }}
                            className="text-xs text-zinc-500 hover:text-violet-400 transition-colors"
                          >
                            {setInfo.name}
                          </Link>
                        ) : (
                          <span className="text-xs text-zinc-700">—</span>
                        )}
                      </td>
                      {/* Status */}
                      <td className="px-3 py-3.5">
                        <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
                          member.status === 'FREE' ? 'bg-emerald-900/50 text-emerald-300' :
                          member.status === 'LOCKED' ? 'bg-orange-900/50 text-orange-300' :
                          member.status === 'DEAD' ? 'bg-zinc-800 text-zinc-500' :
                          member.status === 'ESCAPEE' ? 'bg-amber-900/50 text-amber-300' :
                          member.status === 'ABSCONDER' ? 'bg-yellow-900/50 text-yellow-300' :
                          'bg-zinc-800/50 text-zinc-500'
                        }`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[member.status]}`} />
                          {member.status}
                        </span>
                      </td>
                    </tr>
                  )
                })}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <div className="flex flex-col items-center py-14 text-center">
                    <Users className="mb-3 h-8 w-8 text-zinc-700" />
                    <p className="text-sm text-zinc-500">
                      {q ? 'No members match your search' : hasFilters ? 'No members match these filters' : 'No members yet'}
                    </p>
                    {!q && !hasFilters && (
                      <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">
                        Add the first member →
                      </button>
                    )}
                    {hasFilters && (
                      <button onClick={() => { setStatusFilter(null); setSetFilter('') }} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">
                        Clear filters
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Load more */}
      {!q && data?.next_cursor && (
        <div className="mt-4 flex justify-center">
          <Button variant="outline" size="sm" onClick={() => setCursor(data.next_cursor ?? undefined)}>
            Load more
          </Button>
        </div>
      )}

      {/* Sticky bulk action bar */}
      {selected.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-2.5 shadow-2xl shadow-black/50">
          <span className="text-sm font-medium text-white">{selected.size} selected</span>
          <div className="h-4 w-px bg-zinc-700" />
          <span className="text-xs text-zinc-500">Set status:</span>
          <Select value={bulkStatus} onValueChange={(v) => setBulkStatus(v as MemberStatus)}>
            <SelectTrigger className="h-7 w-28 text-xs border-zinc-700 bg-zinc-800"><SelectValue /></SelectTrigger>
            <SelectContent>
              {ALL_STATUSES.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button size="sm" className="h-7 text-xs" onClick={applyBulkStatus} disabled={bulkUpdate.isPending}>
            {bulkUpdate.isPending ? 'Applying…' : 'Apply'}
          </Button>
          <button onClick={() => setSelected(new Set())} className="text-zinc-500 hover:text-white transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <MemberFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
