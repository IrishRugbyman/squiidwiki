import { createLazyFileRoute, Link } from '@tanstack/react-router'
import { Flag, Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { EmptyState } from '@/components/EmptyState'
import { GangFormSheet } from '@/components/gangs/GangFormSheet'
import { GangSwatch } from '@/components/gangs/GangSwatch'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { effectiveNation, gangForest, NATION_LABEL, NATION_NUMBER, type GangNode } from '@/lib/gangs'
import { useGangs } from '@/lib/queries'
import type { GangListItem, GangNation } from '@/lib/types'
import { useAuthStore } from '@/stores/auth'
import { useUniverseStore } from '@/stores/universe'

export const Route = createLazyFileRoute('/_app/$universe/gangs/')({
  component: GangsPage,
})

const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

const SECTIONS: { key: GangNation | 'NONE'; title: string; blurb: string }[] = [
  { key: 'FOLK', title: `${NATION_LABEL.FOLK} (${NATION_NUMBER.FOLK})`, blurb: 'The six-pointed star: the Gangster Disciples and the cards allied with them.' },
  { key: 'PEOPLE', title: `${NATION_LABEL.PEOPLE} (${NATION_NUMBER.PEOPLE})`, blurb: 'The five-pointed star: the Vice Lords, Latin Kings, Stones and their allies.' },
  { key: 'NONE', title: 'Crips, Bloods and other lineages', blurb: 'Los Angeles cards and their sets, the Sureños and the rest, which ride under neither star.' },
]

function haystack(g: GangListItem): string {
  return fold([g.name, ...(g.aliases ?? []), ...(g.card_aliases ?? []), ...(g.symbols ?? []), g.origin ?? ''].join(' '))
}

/** Keep a node when it or any card under it matches; prune the rest. */
function filterForest(nodes: GangNode[], match: (g: GangListItem) => boolean): GangNode[] {
  const out: GangNode[] = []
  for (const n of nodes) {
    const children = filterForest(n.children, match)
    if (match(n.gang) || children.length) out.push({ gang: n.gang, children })
  }
  return out
}

function Counts({ g }: { g: GangListItem }) {
  return (
    <span className="text-[11px] tabular-nums text-zinc-400">
      {plural(g.set_count, 'set')} · {plural(g.member_count, 'member')}
    </span>
  )
}

function BranchList({ nodes, depth = 0 }: { nodes: GangNode[]; depth?: number }) {
  if (!nodes.length) return null
  return (
    <ul className={depth ? 'ml-4 border-l border-zinc-800 pl-3' : ''}>
      {nodes.map((n) => (
        <li key={n.gang.id}>
          <Link
            from="/$universe" to="/$universe/gangs/$id"
            params={{ id: n.gang.slug ?? n.gang.id }}
            className="flex items-center gap-2 rounded px-1.5 py-1 text-sm text-zinc-300 transition-colors hover:bg-zinc-800/60 hover:text-white"
          >
            <GangSwatch color={n.gang.color} secondary={n.gang.color_secondary} size="xs" />
            <span className="min-w-0 flex-1 truncate">{n.gang.name}</span>
            <Counts g={n.gang} />
          </Link>
          <BranchList nodes={n.children} depth={depth + 1} />
        </li>
      ))}
    </ul>
  )
}

function GangCard({ node }: { node: GangNode }) {
  const g = node.gang
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/40">
      <Link
        from="/$universe" to="/$universe/gangs/$id"
        params={{ id: g.slug ?? g.id }}
        className="group flex items-start gap-3 p-3 transition-colors hover:bg-zinc-800/40"
      >
        <GangSwatch color={g.color} secondary={g.color_secondary} size="lg" />
        <span className="min-w-0 flex-1">
          <span className="block truncate font-semibold text-zinc-100 group-hover:text-white">{g.name}</span>
          {g.aliases?.length ? (
            <span className="block truncate text-[11px] text-zinc-400">{g.aliases.join(' · ')}</span>
          ) : null}
          <span className="mt-0.5 block"><Counts g={g} /></span>
        </span>
      </Link>
      {(g.card_description || g.description) && (
        // Padding on a wrapper: on the clamped paragraph itself the browser
        // clips at the padding edge and a third line shows through it.
        <div className="px-3 pb-2.5">
          <p className="line-clamp-2 text-xs text-zinc-400">{g.card_description || g.description}</p>
        </div>
      )}
      {node.children.length > 0 && (
        <div className="border-t border-zinc-800/80 px-1.5 py-1.5">
          <BranchList nodes={node.children} />
        </div>
      )}
    </div>
  )
}

function GangsPage() {
  const user = useAuthStore((s) => s.user)
  const universeId = useUniverseStore((s) => s.activeUniverse?.id ?? null)
  const { data, isLoading } = useGangs(universeId)
  const [q, setQ] = useState('')
  const [creating, setCreating] = useState(false)
  const isAdmin = user?.global_role === 'ADMIN'

  const gangs = useMemo(() => data?.items ?? [], [data])
  const sections = useMemo(() => {
    const byId = new Map(gangs.map((g) => [g.id, g]))
    const terms = fold(q.trim()).split(/\s+/).filter(Boolean)
    const match = (g: GangListItem) => terms.every((t) => haystack(g).includes(t))
    const forest = filterForest(gangForest(gangs), match)
    return SECTIONS.map((s) => ({
      ...s,
      roots: forest.filter((n) => (effectiveNation(n.gang, byId) ?? 'NONE') === s.key),
    }))
  }, [gangs, q])

  if (!universeId) {
    return <div className="py-24 text-center text-sm text-zinc-400">Select a universe to see its gangs.</div>
  }

  const total = gangs.length
  const shown = sections.reduce((n, s) => n + s.roots.length, 0)

  return (
    <div>
      <PageHeader
        title="Gangs"
        description={`${plural(total, 'card')}: the nations and lineages the sets of this universe claim.`}
        action={isAdmin ? (
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            New gang
          </Button>
        ) : undefined}
      />
      <div className="relative mb-6 max-w-sm">
        <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" aria-hidden />
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search names, aliases, symbols"
          className="pl-8"
          aria-label="Search gangs"
        />
      </div>

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-lg" />)}
        </div>
      ) : total === 0 ? (
        <EmptyState icon={Flag} title="No gangs yet" description="Create one to start tagging sets, alliances and members." />
      ) : shown === 0 ? (
        <p className="py-12 text-center text-sm text-zinc-400">No gang matches &ldquo;{q}&rdquo;.</p>
      ) : (
        <div className="space-y-8">
          {sections.filter((s) => s.roots.length).map((s) => (
            <section key={s.key} aria-labelledby={`nation-${s.key}`}>
              <h2 id={`nation-${s.key}`} className="text-sm font-semibold text-zinc-200">{s.title}</h2>
              <p className="mb-3 text-xs text-zinc-500">{s.blurb}</p>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {s.roots.map((n) => <GangCard key={n.gang.id} node={n} />)}
              </div>
            </section>
          ))}
        </div>
      )}

      {creating && (
        <GangFormSheet open onClose={() => setCreating(false)} initial={null} universeId={universeId} />
      )}
    </div>
  )
}
