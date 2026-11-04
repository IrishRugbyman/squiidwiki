import { Link } from '@tanstack/react-router'
import { Fragment } from 'react'
import { cn } from '@/lib/utils'
import type { MediaOwner, MediaPerson } from '@/lib/types'
import { isOrdered } from './people'

const linkCls =
  'rounded-sm underline decoration-zinc-500/50 decoration-1 underline-offset-[3px] transition-colors hover:text-violet-300 hover:decoration-violet-300/70 focus-visible:text-violet-300 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-violet-400/70'

interface PhotoPeopleProps {
  people: readonly MediaPerson[]
  /** Called when a name is followed, so a viewer sitting over the page can close. */
  onNavigate?: () => void
  className?: string
}

/**
 * Who is in a photo, as links to their pages: "Tay, Doe" when the order is
 * known (left to right), "With Tay, Doe" when it is not. Renders nothing for a
 * photo nobody is tagged in.
 */
export function PhotoPeople({ people, onNavigate, className }: PhotoPeopleProps) {
  if (people.length === 0) return null
  return (
    <p className={cn('min-w-0', className)} data-testid="photo-people">
      {!isOrdered(people) && 'With '}
      {people.map((p, i) => (
        <Fragment key={p.member_id}>
          {i > 0 && ', '}
          <Link
            from="/$universe"
            to="/$universe/members/$id"
            params={{ id: p.slug ?? p.member_id }}
            onClick={onNavigate}
            className={linkCls}
          >
            {p.display_name}
          </Link>
        </Fragment>
      ))}
    </p>
  )
}

/** A link to the page of the entity a photo belongs to (plain text for a source, which has none). */
export function OwnerLink({ owner, onNavigate }: { owner: MediaOwner; onNavigate?: () => void }) {
  const id = owner.slug ?? owner.id
  const common = { from: '/$universe' as const, params: { id }, onClick: onNavigate, className: linkCls }
  switch (owner.type) {
    case 'member':
      return <Link {...common} to="/$universe/members/$id">{owner.name}</Link>
    case 'set':
      return <Link {...common} to="/$universe/sets/$id">{owner.name}</Link>
    case 'incident':
      return <Link {...common} to="/$universe/incidents/$id">{owner.name}</Link>
    case 'alliance':
      return <Link {...common} to="/$universe/alliances/$id">{owner.name}</Link>
    case 'rap_group':
      return <Link {...common} to="/$universe/rap-groups/$id">{owner.name}</Link>
    case 'municipality':
      return <Link {...common} to="/$universe/municipalities/$id">{owner.name}</Link>
    case 'source':
      return <span>{owner.name}</span>
  }
}
