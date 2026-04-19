import { Link } from '@tanstack/react-router'
import { useSets } from '@/api/sets'
import { useUniverseStore } from '@/stores/universe'
import { Badge } from '@/components/ui/badge'

export function SetsPage() {
  const { active } = useUniverseStore()
  const { data: sets, isLoading, error } = useSets(active?.id)

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-destructive">Failed to load sets.</div>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Sets</h1>
        <Link to="/sets/new" className="bg-primary text-primary-foreground text-sm px-4 py-2 rounded hover:bg-primary/90">
          + New Set
        </Link>
      </div>
      <div className="border rounded-lg divide-y">
        {sets?.map((s) => (
          <Link key={s.id} to="/sets/$id" params={{ id: String(s.id) }}>
            <div className="flex items-center justify-between px-4 py-3 hover:bg-accent/50 transition-colors">
              <div className="flex items-center gap-3">
                {s.emoji && <span className="text-xl">{s.emoji}</span>}
                <span className="font-medium">{s.name}</span>
              </div>
              <Badge variant={s.type === 'active' ? 'default' : 'secondary'}>
                {s.type}
              </Badge>
            </div>
          </Link>
        ))}
        {sets?.length === 0 && (
          <p className="p-4 text-muted-foreground text-sm">No sets yet.</p>
        )}
      </div>
    </div>
  )
}
