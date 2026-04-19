import { Link } from '@tanstack/react-router'
import { useAlliances } from '@/api/alliances'
import { useUniverseStore } from '@/stores/universe'
import { Badge } from '@/components/ui/badge'

export function AlliancesPage() {
  const { active } = useUniverseStore()
  const { data: alliances, isLoading, error } = useAlliances(active?.id)

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-destructive">Failed to load alliances.</div>

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Alliances</h1>
      <div className="border rounded-lg divide-y">
        {alliances?.map((a) => (
          <div key={a.id} className="flex items-center justify-between px-4 py-3">
            <span className="font-medium">{a.name}</span>
            <Badge variant={a.status === 'active' ? 'default' : 'secondary'}>
              {a.status}
            </Badge>
          </div>
        ))}
        {alliances?.length === 0 && (
          <p className="p-4 text-muted-foreground text-sm">No alliances yet.</p>
        )}
      </div>
    </div>
  )
}
