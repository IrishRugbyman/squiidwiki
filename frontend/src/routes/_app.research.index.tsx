import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { NotebookText, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { EmptyState } from '@/components/EmptyState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useCreateResearchNote, useResearchNotes, useResearchSearch } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useDebounce } from '@/hooks/useDebounce'

export const Route = createFileRoute('/_app/research/')({
  component: ResearchIndexPage,
})

function formatDate(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: d.getFullYear() === now.getFullYear() ? undefined : 'numeric' })
}

function preview(content: string): string {
  return content.replace(/\s+/g, ' ').trim().slice(0, 160)
}

function ResearchIndexPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const debouncedQ = useDebounce(q, 250)

  const { data, isLoading } = useResearchNotes(universe?.id ?? null)
  const { data: searchResults, isLoading: searchLoading } = useResearchSearch(universe?.id ?? null, debouncedQ)
  const create = useCreateResearchNote()

  if (!universe) return <NoUniverse />

  const isSearching = debouncedQ.length >= 2
  const items = isSearching ? (searchResults ?? []) : (data?.items ?? [])
  const loading = isSearching ? searchLoading : isLoading

  async function handleNew() {
    if (!universe) return
    const note = await create.mutateAsync({
      universe_id: universe.id,
      title: 'Untitled note',
      content: '',
    })
    navigate({ to: '/research/$id', params: { id: note.id }, search: { edit: 1 } })
  }

  return (
    <div>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <NotebookText className="h-5 w-5 text-violet-500" />
          <h1 className="text-xl font-bold text-white">Research</h1>
          <span className="text-xs text-zinc-600">scratchpad for {universe.name}</span>
        </div>
        <Button size="sm" onClick={handleNew} disabled={create.isPending}>
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          {create.isPending ? 'Creating…' : 'New note'}
        </Button>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative max-w-sm flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input
            className="pl-8 h-8 text-sm"
            placeholder="Search notes…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={NotebookText}
          title={q ? `No notes match "${q}"` : 'No research notes yet'}
          description={q ? undefined : 'Capture text, paste links from socials, jot down anything you find.'}
          action={
            !q ? (
              <Button size="sm" onClick={handleNew} disabled={create.isPending}>
                <Plus className="mr-1.5 h-3.5 w-3.5" />Start your first note
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid gap-2">
          {items.map((n) => (
            <Link
              key={n.id}
              to="/research/$id"
              params={{ id: n.id }}
              search={{ edit: undefined }}
              className="group block rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 transition-colors hover:border-zinc-700 hover:bg-zinc-900/60"
            >
              <div className="flex items-start justify-between gap-4">
                <h3 className="font-medium text-white group-hover:text-violet-400 transition-colors truncate">
                  {n.title || 'Untitled'}
                </h3>
                <span className="shrink-0 text-[11px] text-zinc-600 tabular-nums">
                  {formatDate(n.updated_at)}
                </span>
              </div>
              {n.content && (
                <p className="mt-1 text-sm text-zinc-500 line-clamp-2">
                  {preview(n.content)}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
