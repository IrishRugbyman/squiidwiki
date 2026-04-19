import { useUniverses } from '@/api/universes'
import { useUniverseStore } from '@/stores/universe'
import { Badge } from '@/components/ui/badge'

export function UniversesPage() {
  const { data: universes, isLoading, error } = useUniverses()
  const { active, setActive } = useUniverseStore()

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-destructive">Failed to load universes.</div>

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Universes</h1>
      <div className="grid gap-3">
        {universes?.map((u) => (
          <div
            key={u.id}
            className="flex items-center justify-between border rounded-lg p-4 hover:bg-accent/50 cursor-pointer transition-colors"
            onClick={() => setActive(u)}
          >
            <div>
              <p className="font-medium">{u.name}</p>
              <p className="text-sm text-muted-foreground">{u.slug}</p>
            </div>
            {active?.id === u.id && <Badge>Active</Badge>}
          </div>
        ))}
        {universes?.length === 0 && (
          <p className="text-muted-foreground text-sm">No universes yet.</p>
        )}
      </div>
    </div>
  )
}
