import { Link } from '@tanstack/react-router'
import { Mic } from 'lucide-react'
import type { MemberRapGroupRef } from '@/lib/types'

/**
 * The fuchsia "Rapper" pill on a member's page. With rap groups or labels it
 * reads `Rapper · A · B`, each name a link to its page; without, plain `Rapper`.
 * Shown when the member is flagged a rapper or belongs to any group.
 */
export function RapperPill({ isRapper, groups }: { isRapper: boolean; groups: MemberRapGroupRef[] | undefined }) {
  const list = groups ?? []
  if (!isRapper && list.length === 0) return null
  return (
    <span className="inline-flex flex-wrap items-center gap-x-1.5 gap-y-0.5 rounded-full bg-fuchsia-950/50 px-2.5 py-0.5 text-xs text-fuchsia-300 ring-1 ring-fuchsia-800/60">
      <span className="inline-flex items-center gap-1">
        <Mic className="h-3 w-3" aria-hidden />Rapper
      </span>
      {list.map((g) => (
        <span key={g.id} className="inline-flex items-center gap-1.5">
          <span className="text-fuchsia-500/70" aria-hidden>·</span>
          <Link
            from="/$universe" to="/$universe/rap-groups/$id" params={{ id: g.slug ?? g.id }}
            className="rounded-sm underline decoration-fuchsia-400/0 decoration-1 underline-offset-[3px] transition-colors hover:text-fuchsia-100 hover:decoration-fuchsia-300/70 focus-visible:text-fuchsia-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-fuchsia-400/70"
          >
            {g.name}
          </Link>
        </span>
      ))}
    </span>
  )
}
