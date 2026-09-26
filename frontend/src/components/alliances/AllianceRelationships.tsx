import { Link } from '@tanstack/react-router'
import { Plus, Swords, Users, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { AffiliationCombobox, type ComboboxItem } from '@/components/members/MemberFormSheet/pickers/AffiliationCombobox'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  useAddAllianceRelationship,
  useAlliances,
  useAllSets,
  useDeleteAllianceRelationship,
} from '@/lib/queries'
import type { AllianceRelationshipItem, SetRelationshipType } from '@/lib/types'

// Alliance-level allies and enemies. The far side is another alliance or a
// single set; the backend refuses a set inside the alliance itself.

const byName = (a: AllianceRelationshipItem, b: AllianceRelationshipItem) =>
  a.other_name.localeCompare(b.other_name, undefined, { sensitivity: 'base', numeric: true })

function OtherLink({ rel }: { rel: AllianceRelationshipItem }) {
  const id = rel.other_slug ?? rel.other_id
  const cls = 'truncate text-sm text-zinc-300 hover:text-violet-400'
  return rel.other_kind === 'alliance'
    ? <Link to="/alliances/$id" params={{ id }} className={cls}>{rel.other_name}</Link>
    : <Link to="/sets/$id" params={{ id }} className={cls}>{rel.other_name}</Link>
}

function KindTag({ kind }: { kind: AllianceRelationshipItem['other_kind'] }) {
  return (
    <span className="shrink-0 rounded border border-zinc-800 px-1 text-[10px] uppercase tracking-wider text-zinc-500">
      {kind === 'alliance' ? 'alliance' : 'set'}
    </span>
  )
}

function Group({ title, tone, rows, render }: {
  title: string
  tone: string
  rows: AllianceRelationshipItem[]
  render: (r: AllianceRelationshipItem) => React.ReactNode
}) {
  if (rows.length === 0) return null
  return (
    <div>
      <p className={`mb-1 text-[10px] font-semibold uppercase tracking-wider ${tone}`}>{title} ({rows.length})</p>
      <div className="space-y-0.5">{rows.map(render)}</div>
    </div>
  )
}

/** The alliance page's list of its own allies and enemies, editable. */
export function AllianceRelationshipsPanel({ allianceId, universeId, relationships, onAdd }: {
  allianceId: string
  universeId: string
  relationships: AllianceRelationshipItem[]
  onAdd: () => void
}) {
  const remove = useDeleteAllianceRelationship(allianceId, universeId)
  const allies = relationships.filter((r) => r.type === 'FRIEND').sort(byName)
  const enemies = relationships.filter((r) => r.type === 'ENEMY').sort(byName)

  function row(r: AllianceRelationshipItem) {
    const dot = r.type === 'FRIEND' ? 'bg-emerald-500' : 'bg-red-500'
    return (
      <div key={r.id} className="group flex items-center justify-between gap-2 rounded px-1.5 py-1 hover:bg-zinc-800/50">
        <span className="flex min-w-0 items-center gap-2">
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
          <OtherLink rel={r} />
          <KindTag kind={r.other_kind} />
          {r.from_date && <span className="shrink-0 text-[11px] text-zinc-500">since <FuzzyDate value={r.from_date} /></span>}
        </span>
        <button
          type="button"
          aria-label={`Remove relationship with ${r.other_name}`}
          disabled={remove.isPending && remove.variables === r.id}
          onClick={() => remove.mutate(r.id)}
          className="shrink-0 text-zinc-500 transition-all hover:text-red-400 focus-visible:opacity-100 group-hover:opacity-100 disabled:opacity-40 pointer-fine:opacity-0"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3">
      <div className="mb-2.5 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Relationships{relationships.length > 0 ? ` (${relationships.length})` : ''}
        </p>
        <button type="button" onClick={onAdd} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
          <Plus className="h-3 w-3" />Add
        </button>
      </div>
      {relationships.length === 0 ? (
        <p className="text-xs text-zinc-400">No relationships recorded.</p>
      ) : (
        <div className="space-y-3">
          <Group title="Allies" tone="text-emerald-400" rows={allies} render={row} />
          <Group title="Enemies" tone="text-red-400" rows={enemies} render={row} />
        </div>
      )}
    </div>
  )
}

/**
 * On a set page: the links its alliance holds, and alliances that name the set.
 * Read-only here; they are edited on the alliance's page.
 */
export function InheritedAllianceRelationships({ relationships }: { relationships: AllianceRelationshipItem[] }) {
  if (relationships.length === 0) return null
  const allies = relationships.filter((r) => r.type === 'FRIEND').sort(byName)
  const enemies = relationships.filter((r) => r.type === 'ENEMY').sort(byName)

  function row(r: AllianceRelationshipItem) {
    const dot = r.type === 'FRIEND' ? 'bg-emerald-500/60' : 'bg-red-500/60'
    return (
      <div key={r.id} className="flex items-center gap-2 rounded px-1.5 py-1 hover:bg-zinc-800/50">
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
        <OtherLink rel={r} />
        <KindTag kind={r.other_kind} />
        {r.via_alliance_id && (
          <Link to="/alliances/$id" params={{ id: r.via_alliance_slug ?? r.via_alliance_id }}
            className="ml-auto shrink-0 truncate text-[11px] text-zinc-500 hover:text-violet-400"
            title="Held by this set's alliance, so every set in it shares the link">
            via {r.via_alliance_name ?? 'its alliance'}
          </Link>
        )}
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3">
      <p className="mb-2.5 text-xs font-medium uppercase tracking-wider text-zinc-400">
        Through alliances ({relationships.length})
      </p>
      <div className="space-y-3">
        <Group title="Allies" tone="text-emerald-400" rows={allies} render={row} />
        <Group title="Enemies" tone="text-red-400" rows={enemies} render={row} />
      </div>
    </div>
  )
}

export function AddAllianceRelationshipDialog({ allianceId, allianceName, universeId, existing, open, onClose }: {
  allianceId: string
  allianceName: string
  universeId: string
  existing: AllianceRelationshipItem[]
  open: boolean
  onClose: () => void
}) {
  const { data: alliances } = useAlliances(universeId)
  const { data: sets } = useAllSets(universeId)
  const add = useAddAllianceRelationship(allianceId, universeId)
  const [target, setTarget] = useState('')
  const [type, setType] = useState<SetRelationshipType>('ENEMY')
  const [since, setSince] = useState<FuzzyDateValue | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Keys carry the kind, so the one picker can hold alliances and sets.
  const items = useMemo<ComboboxItem[]>(() => {
    const taken = new Set(existing.filter((r) => r.is_current).map((r) => `${r.other_kind === 'alliance' ? 'a' : 's'}:${r.other_id}`))
    const out: ComboboxItem[] = []
    for (const a of alliances?.items ?? []) {
      if (a.id === allianceId || taken.has(`a:${a.id}`)) continue
      out.push({ id: `a:${a.id}`, name: a.name, hint: 'alliance', dotClass: 'bg-violet-400', keywords: (a.aliases ?? []).join(' ') })
    }
    for (const s of sets?.items ?? []) {
      // Its own sets are refused by the server; reserved sets hold no links.
      if (s.is_reserved || s.alliance_id === allianceId || taken.has(`s:${s.id}`)) continue
      out.push({
        id: `s:${s.id}`,
        name: s.name,
        hint: s.alliance_name ? `set · ${s.alliance_name}` : 'set',
        dotClass: s.status === 'EXTINCT' ? 'bg-zinc-600' : 'bg-emerald-400',
        keywords: (s.name_variants ?? []).flatMap((v) => [v.name, v.initials, v.number]).filter(Boolean).join(' '),
      })
    }
    return out
  }, [alliances, sets, allianceId, existing])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!target) return
    setError(null)
    const [kind, id] = target.split(':')
    try {
      await add.mutateAsync({
        ...(kind === 'a' ? { target_alliance_id: id } : { target_set_id: id }),
        type,
        from_date: since ?? undefined,
      })
      setTarget(''); setSince(null)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add relationship')
    }
  }

  const isAlly = type === 'FRIEND'
  const toggle = (t: SetRelationshipType, active: string) =>
    `flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
      type === t ? active : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-300'
    }`

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isAlly ? <Users className="h-4 w-4 text-emerald-400" /> : <Swords className="h-4 w-4 text-red-400" />}
            Add {isAlly ? 'ally' : 'enemy'} of {allianceName}
          </DialogTitle>
          <DialogDescription>
            Held by the whole alliance, against another alliance or a single set. Every set in {allianceName} shows it.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-2">
            <button type="button" onClick={() => setType('FRIEND')} className={toggle('FRIEND', 'border-emerald-600 bg-emerald-950/40 text-emerald-300')}>
              <Users className="h-4 w-4" /> Ally
            </button>
            <button type="button" onClick={() => setType('ENEMY')} className={toggle('ENEMY', 'border-red-700 bg-red-950/40 text-red-300')}>
              <Swords className="h-4 w-4" /> Enemy
            </button>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">Alliance or set</label>
            <AffiliationCombobox label="Alliance or set" value={target} onChange={setTarget} items={items} placeholder="Select an alliance or a set…" />
          </div>
          <FuzzyDateInput label="Since" idPrefix="alliance-rel-since" value={since} onChange={setSince} />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={!target || add.isPending}>
              {add.isPending ? 'Adding…' : `Add ${isAlly ? 'ally' : 'enemy'}`}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
