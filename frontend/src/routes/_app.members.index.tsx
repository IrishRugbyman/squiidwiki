import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Plus, Search, Users } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { MemberStatusBadge } from '@/components/StatusBadge'
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
import type { MemberRead, MemberStatus } from '@/lib/types'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { useMemo } from 'react'

export const Route = createFileRoute('/_app/members/')({
  component: MembersPage,
})

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
            <input
              id="m-nku" type="checkbox"
              checked={nicknameUnknown}
              onChange={(e) => setNicknameUnknown(e.target.checked)}
              className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
            />
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
                {(['FREE', 'LOCKED', 'DEAD', 'UNKNOWN', 'ESCAPEE', 'ABSCONDER'] as MemberStatus[]).map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
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
                {(sets?.items ?? []).map((s) => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Alliance</Label>
            <Select value={allianceId || 'none'} onValueChange={(v) => setAllianceId(v === 'none' ? '' : v)}>
              <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">— None —</SelectItem>
                {(alliances?.items ?? []).map((a) => (
                  <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                ))}
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

function MembersPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkStatus, setBulkStatus] = useState<MemberStatus>('FREE')
  const [sortKey, setSortKey] = useState<'display_name' | 'status' | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const bulkUpdate = useBulkMemberStatus(universe?.id ?? '')

  const { data, isLoading } = useMembers(universe?.id ?? null, cursor)
  const { data: searchResults } = useMemberSearch(universe?.id ?? null, q)

  if (!universe) return <NoUniverse />

  const rawItems = q.length >= 2 ? (searchResults ?? []) : (data?.items ?? [])
  const total = data?.total

  function toggleSort(key: 'display_name' | 'status') {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const items = useMemo(() => {
    if (!sortKey) return rawItems
    return [...rawItems].sort((a, b) => {
      const av = String((a as any)[sortKey] ?? '')
      const bv = String((b as any)[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [rawItems, sortKey, sortDir])

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === items.length) setSelected(new Set())
    else setSelected(new Set(items.map((m) => m.id)))
  }

  async function applyBulkStatus() {
    if (selected.size === 0) return
    await bulkUpdate.mutateAsync({ member_ids: Array.from(selected), status: bulkStatus })
    setSelected(new Set())
  }

  return (
    <div>
      <PageHeader
        title="Members"
        description={total != null ? `${total} total` : undefined}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Member</Button>}
      />

      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8" placeholder="Search members…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <Button variant="outline" size="sm" onClick={() => downloadCsv(`/members/?universe_id=${universe.id}&format=csv`, 'members.csv')}>
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
        {selected.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-400">{selected.size} selected</span>
            <Select value={bulkStatus} onValueChange={(v) => setBulkStatus(v as MemberStatus)}>
              <SelectTrigger className="w-32 h-8 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                {(['FREE', 'LOCKED', 'DEAD', 'UNKNOWN', 'ESCAPEE', 'ABSCONDER'] as MemberStatus[]).map((s) => (
                  <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button size="sm" onClick={applyBulkStatus} disabled={bulkUpdate.isPending} className="h-8 text-xs">
              {bulkUpdate.isPending ? 'Applying…' : 'Apply'}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())} className="h-8 text-xs text-zinc-500">
              Clear
            </Button>
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="w-10 px-3 py-2.5">
                <input
                  type="checkbox"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={toggleAll}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              <th className="px-4 py-2.5 text-left">
                <button onClick={() => toggleSort('display_name')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors">
                  Name <span className="text-zinc-600">{sortKey === 'display_name' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
              <th className="px-4 py-2.5 text-left">
                <button onClick={() => toggleSort('status')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors">
                  Status <span className="text-zinc-600">{sortKey === 'status' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading && !q
              ? Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-3 py-3"><div className="h-4 w-4 rounded bg-zinc-800" /></td>
                    <td className="px-4 py-3" colSpan={2}><Skeleton className="h-4 w-48" /></td>
                  </tr>
                ))
              : items.map((member) => (
                  <tr key={member.id} className="hover:bg-zinc-900/50 transition-colors">
                    <td className="px-3 py-3">
                      <input
                        type="checkbox"
                        checked={selected.has(member.id)}
                        onChange={() => toggleSelect(member.id)}
                        className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                      />
                    </td>
                    <td className="p-0">
                      <Link to="/members/$id" params={{ id: member.slug ?? member.id }} className="block px-4 py-3 font-medium text-white hover:text-violet-400 transition-colors">
                        {member.display_name}
                      </Link>
                    </td>
                    <td className="p-0">
                      <Link to="/members/$id" params={{ id: member.slug ?? member.id }} className="block px-4 py-3" tabIndex={-1}>
                        <MemberStatusBadge status={member.status} />
                      </Link>
                    </td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={3}>
                  <div className="flex flex-col items-center py-12 text-center">
                    <Users className="mb-3 h-8 w-8 text-zinc-700" />
                    <p className="text-sm text-zinc-500">{q ? 'No members match your search' : 'No members yet'}</p>
                    {!q && (
                      <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">
                        Add the first member →
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!q && data?.next_cursor && (
        <div className="mt-4 flex justify-end">
          <Button variant="outline" size="sm" onClick={() => setCursor(data.next_cursor ?? undefined)}>Load more</Button>
        </div>
      )}

      <MemberFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
