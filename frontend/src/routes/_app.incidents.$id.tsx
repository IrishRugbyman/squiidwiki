import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { ErrorState } from '@/components/ErrorState'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { useIncident } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/incidents/$id')({
  component: IncidentDetailPage,
})

const ROLE_STYLE: Record<string, string> = {
  SHOOTER: 'bg-red-900 text-red-300 border-transparent',
  ASSISTED: 'bg-orange-900 text-orange-300 border-transparent',
  VICTIM: 'bg-zinc-800 text-zinc-300 border-transparent',
  BYSTANDER: 'bg-zinc-900 text-zinc-500 border-zinc-700',
}

const OUTCOME_STYLE: Record<string, string> = {
  KILLED: 'bg-zinc-900 text-zinc-500 line-through border-zinc-700',
  INJURED: 'bg-amber-900 text-amber-300 border-transparent',
  UNHARMED: 'bg-emerald-900 text-emerald-300 border-transparent',
  UNKNOWN: 'border-zinc-700 text-zinc-500',
}

function IncidentDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data: incident, isLoading, isError, refetch } = useIncident(id, universe?.id ?? null)

  if (isError) return <ErrorState title="Incident not found" onRetry={() => refetch()} />

  return (
    <div>
      <Link to="/incidents" className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Incidents
      </Link>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      ) : incident ? (
        <>
          <div className="mb-6">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">{incident.type}</h1>
              {incident.verified && <Badge className="bg-emerald-900 text-emerald-300 border-transparent">Verified</Badge>}
            </div>
            <p className="mt-1 text-sm text-zinc-400">
              <FuzzyDate value={incident.date} fallback="Date unknown" />
              {incident.location_text && <> · {incident.location_text}</>}
            </p>
          </div>

          <Tabs defaultValue="participants">
            <TabsList>
              <TabsTrigger value="participants">
                Participants
                {incident.participants.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incident.participants.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="narrative">Narrative</TabsTrigger>
            </TabsList>

            <TabsContent value="participants">
              {incident.participants.length === 0 ? (
                <p className="text-sm text-zinc-600">No participants recorded.</p>
              ) : (
                <div className="space-y-2">
                  {incident.participants.map((p) => (
                    <div key={p.member_id} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3">
                      <Link to="/members/$id" params={{ id: p.member_id }} className="text-sm font-medium text-white hover:text-violet-400 transition-colors">
                        {p.member_id}
                      </Link>
                      <div className="flex items-center gap-2">
                        <Badge className={ROLE_STYLE[p.role] ?? ''}>{p.role}</Badge>
                        <Badge className={OUTCOME_STYLE[p.outcome] ?? ''}>{p.outcome}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="narrative">
              {incident.narrative ? (
                <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{incident.narrative}</p>
              ) : (
                <p className="text-sm text-zinc-600">No narrative recorded.</p>
              )}
            </TabsContent>
          </Tabs>
        </>
      ) : null}
    </div>
  )
}
