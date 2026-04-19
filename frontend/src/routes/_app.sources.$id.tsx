import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, ExternalLink, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useSource, useSourceIncidents, useSourceMembers, useDeleteSource } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { SourceFormSheet } from './_app.sources.index'

export const Route = createFileRoute('/_app/sources/$id')({
  component: SourceDetailPage,
})

function SourceDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const { data: source, isLoading, isError, refetch } = useSource(id, universe?.id ?? null)
  const { data: incidents } = useSourceIncidents(id, universe?.id ?? null)
  const { data: members } = useSourceMembers(id, universe?.id ?? null)
  const deleteSource = useDeleteSource(universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    if (!source) return
    try {
      await deleteSource.mutateAsync(source.id)
      navigate({ to: '/sources' })
    } catch {
      setDeleting(false)
    }
  }

  if (isError) return <ErrorState title="Source not found" onRetry={() => refetch()} />

  return (
    <div>
      <Link to="/sources" className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Sources
      </Link>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-24" />
        </div>
      ) : source ? (
        <>
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white">{source.title}</h1>
              {source.publication && <p className="text-sm text-zinc-400">{source.publication}</p>}
              <div className="mt-2 flex items-center gap-2">
                <ReliabilityBadge reliability={source.reliability} />
                {source.published_at && (
                  <span className="text-xs text-zinc-500">
                    Published <FuzzyDate value={source.published_at} />
                  </span>
                )}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
              </Button>
              {user?.global_role === 'ADMIN' && (
                <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
                </Button>
              )}
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                <Button variant="outline" size="sm" className="gap-1.5">
                  <ExternalLink className="h-3.5 w-3.5" /> Open
                </Button>
              </a>
            </div>
          </div>

          {source.notes && (
            <div className="mb-4 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{source.notes}</p>
            </div>
          )}

          {source.archive_url && (
            <a href={source.archive_url} target="_blank" rel="noopener noreferrer"
              className="mb-6 inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
              <ExternalLink className="h-3 w-3" /> Archived version
            </a>
          )}

          <Tabs defaultValue="incidents" className="mt-4">
            <TabsList>
              <TabsTrigger value="incidents">
                Incidents
                {incidents && incidents.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incidents.items.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="members">
                Members
                {members && members.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{members.items.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="incidents" className="mt-4">
              {!incidents || incidents.items.length === 0 ? (
                <p className="text-sm text-zinc-600">No incidents cite this source.</p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Type</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {incidents.items.map((inc) => (
                        <tr key={inc.id} className="hover:bg-zinc-900/50">
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-white hover:text-violet-400">
                              {inc.type}
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-zinc-400" tabIndex={-1}>
                              <FuzzyDate value={inc.date} fallback="Unknown date" />
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="members" className="mt-4">
              {!members || members.items.length === 0 ? (
                <p className="text-sm text-zinc-600">No members cite this source.</p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Name</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {members.items.map((m) => (
                        <tr key={m.id} className="hover:bg-zinc-900/50">
                          <td className="p-0">
                            <Link to="/members/$id" params={{ id: m.slug ?? m.id }} className="block px-4 py-3 text-white hover:text-violet-400">
                              {m.display_name}
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/members/$id" params={{ id: m.slug ?? m.id }} className="block px-4 py-3" tabIndex={-1}>
                              <MemberStatusBadge status={m.status} />
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>
          </Tabs>

          {universe && (
            <SourceFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={source}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Source"
            description={`Permanently delete "${source.title}"? This cannot be undone.`}
            confirmLabel="Delete"
            destructive
            pending={deleteSource.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
