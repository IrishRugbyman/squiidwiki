import { useParams, Link } from '@tanstack/react-router'
import { useMember } from '@/api/members'
import { Badge } from '@/components/ui/badge'

export function MemberDetailPage() {
  const { id } = useParams({ from: '/app/members/$id' })
  const { data: member, isLoading, error } = useMember(Number(id))

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-destructive">Member not found.</div>
  if (!member) return null

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">{member.name}</h1>
          <Badge className="mt-1">{member.status}</Badge>
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-4 text-sm">
        {member.birth_date_sortable && (
          <>
            <dt className="text-muted-foreground">Born</dt>
            <dd>{member.birth_date_sortable}</dd>
          </>
        )}
        {member.death_date_sortable && (
          <>
            <dt className="text-muted-foreground">Died</dt>
            <dd>{member.death_date_sortable}</dd>
          </>
        )}
        {member.set_id && (
          <>
            <dt className="text-muted-foreground">Set</dt>
            <dd>
              <Link to="/sets/$id" params={{ id: String(member.set_id) }} className="hover:underline text-primary">
                #{member.set_id}
              </Link>
            </dd>
          </>
        )}
      </dl>

      {member.description && (
        <p className="text-muted-foreground">{member.description}</p>
      )}

      <Link to="/members" className="text-sm text-muted-foreground hover:underline">
        ← Back
      </Link>
    </div>
  )
}
