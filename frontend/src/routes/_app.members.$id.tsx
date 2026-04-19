import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { MemberIdentity } from '@/components/MemberIdentity'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useMember, useMemberStats } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'

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
  const { data: member, isLoading, isError, refetch } = useMember(id, universe?.id ?? null)
  const { data: stats } = useMemberStats(id, universe?.id ?? null)

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
          <div className="mb-6">
            <MemberIdentity member={member} showLegalName className="text-2xl font-bold" secondaryClassName="text-base mt-1" />
            <div className="mt-2 flex items-center gap-2">
              <MemberStatusBadge status={member.status} />
              {member.aliases && member.aliases.length > 0 && (
                <span className="text-xs text-zinc-500">also: {member.aliases.join(', ')}</span>
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
            </TabsList>

            <TabsContent value="overview">
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                <DetailRow label="Date of Birth"><FuzzyDate value={member.dob} fallback="Unknown" /></DetailRow>
                <DetailRow label="Date of Death">
                  {member.date_of_death ? <FuzzyDate value={member.date_of_death} /> : <span className="text-zinc-600">—</span>}
                </DetailRow>
                {member.release_date && (
                  <DetailRow label="Release Date"><FuzzyDate value={member.release_date} /></DetailRow>
                )}
                <DetailRow label="Set">
                  {member.set_id ? (
                    <Link to="/sets/$id" params={{ id: member.set_id }} className="text-violet-400 hover:underline">
                      {member.set_id}
                    </Link>
                  ) : <span className="text-zinc-600">—</span>}
                </DetailRow>
              </div>
            </TabsContent>

            <TabsContent value="biography">
              {member.biography ? (
                <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{member.biography}</p>
              ) : (
                <p className="text-sm text-zinc-600">No biography recorded.</p>
              )}
            </TabsContent>
          </Tabs>
        </>
      ) : null}
    </div>
  )
}
