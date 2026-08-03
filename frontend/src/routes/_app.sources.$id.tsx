import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Archive, ExternalLink, Link2, Pencil, Trash2 } from 'lucide-react'
import { lazy, Suspense, useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { timeAgo } from '@/lib/utils'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { RELIABILITY_DESCRIPTION } from '@/lib/statusColors'
import { useSource, useSourceIncidents, useSourceMembers, useDeleteSource } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { SourceFormSheet } from './_app.sources.index'
import { Skeleton } from '@/components/ui/skeleton'

const PhotoGallery = lazy(() =>
  import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })),
)
import { AttachIncidentsToSourceDialog } from '@/components/AttachIncidentsToSourceDialog'
import { AttachMembersToSourceDialog } from '@/components/AttachMembersToSourceDialog'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'

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

  useRecordRecent(source ? { type: 'source', id: source.id, slug: null, label: source.title } : null)

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [attachingIncident, setAttachingIncident] = useState(false)
  const [attachingMember, setAttachingMember] = useState(false)

  useEditShortcut(() => source && setEditing(true))

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
    <TooltipProvider delayDuration={200}>
    <div>
      <Breadcrumbs
        items={[
          { label: 'Sources', to: '/sources' },
          { label: source?.title ?? 'Source' },
        ]}
      />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : source ? (
        <>
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-2xl font-bold text-white">{source.title}</h1>
                <CopyButton value={window.location.href} label="Copy link to this source" className="opacity-60 hover:opacity-100" />
              </div>
              {source.publication && <p className="text-sm text-zinc-400">{source.publication}</p>}
              <div className="mt-2 flex items-center gap-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="inline-block"><ReliabilityBadge reliability={source.reliability} /></span>
                  </TooltipTrigger>
                  <TooltipContent side="right">{RELIABILITY_DESCRIPTION[source.reliability]}</TooltipContent>
                </Tooltip>
                {source.published_at && (
                  <span className="text-xs text-zinc-400">
                    Published <FuzzyDate value={source.published_at} />
                  </span>
                )}
                <span className="text-[11px] text-zinc-400">Updated {timeAgo(source.updated_at)}</span>
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
                <Button variant="secondary" size="sm" className="gap-1.5">
                  <ExternalLink className="h-3.5 w-3.5" /> Open
                </Button>
              </a>
              {source.archive_url && (
                <a href={source.archive_url} target="_blank" rel="noopener noreferrer">
                  <Button variant="secondary" size="sm" className="gap-1.5">
                    <Archive className="h-3.5 w-3.5" /> Archive
                  </Button>
                </a>
              )}
            </div>
          </div>

          {source.notes && (
            <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">Notes</h3>
              <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{source.notes}</p>
            </div>
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
              <TabsTrigger value="photos">Photos</TabsTrigger>
            </TabsList>

            <TabsContent value="incidents" className="mt-4">
              <div className="mb-3 flex justify-end">
                <Button size="sm" variant="outline" onClick={() => setAttachingIncident(true)}>
                  <Link2 className="mr-1.5 h-3.5 w-3.5" />Attach to incident
                </Button>
              </div>
              {!incidents || incidents.items.length === 0 ? (
                <p className="text-sm text-zinc-400">No incidents cite this source.</p>
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
                          <td className="px-4 py-3 text-zinc-400">
                            <FuzzyDate value={inc.date} fallback="Unknown date" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="members" className="mt-4">
              <div className="mb-3 flex justify-end">
                <Button size="sm" variant="outline" onClick={() => setAttachingMember(true)}>
                  <Link2 className="mr-1.5 h-3.5 w-3.5" />Attach to member
                </Button>
              </div>
              {!members || members.items.length === 0 ? (
                <p className="text-sm text-zinc-400">No members cite this source.</p>
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
                          <td className="px-4 py-3">
                            <MemberStatusBadge status={m.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="photos" className="mt-4">
              {universe && (
                <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                  <PhotoGallery entityType="source" entityId={source.id} universeId={universe.id} />
                </Suspense>
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

          {universe && (
            <AttachIncidentsToSourceDialog
              sourceId={source.id}
              universeId={universe.id}
              attachedIncidentIds={incidents?.items.map((i) => i.id) ?? []}
              open={attachingIncident}
              onClose={() => setAttachingIncident(false)}
            />
          )}

          {universe && (
            <AttachMembersToSourceDialog
              sourceId={source.id}
              universeId={universe.id}
              attachedMemberIds={members?.items.map((m) => m.id) ?? []}
              open={attachingMember}
              onClose={() => setAttachingMember(false)}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Source"
            description={`Permanently delete "${source.title}"? This cannot be undone.`}
            impact={(() => {
              const incCount = incidents?.items.length ?? 0
              const memCount = members?.items.length ?? 0
              if (!incCount && !memCount) return null
              const parts: string[] = []
              if (incCount) parts.push(`${incCount} incident${incCount === 1 ? '' : 's'}`)
              if (memCount) parts.push(`${memCount} member${memCount === 1 ? '' : 's'}`)
              return <span>{parts.join(' and ')} will lose this citation.</span>
            })()}
            confirmLabel="Delete"
            destructive
            pending={deleteSource.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
    </TooltipProvider>
  )
}
