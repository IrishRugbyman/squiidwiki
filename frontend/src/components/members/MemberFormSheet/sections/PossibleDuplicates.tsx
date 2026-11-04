import { AlertTriangle } from 'lucide-react'
import { useDebounce } from '@/hooks/useDebounce'
import { useSimilarMembers } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import type { MemberSimilar } from '@/lib/types'

/**
 * Members already on file whose name is close to the one being typed: the check
 * that catches a second record one letter away from the first. Asks
 * /members/similar for the nickname and the legal name separately (a match on
 * either matters) and merges by member, keeping the better score. Advisory only:
 * two people can share a name, so nothing here blocks the save.
 */
export function PossibleDuplicates({
  universeId, nickname, legalName, excludeId,
}: { universeId: string; nickname: string; legalName: string; excludeId?: string }) {
  const universeSlug = useUniverseStore((s) => s.activeUniverse?.slug)
  const dn = useDebounce(nickname.trim(), 400)
  const dl = useDebounce(legalName.trim(), 400)
  const { data: byNick } = useSimilarMembers(universeId, dn, excludeId)
  const { data: byLegal } = useSimilarMembers(universeId, dl, excludeId)

  const merged = new Map<string, MemberSimilar>()
  for (const r of [...(dn.length >= 3 ? byNick ?? [] : []), ...(dl.length >= 3 ? byLegal ?? [] : [])]) {
    const prev = merged.get(r.member.id)
    if (!prev || r.score > prev.score) merged.set(r.member.id, r)
  }
  const rows = [...merged.values()].sort((a, b) => b.score - a.score).slice(0, 5)
  if (rows.length === 0) return null

  return (
    <div className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2">
      <p className="flex items-center gap-1.5 text-xs font-medium text-amber-300">
        <AlertTriangle className="h-3.5 w-3.5" />
        {rows.some((r) => r.score >= 1) ? 'Already on file?' : 'Possible duplicate'}
      </p>
      <ul className="mt-1 space-y-0.5">
        {rows.map(({ member: m, score }) => (
          <li key={m.id} className="flex items-baseline gap-2 text-xs">
            <a
              href={`/${universeSlug}/members/${m.slug ?? m.id}`}
              target="_blank"
              rel="noreferrer"
              className="truncate text-zinc-200 underline-offset-2 hover:underline"
            >
              {m.display_name}
            </a>
            {m.primary_set_name && <span className="truncate text-zinc-500">{m.primary_set_name}</span>}
            <span className="ml-auto shrink-0 text-[10px] text-zinc-500">{m.status} · {Math.round(score * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
