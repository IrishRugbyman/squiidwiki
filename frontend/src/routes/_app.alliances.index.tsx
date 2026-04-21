import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Network, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { AllianceStatusBadge } from '@/components/StatusBadge'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useAlliances, useCreateAlliance, useUpdateAlliance } from '@/lib/queries'
import type { AllianceRead, AllianceStatus } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import { useMemo } from 'react'

export const Route = createFileRoute('/_app/alliances/')({
  component: AlliancesPage,
})

interface AllianceFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: AllianceRead
  onSaved?: (data: AllianceRead) => void
}

export function AllianceFormSheet({ universeId, open, onClose, initial, onSaved }: AllianceFormProps) {
  const create = useCreateAlliance()
  const update = useUpdateAlliance(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const [name, setName] = useState(initial?.name ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [status, setStatus] = useState<AllianceStatus>(initial?.status ?? 'ACTIVE')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const body = { universe_id: universeId, name, description: description || null, status }
    try {
      if (isEdit) {
        const updated = await update.mutateAsync(body)
        onSaved?.(updated)
      } else {
        await create.mutateAsync(body)
        setName(''); setDescription(''); setStatus('ACTIVE')
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} alliance`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Alliance' : 'Add Alliance'}
        description={isEdit ? 'Update this alliance' : 'Create a new gang alliance'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="a-name">Name *</Label>
            <Input id="a-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Alliance name" />
          </div>
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as AllianceStatus)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="DORMANT">Dormant</SelectItem>
                <SelectItem value="EXTINCT">Extinct</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="a-desc">Description</Label>
            <Textarea id="a-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Overview…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Alliance'}
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

function AlliancesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const [sortKey, setSortKey] = useState<'name' | 'status' | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const PAGE = 20

  const { data, isLoading } = useAlliances(universe?.id ?? null, offset)

  if (!universe) return <NoUniverse />

  const rawItems = (data?.items ?? []).filter((a) => !q || a.name.toLowerCase().includes(q.toLowerCase()))
  const total = data?.total ?? 0

  function toggleSort(key: 'name' | 'status') {
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

  return (
    <div>
      <PageHeader
        title="Alliances"
        description={`${total} total`}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Alliance</Button>}
      />

      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8" placeholder="Search alliances…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <Button variant="outline" size="sm" onClick={() => downloadCsv(`/alliances/?universe_id=${universe.id}&format=csv`, 'alliances.csv')}>
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left">
                <button onClick={() => toggleSort('name')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors">
                  Name <span className="text-zinc-600">{sortKey === 'name' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
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
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={2}><Skeleton className="h-4 w-48" /></td>
                  </tr>
                ))
              : items.map((alliance) => (
                    <tr key={alliance.id} className="hover:bg-zinc-900/50 transition-colors">
                      <td className="p-0">
                        <Link to="/alliances/$id" params={{ id: alliance.slug ?? alliance.id }} className="block px-4 py-3 font-medium text-white hover:text-violet-400 transition-colors">
                          {alliance.name}
                        </Link>
                      </td>
                      <td className="p-0">
                        <Link to="/alliances/$id" params={{ id: alliance.slug ?? alliance.id }} className="block px-4 py-3" tabIndex={-1}>
                          <AllianceStatusBadge status={alliance.status} />
                        </Link>
                      </td>
                    </tr>
                  ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={2}>
                  <div className="flex flex-col items-center py-12 text-center">
                    <Network className="mb-3 h-8 w-8 text-zinc-700" />
                    <p className="text-sm text-zinc-500">{q ? 'No alliances match your search' : 'No alliances yet'}</p>
                    {!q && (
                      <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">
                        Create the first alliance →
                      </button>
                    )}
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

      <AllianceFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
