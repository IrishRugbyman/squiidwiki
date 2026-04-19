import { createFileRoute, Link } from '@tanstack/react-router'
import { Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { SetStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useCreateSet, useSets, useSetSearch } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import type { SetStatus } from '@/lib/types'

export const Route = createFileRoute('/_app/sets')({
  component: SetsPage,
})

function CreateSetSheet({ universeId, open, onClose }: { universeId: string; open: boolean; onClose: () => void }) {
  const create = useCreateSet()
  const [name, setName] = useState('')
  const [alias, setAlias] = useState('')
  const [bio, setBio] = useState('')
  const [status, setStatus] = useState<SetStatus>('ACTIVE')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      await create.mutateAsync({ universe_id: universeId, name, alias: alias || null, bio: bio || null, status })
      setName(''); setAlias(''); setBio(''); setStatus('ACTIVE')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create set')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title="Add Set" description="Create a new gang set in this universe">
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
            <Button type="submit" disabled={create.isPending} className="flex-1">
              {create.isPending ? 'Saving…' : 'Create Set'}
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

function SetsPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const PAGE = 20

  const { data, isLoading } = useSets(universe?.id ?? null, offset)
  const { data: searchResults } = useSetSearch(universe?.id ?? null, q)

  if (!universe) return <NoUniverse />

  const items = q.length >= 2 ? (searchResults ?? []) : (data?.items ?? [])
  const total = data?.total ?? 0

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
          <Input
            className="pl-8"
            placeholder="Search sets…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Name</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Alias</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading && !q
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={3}><Skeleton className="h-4 w-48" /></td>
                  </tr>
                ))
              : items.map((set) => (
                  <tr key={set.id} className="hover:bg-zinc-900/50 transition-colors">
                    <td className="px-4 py-3">
                      <Link to="/sets/$id" params={{ id: set.id }} className="font-medium text-white hover:text-violet-400 transition-colors">
                        {set.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-zinc-400">—</td>
                    <td className="px-4 py-3"><SetStatusBadge status={set.status} /></td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-12 text-center text-sm text-zinc-500">No sets found</td>
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

      <CreateSetSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
