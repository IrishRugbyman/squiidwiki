import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { MemberIdentity } from '@/components/MemberIdentity'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  useMember, useMemberStats, useSets, useAlliances,
  useDeleteMember, useMemberIncidents,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { MemberFormSheet } from './_app.members.index'

export const Route = createFileRoute('/_app/members/$id')({
  component: MemberDetailPage,
})

function StatPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <span className="text-2xl font-bold text-white">{value}</span>
      <span className="mt-0.5 text-xs text-zinc-400">{label}</span>
    </div>
  )
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-4 py-2 border-b border-zinc-800/50 last:border-0">
      <span className="w-32 shrink-0 text-xs text-zinc-500">{label}</span>
      <span className="text-sm text-zinc-200">{children}</span>
    </div>
  )
}

function MemberDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: member, isLoading, isError, refetch } = useMember(id, universe?.id ?? null)
  const { data: stats } = useMemberStats(id, universe?.id ?? null)
  const { data: allSets } = useSets(universe?.id ?? null)
  const { data: allAlliances } = useAlliances(universe?.id ?? null)
  const { data: incidents } = useMemberIncidents(id, universe?.id ?? null)

  const deleteMember = useDeleteMember(universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const setName = (sid: string) => allSets?.items.find((s) => s.id === sid)?.name ?? sid
  const setSlug = (sid: string) => allSets?.items.find((s) => s.id === sid)?.slug ?? sid
  const allianceName = (aid: string) => allAlliances?.items.find((a) => a.id === aid)?.name ?? aid

  async function handleDelete() {
    if (!member) return
    try {
      await deleteMember.mutateAsync(member.id)
      navigate({ to: '/members' })
    } catch {
      setDeleting(false)
    }
  }

  if (isError) return <ErrorState title="Member not found" onRetry={() => refetch()} />

  return (
    <div>
      <Link to="/members" className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Members
      </Link>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      ) : member ? (
        <>
          <div className="mb-6 flex items-start justify-between">
            <div>
              <MemberIdentity member={member} showLegalName className="text-2xl font-bold" secondaryClassName="text-base mt-1" />
              <div className="mt-2 flex items-center gap-2">
                <MemberStatusBadge status={member.status} />
                {member.aliases && member.aliases.length > 0 && (
                  <span className="text-xs text-zinc-500">also: {member.aliases.join(', ')}</span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
              </Button>
              {user?.global_role === 'ADMIN' && (
                <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
                </Button>
              )}
            </div>
          </div>

          {stats && (
            <div className="mb-6 grid grid-cols-4 gap-2">
              <StatPill label="Shootings" value={stats.shootings} />
              <StatPill label="Assists" value={stats.assists} />
              <StatPill label="Kills" value={stats.kills} />
              <StatPill label="Survived" value={stats.times_shot_survived} />
            </div>
          )}

          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="biography">Bio</TabsTrigger>
              <TabsTrigger value="incidents">
                Incidents
                {incidents && incidents.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incidents.items.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-4">
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                <DetailRow label="Date of Birth"><FuzzyDate value={member.dob} fallback="Unknown" /></DetailRow>
                {member.status === 'DEAD' && (
                  <DetailRow label="Date of Death">
                    {member.date_of_death ? <FuzzyDate value={member.date_of_death} /> : <span className="text-zinc-600">Unknown</span>}
                  </DetailRow>
                )}
                {member.status === 'LOCKED' && (
                  <DetailRow label="Release Date">
                    {member.release_date ? <FuzzyDate value={member.release_date} /> : <span className="text-zinc-600">Unknown</span>}
                  </DetailRow>
                )}
                <DetailRow label="Set">
                  {member.set_id ? (
                    <Link to="/sets/$id" params={{ id: setSlug(member.set_id) }} className="text-violet-400 hover:underline">
                      {setName(member.set_id)}
                    </Link>
                  ) : <span className="text-zinc-600">—</span>}
                </DetailRow>
                <DetailRow label="Alliance">
                  {member.alliance_id ? (
                    <Link to="/alliances/$id" params={{ id: member.alliance_id }} className="text-violet-400 hover:underline">
                      {allianceName(member.alliance_id)}
                    </Link>
                  ) : <span className="text-zinc-600">—</span>}
                </DetailRow>
              </div>
            </TabsContent>

            <TabsContent value="biography" className="mt-4">
              {member.biography ? (
                <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{member.biography}</p>
              ) : (
                <p className="text-sm text-zinc-600">No biography recorded.</p>
              )}
            </TabsContent>

            <TabsContent value="incidents" className="mt-4">
              {!incidents || incidents.items.length === 0 ? (
                <p className="text-sm text-zinc-600">No incidents recorded.</p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Date</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Type</th>
                        <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Verified</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {incidents.items.map((inc) => (
                        <tr key={inc.id} className="hover:bg-zinc-900/50">
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-zinc-300 hover:text-violet-400">
                              {inc.date ? <FuzzyDate value={inc.date} /> : '—'}
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3" tabIndex={-1}>
                              <Badge variant="outline" className="text-xs">{inc.type}</Badge>
                            </Link>
                          </td>
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3" tabIndex={-1}>
                              {inc.verified
                                ? <Badge className="bg-emerald-900 text-emerald-300 border-transparent">Yes</Badge>
                                : <span className="text-zinc-500 text-xs">No</span>}
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
            <MemberFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={member}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Member"
            description={`Permanently delete "${member.display_name}"? This cannot be undone.`}
            confirmLabel="Delete"
            destructive
            pending={deleteMember.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
