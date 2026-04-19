import { useParams, Link } from '@tanstack/react-router'
import { useSet } from '@/api/sets'
import { Badge } from '@/components/ui/badge'

export function SetDetailPage() {
  const { id } = useParams({ from: '/app/sets/$id' })
  const { data: set, isLoading, error } = useSet(Number(id))

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-destructive">Set not found.</div>
  if (!set) return null

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        {set.emoji && <span className="text-4xl">{set.emoji}</span>}
        <div>
          <h1 className="text-2xl font-bold">{set.name}</h1>
          <Badge variant={set.type === 'active' ? 'default' : 'secondary'} className="mt-1">
            {set.type}
          </Badge>
        </div>
      </div>

      {set.description && (
        <p className="text-muted-foreground">{set.description}</p>
      )}

      <div className="flex gap-2">
        <Link
          to="/sets/$id/edit"
          params={{ id: String(set.id) }}
          className="text-sm border px-3 py-1.5 rounded hover:bg-accent transition-colors"
        >
          Edit
        </Link>
        <Link to="/sets" className="text-sm text-muted-foreground hover:underline px-3 py-1.5">
          ← Back
        </Link>
      </div>
    </div>
  )
}
