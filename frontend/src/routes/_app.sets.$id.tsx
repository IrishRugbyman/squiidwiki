import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowLeft, Swords, Users } from 'lucide-react'
import { useSet, useSetStats } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { SetStatusBadge } from '@/components/StatusBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { ErrorState } from '@/components/ErrorState'

export const Route = createFileRoute('/_app/sets/$id')({
  component: SetDetailPage,
})

function StatPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <span className="text-2xl font-bold text-white">{value}</span>
      <span className="mt-0.5 text-xs text-zinc-400">{label}</span>
    </div>
  )
}

function SetDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data: set, isLoading, isError, refetch } = useSet(id, universe?.id ?? null)
  const { data: stats } = useSetStats(id, universe?.id ?? null)

  if (isError) return <ErrorState title="Set not found" onRetry={() => refetch()} />

  return (
    <div>
      <Link to="/sets" className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Sets
      </Link>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-24" />
        </div>
      ) : set ? (
        <>
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">{set.name}</h1>
              {set.alias && <p className="text-sm text-zinc-400">a/k/a {set.alias}</p>}
              <div className="mt-2"><SetStatusBadge status={set.status} /></div>
            </div>
          </div>

          {stats && (
            <div className="mb-6 grid grid-cols-5 gap-2">
              <StatPill label="Members" value={stats.member_count} />
              <StatPill label="Dead" value={stats.dead_members} />
              <StatPill label="Shootings" value={stats.total_shootings} />
              <StatPill label="Assists" value={stats.total_assists} />
              <StatPill label="Kills" value={stats.total_kills} />
            </div>
          )}

          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="relationships">
                Relationships
                {set.friend_ids.length + set.enemy_ids.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">
                    {set.friend_ids.length + set.enemy_ids.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              {set.bio ? (
                <p className="text-sm text-zinc-300 leading-relaxed">{set.bio}</p>
              ) : (
                <p className="text-sm text-zinc-600">No biography recorded.</p>
              )}
            </TabsContent>

            <TabsContent value="relationships">
              {set.friend_ids.length === 0 && set.enemy_ids.length === 0 ? (
                <p className="text-sm text-zinc-600">No relationships recorded.</p>
              ) : (
                <div className="space-y-4">
                  {set.friend_ids.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                        <Users className="h-3.5 w-3.5" /> Allies ({set.friend_ids.length})
                      </div>
                      <div className="space-y-1">
                        {set.friend_ids.map((sid) => (
                          <Link key={sid} to="/sets/$id" params={{ id: sid }} className="block text-sm text-zinc-300 hover:text-violet-400">
                            {sid}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                  {set.enemy_ids.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-red-400">
                        <Swords className="h-3.5 w-3.5" /> Enemies ({set.enemy_ids.length})
                      </div>
                      <div className="space-y-1">
                        {set.enemy_ids.map((sid) => (
                          <Link key={sid} to="/sets/$id" params={{ id: sid }} className="block text-sm text-zinc-300 hover:text-violet-400">
                            {sid}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </>
      ) : null}
    </div>
  )
}
