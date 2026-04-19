import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Plus, Search, Shield } from 'lucide-react'
import { useMemo, useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { SetStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { useCreateSet, useSets, useSetSearch, useUpdateSet } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import type { SetRead, SetStatus } from '@/lib/types'

export const Route = createFileRoute('/_app/sets/')({
  component: SetsPage,
})

interface SetFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: SetRead
}

export function SetFormSheet({ universeId, open, onClose, initial }: SetFormProps) {
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
        await update.mutateAsync({ universe_id: universeId, name, alias: alias || null, bio: bio || null, status })
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

function SetsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const PAGE = 20

  const { data, isLoading } = useSets(universe?.id ?? null, offset)
  const { data: searchResults } = useSetSearch(universe?.id ?? null, q)

  if (!universe) return <NoUniverse />

  const rawItems = q.length >= 2 ? (searchResults ?? []) : (data?.items ?? [])
  const total = data?.total ?? 0

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const items = useMemo(() => {
    if (!sortKey) return rawItems
    return [...rawItems].sort((a, b) => {
      const av = String((a as any)[sortKey] ?? '')
      const bv = String((b as any)[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [rawItems, sortKey, sortDir])

  return (
    <div>
      <PageHeader
        title="Sets"
        description={`${total} total`}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Set</Button>}
      />

      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8" placeholder="Search sets…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <Button
          variant="outline" size="sm"
          onClick={() => downloadCsv(`/sets/?universe_id=${universe.id}&format=csv`, 'sets.csv')}
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <SortHeader label="Name" col="name" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
              <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Alias</th>
              <SortHeader label="Status" col="status" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading && !q
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={3}><Skeleton className="h-4 w-48" /></td>
                  </tr>
                ))
              : items.map((set) => {
                  const linkId = set.slug ?? set.id
                  return (
                    <tr key={set.id} className="hover:bg-zinc-900/50 transition-colors">
                      <td className="p-0">
                        <Link to="/sets/$id" params={{ id: linkId }} className="block px-4 py-3 font-medium text-white hover:text-violet-400 transition-colors">
                          {set.name}
                        </Link>
                      </td>
                      <td className="p-0">
                        <Link to="/sets/$id" params={{ id: linkId }} className="block px-4 py-3 text-zinc-400" tabIndex={-1}>
                          {(set as { alias?: string | null }).alias ?? '—'}
                        </Link>
                      </td>
                      <td className="p-0">
                        <Link to="/sets/$id" params={{ id: linkId }} className="block px-4 py-3" tabIndex={-1}>
                          <SetStatusBadge status={set.status} />
                        </Link>
                      </td>
                    </tr>
                  )
                })}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={3}>
                  <div className="flex flex-col items-center py-12 text-center">
                    <Shield className="mb-3 h-8 w-8 text-zinc-700" />
                    <p className="text-sm text-zinc-500">No sets yet</p>
                    <button
                      onClick={() => setCreating(true)}
                      className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors"
                    >
                      Create the first set →
                    </button>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

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
    </div>
  )
}
