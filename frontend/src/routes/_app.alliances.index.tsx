import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Network, Plus, Search } from 'lucide-react'
import { useState, useMemo } from 'react'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { AllianceStatusToggle } from '@/components/StatusToggle'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { EmptyState } from '@/components/EmptyState'
import { TableRowSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useAlliances, useCreateAlliance, useUpdateAlliance, useUpdateAllianceStatus } from '@/lib/queries'
import type { AllianceRead, AllianceStatus } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'

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
  const [aliases, setAliases] = useState(initial?.aliases?.join(', ') ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [status, setStatus] = useState<AllianceStatus>(initial?.status ?? 'ACTIVE')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const aliasList = aliases.split(',').map((s) => s.trim()).filter(Boolean)
    const body = {
      universe_id: universeId,
      name,
      aliases: aliasList.length > 0 ? aliasList : null,
      description: description || null,
      status,
    }
    try {
      if (isEdit) {
        const updated = await update.mutateAsync(body)
        onSaved?.(updated)
        toast.success(`Updated "${name}"`)
      } else {
        await create.mutateAsync(body)
        setName(''); setAliases(''); setDescription(''); setStatus('ACTIVE')
        toast.success(`Created "${name}"`)
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
            <Label htmlFor="a-aliases">Aliases <span className="text-zinc-600">(comma-separated)</span></Label>
            <Input id="a-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. EastSide, ESC" />
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

  const statusUpdate = useUpdateAllianceStatus(universe?.id ?? '')
  const { data, isLoading } = useAlliances(universe?.id ?? null, offset)

  const rawItems = (data?.items ?? []).filter((a) => !q || a.name.toLowerCase().includes(q.toLowerCase()))

  const items = useMemo(() => {
    if (!sortKey) return rawItems
    return [...rawItems].sort((a, b) => {
      const av = String((a as unknown as Record<string, unknown>)[sortKey] ?? '')
      const bv = String((b as unknown as Record<string, unknown>)[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [rawItems, sortKey, sortDir])

  if (!universe) return <NoUniverse />

  const total = data?.total ?? 0

  function toggleSort(key: 'name' | 'status') {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const activeCount = (data?.items ?? []).filter((a) => a.status === 'ACTIVE').length
  const dormantCount = (data?.items ?? []).filter((a) => a.status === 'DORMANT').length
  const extinctCount = (data?.items ?? []).filter((a) => a.status === 'EXTINCT').length
  const description = isLoading
    ? undefined
    : total === 0
    ? 'No alliances yet'
    : [
        activeCount > 0 && `${activeCount} active`,
        dormantCount > 0 && `${dormantCount} dormant`,
        extinctCount > 0 && `${extinctCount} extinct`,
      ].filter(Boolean).join(' · ') || `${total} total`

  return (
    <div>
      <PageHeader
        title="Alliances"
        description={description}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Alliance</Button>}
      />

      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8" placeholder="Search alliances…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <Button variant="outline" size="sm" onClick={() => {
          const date = new Date().toISOString().slice(0, 10)
          downloadCsv(`/alliances/?universe_id=${universe.id}&format=csv`, `alliances-${universe.slug}-${date}.csv`)
        }}>
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th
                className="px-4 py-2.5 text-left"
                scope="col"
                aria-sort={sortKey === 'name' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                <button onClick={() => toggleSort('name')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white">
                  Name <span className="text-zinc-600" aria-hidden>{sortKey === 'name' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
              <th
                className="px-4 py-2.5 text-left"
                scope="col"
                aria-sort={sortKey === 'status' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                <button onClick={() => toggleSort('status')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white">
                  Status <span className="text-zinc-600" aria-hidden>{sortKey === 'status' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={2} height={52} />)
              : items.map((alliance) => (
                    <tr key={alliance.id} className="hover:bg-zinc-900/50 transition-colors">
                      <td className="p-0">
                        <Link to="/alliances/$id" params={{ id: alliance.slug ?? alliance.id }} className="block px-4 py-3 font-medium text-white hover:text-violet-400 transition-colors">
                          {alliance.name}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <AllianceStatusToggle
                          value={alliance.status}
                          pending={statusUpdate.isPending && statusUpdate.variables?.id === alliance.id}
                          onChange={(s) => statusUpdate.mutate({ id: alliance.id, status: s })}
                        />
                      </td>
                    </tr>
                  ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={2}>
                  <EmptyState
                    icon={Network}
                    title={q ? `No alliances match "${q}"` : 'No alliances yet'}
                    description={!q ? 'Create an alliance to organise sets.' : undefined}
                    action={
                      !q ? (
                        <Button size="sm" onClick={() => setCreating(true)}>
                          <Plus className="mr-1.5 h-4 w-4" /> Create the first alliance
                        </Button>
                      ) : undefined
                    }
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!q && total > PAGE && (
        <nav className="mt-4 flex items-center justify-between text-sm text-zinc-400" aria-label="Pagination">
          <span>Showing {offset + 1}–{Math.min(offset + PAGE, total)} of {total}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" aria-disabled={offset === 0} disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Prev</Button>
            <Button variant="outline" size="sm" aria-disabled={offset + PAGE >= total} disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>Next</Button>
          </div>
        </nav>
      )}

      <AllianceFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
