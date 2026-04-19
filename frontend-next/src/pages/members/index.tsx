import { Link } from '@tanstack/react-router'
import { useMembers } from '@/api/members'
import { useUniverseStore } from '@/stores/universe'
import { Badge } from '@/components/ui/badge'

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  alive: 'default',
  dead: 'destructive',
  locked_up: 'outline',
  unknown: 'secondary',
}

export function MembersPage() {
  const { active } = useUniverseStore()
  const { data: members, isLoading, error } = useMembers(active?.id)

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-destructive">Failed to load members.</div>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Members</h1>
        <Link to="/members/new" className="bg-primary text-primary-foreground text-sm px-4 py-2 rounded hover:bg-primary/90">
          + New Member
        </Link>
      </div>
      <div className="border rounded-lg divide-y">
        {members?.map((m) => (
          <Link key={m.id} to="/members/$id" params={{ id: String(m.id) }}>
            <div className="flex items-center justify-between px-4 py-3 hover:bg-accent/50 transition-colors">
              <span className="font-medium">{m.name}</span>
              <Badge variant={statusVariant[m.status] ?? 'secondary'}>
                {m.status}
              </Badge>
            </div>
          </Link>
        ))}
        {members?.length === 0 && (
          <p className="p-4 text-muted-foreground text-sm">No members yet.</p>
        )}
      </div>
    </div>
  )
}
