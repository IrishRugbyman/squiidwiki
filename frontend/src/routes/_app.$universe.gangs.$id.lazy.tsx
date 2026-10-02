import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { GitFork, Network, Pencil, Plus, Shield, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { DetailRow, None, PanelHeading, StatStrip } from '@/components/detail/DetailParts'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { GangFormSheet } from '@/components/gangs/GangFormSheet'
import { GangSwatch } from '@/components/gangs/GangSwatch'
import { LinkifiedText } from '@/components/LinkifiedText'
import { AllianceStatusBadge, SetStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useEditShortcut } from '@/hooks/useKeymap'
import { gangBandStyle, NATION_LABEL, NATION_NUMBER } from '@/lib/gangs'
import { useDeleteGang, useGangDetail } from '@/lib/queries'
import type { GangDetail, GangListItem, GangSetItem } from '@/lib/types'
import { useAuthStore } from '@/stores/auth'
import { useUniverseStore } from '@/stores/universe'
import { SetAvatar } from './_app.$universe.sets.index'

// The gang page, in its own chunk (the route file only declares it).
export const Route = createLazyFileRoute('/_app/$universe/gangs/$id')({
  component: GangDetailPage,
})

/** The card's aliases and this universe's own, once each. */
function aliasesOf(g: { aliases: string[] | null; card_aliases: string[] | null }): string[] {
  const seen = new Set<string>()
  return [...(g.card_aliases ?? []), ...(g.aliases ?? [])].filter((a) => {
    const k = a.toLowerCase()
    if (seen.has(k)) return false
    seen.add(k)
    return true
  })
}

const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

function ColorChip({ hex, label }: { hex: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-900/60 py-0.5 pl-1 pr-2 text-xs text-zinc-300">
      <span className="h-3.5 w-3.5 rounded ring-1 ring-zinc-700" style={{ backgroundColor: hex }} aria-hidden />
      <span className="font-mono">{hex}</span>
      <span className="sr-only">{label}</span>
    </span>
  )
}

function SetTile({ set, gangColor }: { set: GangSetItem; gangColor: string | null }) {
  return (
    <Link
      from="/$universe" to="/$universe/sets/$id"
      params={{ id: set.slug ?? set.id }}
      className="group flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2.5 transition-colors hover:border-zinc-700 hover:bg-zinc-800/40"
    >
      <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} gangColor={gangColor} />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-zinc-100 group-hover:text-white">{set.name}</span>
          {!set.is_primary && (
            <span className="shrink-0 rounded bg-zinc-800 px-1.5 py-px text-[10px] text-zinc-400" title="Claims this card as a second gang">
              also
            </span>
          )}
        </span>
        <span className="block truncate text-[11px] text-zinc-400">
          {[set.municipality_name, set.alliance_name].filter(Boolean).join(' · ') || plural(set.member_count, 'member')}
        </span>
      </span>
      <span className="flex shrink-0 flex-col items-end gap-1">
        <SetStatusBadge status={set.status} />
        <span className="text-[11px] tabular-nums text-zinc-500">{set.member_count}</span>
      </span>
    </Link>
  )
}

function BranchTile({ g }: { g: GangListItem }) {
  return (
    <Link
      from="/$universe" to="/$universe/gangs/$id"
      params={{ id: g.slug ?? g.id }}
      className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2.5 transition-colors hover:border-zinc-700 hover:bg-zinc-800/40"
    >
      <GangSwatch color={g.color} secondary={g.color_secondary} size="md" />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-zinc-100">{g.name}</span>
        <span className="text-[11px] tabular-nums text-zinc-400">
          {plural(g.set_count, 'set')} · {plural(g.member_count, 'member')}
        </span>
      </span>
    </Link>
  )
}

function Header({ gang, onEdit, onDelete, onBranch, isAdmin }: {
  gang: GangDetail
  onEdit: () => void
  onDelete: () => void
  onBranch: () => void
  isAdmin: boolean
}) {
  // A branch rides under its nearest ancestor's star.
  const nation = gang.nation
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/40">
      <div className="h-3 w-full" style={gangBandStyle(gang.color, gang.color_secondary)} aria-hidden />
      <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-start">
        <GangSwatch color={gang.color} secondary={gang.color_secondary} size="lg" className="h-16 w-16 rounded-xl" />
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold text-white">{gang.name}</h1>
          {aliasesOf(gang).length ? <p className="mt-0.5 text-sm text-zinc-400">{aliasesOf(gang).join(' · ')}</p> : null}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {nation && (
              <span className="rounded-full bg-violet-950/60 px-2.5 py-0.5 text-xs font-medium text-violet-300 ring-1 ring-violet-800/50">
                {NATION_LABEL[nation]} · {NATION_NUMBER[nation]}
              </span>
            )}
            {gang.parent && (
              <Link
                from="/$universe" to="/$universe/gangs/$id"
                params={{ id: gang.parent.slug ?? gang.parent.id }}
                className="inline-flex items-center gap-1.5 rounded-full bg-zinc-800/80 px-2.5 py-0.5 text-xs text-zinc-300 ring-1 ring-zinc-700 hover:ring-zinc-500"
              >
                <GangSwatch color={gang.parent.color} secondary={gang.parent.color_secondary} size="xs" />
                Branch of {gang.parent.name}
              </Link>
            )}
          </div>
        </div>
        {isAdmin && (
          <div className="flex shrink-0 gap-1.5">
            <Button size="sm" variant="outline" onClick={onBranch} title="Add a branch of this card">
              <Plus className="mr-1 h-3.5 w-3.5" />Branch
            </Button>
            <Button size="sm" variant="outline" onClick={onEdit} title="Edit (E)">
              <Pencil className="mr-1 h-3.5 w-3.5" />Edit
            </Button>
            <Button size="sm" variant="ghost" onClick={onDelete} className="text-red-400 hover:text-red-300" aria-label="Delete gang">
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

function GangDetailPage() {
  const { id } = Route.useParams()
  const navigate = useNavigate()
  const universeId = useUniverseStore((s) => s.activeUniverse?.id ?? null)
  const universeName = useUniverseStore((s) => s.activeUniverse?.name ?? 'this universe')
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.global_role === 'ADMIN'
  const { data: gang, isLoading, isError, refetch } = useGangDetail(id, universeId)
  const del = useDeleteGang(universeId ?? '')
  const [editing, setEditing] = useState(false)
  const [branching, setBranching] = useState(false)
  const [deleting, setDeleting] = useState(false)
  useEditShortcut(() => { if (isAdmin && gang) setEditing(true) })

  if (!universeId) return <div className="py-24 text-center text-sm text-zinc-400">Select a universe first.</div>
  if (isError) return <ErrorState title="Gang not found" onRetry={() => refetch()} />
  if (isLoading || !gang) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-16 rounded-lg" />
      </div>
    )
  }

  const trail = [...gang.ancestors].reverse()
  const hasFacts = gang.origin || gang.founded_at?.year || gang.color || gang.symbols?.length

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Gangs', to: '/$universe/gangs' },
          ...trail.map((a) => ({ label: a.name, to: `/$universe/gangs/${a.slug ?? a.id}` })),
          { label: gang.name },
        ]}
      />
      <Header
        gang={gang}
        isAdmin={isAdmin}
        onEdit={() => setEditing(true)}
        onBranch={() => setBranching(true)}
        onDelete={() => setDeleting(true)}
      />
      <StatStrip
        cells={[
          { label: 'Sets', value: gang.set_count, accent: 'text-zinc-100' },
          { label: 'Members', value: gang.member_count, accent: 'text-zinc-100' },
          { label: 'Alliances', value: gang.alliance_count, accent: 'text-blue-300' },
          { label: 'Branches', value: gang.branches.length, accent: 'text-violet-300' },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-w-0 space-y-6">
          {(gang.card_description || gang.description) && (
            <section>
              <PanelHeading>About</PanelHeading>
              {gang.card_description && (
                <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300">
                  <LinkifiedText text={gang.card_description} />
                </p>
              )}
              {gang.description && (
                <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2">
                  <p className="mb-1 text-[11px] font-medium uppercase tracking-wider text-zinc-500">In {universeName}</p>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300">
                    <LinkifiedText text={gang.description} />
                  </p>
                </div>
              )}
            </section>
          )}

          {gang.branches.length > 0 && (
            <section>
              <PanelHeading><GitFork className="mr-1 inline h-3.5 w-3.5" />Branches</PanelHeading>
              <div className="grid gap-2 sm:grid-cols-2">
                {gang.branches.map((b) => <BranchTile key={b.id} g={b} />)}
              </div>
            </section>
          )}

          <section>
            <PanelHeading><Shield className="mr-1 inline h-3.5 w-3.5" />Sets claiming {gang.name}</PanelHeading>
            {gang.sets.length === 0 ? (
              <EmptyState icon={Shield} title="No sets yet" description="Sets claim a card from their own form; a set can claim several." />
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {gang.sets.map((s) => <SetTile key={s.id} set={s} gangColor={gang.color} />)}
              </div>
            )}
          </section>
        </div>

        <aside className="space-y-6">
          {hasFacts && (
            <section>
              <PanelHeading>Card</PanelHeading>
              <dl className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-3 py-1">
                <DetailRow label="Origin">{gang.origin ?? <None />}</DetailRow>
                <DetailRow label="Founded">{gang.founded_at?.year ? <FuzzyDate value={gang.founded_at} /> : <None />}</DetailRow>
                <DetailRow label="Colors">
                  {gang.color ? (
                    <span className="flex flex-wrap gap-1.5">
                      <ColorChip hex={gang.color} label="primary" />
                      {gang.color_secondary && <ColorChip hex={gang.color_secondary} label="secondary" />}
                    </span>
                  ) : <None />}
                </DetailRow>
                <DetailRow label="Symbols">
                  {gang.symbols?.length ? (
                    <span className="flex flex-wrap gap-1">
                      {gang.symbols.map((s) => (
                        <span key={s} className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs text-zinc-300">{s}</span>
                      ))}
                    </span>
                  ) : <None />}
                </DetailRow>
              </dl>
            </section>
          )}
          <section>
            <PanelHeading><Network className="mr-1 inline h-3.5 w-3.5" />Alliances</PanelHeading>
            {gang.alliances.length === 0 ? (
              <p className="text-xs text-zinc-500">No alliance is tagged with this card.</p>
            ) : (
              <ul className="space-y-1">
                {gang.alliances.map((a) => (
                  <li key={a.id}>
                    <Link
                      from="/$universe" to="/$universe/alliances/$id"
                      params={{ id: a.slug ?? a.id }}
                      className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm text-blue-300 hover:bg-zinc-800/60"
                    >
                      <span className="truncate">{a.name}</span>
                      <AllianceStatusBadge status={a.status} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>

      {editing && (
        <GangFormSheet open onClose={() => setEditing(false)} initial={gang} universeId={universeId} />
      )}
      {branching && (
        <GangFormSheet open onClose={() => setBranching(false)} initial={null} universeId={universeId} defaultParentId={gang.id} />
      )}
      {deleting && (
        <ConfirmDialog
          open
          title={`Delete ${gang.name}?`}
          description={`${plural(gang.set_count, 'set')} lose this card (a set with another gang keeps it, as its new primary). Alliances and members tagged with it are unlinked, and branches become top-level cards.`}
          confirmLabel="Delete"
          destructive
          pending={del.isPending}
          onConfirm={() =>
            del.mutate(gang.id, {
              onSuccess: () => {
                toast.success(`Deleted ${gang.name}`)
                navigate({ from: '/$universe', to: '/$universe/gangs' })
              },
              onError: () => setDeleting(false),
            })
          }
          onCancel={() => setDeleting(false)}
        />
      )}
    </div>
  )
}
