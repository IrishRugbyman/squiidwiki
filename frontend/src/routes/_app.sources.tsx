import { createFileRoute } from '@tanstack/react-router'
import { ExternalLink, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useCreateSource, useSources } from '@/lib/queries'
import type { SourceReliability } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/sources')({
  component: SourcesPage,
})

function CreateSourceSheet({ universeId, open, onClose }: { universeId: string; open: boolean; onClose: () => void }) {
  const create = useCreateSource()
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [publication, setPublication] = useState('')
  const [reliability, setReliability] = useState<SourceReliability>('UNVERIFIED')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      await create.mutateAsync({
        universe_id: universeId,
        url,
        title,
        publication: publication || null,
        reliability,
        notes: notes || null,
      })
      setUrl(''); setTitle(''); setPublication(''); setReliability('UNVERIFIED'); setNotes('')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create source')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title="Add Source" description="Add a citation or reference">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="s-url">URL *</Label>
            <Input id="s-url" type="url" required value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="s-title">Title *</Label>
            <Input id="s-title" required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Article or document title" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="s-pub">Publication</Label>
            <Input id="s-pub" value={publication} onChange={(e) => setPublication(e.target.value)} placeholder="e.g. Detroit Free Press" />
          </div>
          <div className="space-y-1.5">
            <Label>Reliability</Label>
            <Select value={reliability} onValueChange={(v) => setReliability(v as SourceReliability)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
                <SelectItem value="UNVERIFIED">Unverified</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="s-notes">Notes</Label>
            <Textarea id="s-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Caveats or context…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={create.isPending} className="flex-1">
              {create.isPending ? 'Saving…' : 'Add Source'}
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

function SourcesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const PAGE = 20

  const { data, isLoading } = useSources(universe?.id ?? null, offset)

  if (!universe) return <NoUniverse />

  const items = (data?.items ?? []).filter((s) => !q || s.title.toLowerCase().includes(q.toLowerCase()))
  const total = data?.total ?? 0

  return (
    <div>
      <PageHeader
        title="Sources"
        description={`${total} total`}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Source</Button>}
      />

      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8" placeholder="Filter sources…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Title</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Reliability</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400 w-10"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={3}><Skeleton className="h-4 w-64" /></td>
                  </tr>
                ))
              : items.map((source) => (
                  <tr key={source.id} className="hover:bg-zinc-900/50 transition-colors">
                    <td className="px-4 py-3 font-medium text-white">{source.title}</td>
                    <td className="px-4 py-3"><ReliabilityBadge reliability={source.reliability} /></td>
                    <td className="px-4 py-3">
                      <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-violet-400 transition-colors">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-12 text-center text-sm text-zinc-500">No sources found</td>
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

      <CreateSourceSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}

