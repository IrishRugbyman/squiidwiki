import { Link } from '@tanstack/react-router'
import { useIncidents } from '@/api/incidents'
import { useUniverseStore } from '@/stores/universe'
import { Badge } from '@/components/ui/badge'

export function IncidentsPage() {
  const { active } = useUniverseStore()
  const { data: incidents, isLoading, error } = useIncidents(active?.id)

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-destructive">Failed to load incidents.</div>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Incidents</h1>
        <Link to="/incidents/new" className="bg-primary text-primary-foreground text-sm px-4 py-2 rounded hover:bg-primary/90">
          + New Incident
        </Link>
      </div>
      <div className="border rounded-lg divide-y">
        {incidents?.map((i) => (
          <Link key={i.id} to="/incidents/$id" params={{ id: String(i.id) }}>
            <div className="flex items-center justify-between px-4 py-3 hover:bg-accent/50 transition-colors">
              <div className="flex items-center gap-3">
                <Badge variant={i.incident_type === 'murder' ? 'destructive' : 'default'}>
                  {i.incident_type}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {i.date_sortable ?? 'Unknown date'} · {i.participants.length} participants
                </span>
              </div>
              {i.verified && <Badge variant="outline">Verified</Badge>}
            </div>
          </Link>
        ))}
        {incidents?.length === 0 && (
          <p className="p-4 text-muted-foreground text-sm">No incidents yet.</p>
        )}
      </div>
    </div>
  )
}
