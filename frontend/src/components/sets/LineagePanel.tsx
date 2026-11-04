import { Link } from '@tanstack/react-router'
import { ListTree, Plus, Trash2, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { AffiliationCombobox } from '@/components/members/MemberFormSheet/pickers/AffiliationCombobox'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  useAddAllianceLineage,
  useAddSetLineage,
  useAlliances,
  useAllSets,
  useDeleteAllianceLineage,
  useDeleteSetLineage,
  useEndAllianceLineage,
  useEndSetLineage,
  useSetLineage,
} from '@/lib/queries'
import { setPickerItems } from '@/lib/setPicker'
import type { AllianceLineageItem, SetLineageItem, SetLineageKind } from '@/lib/types'

// ─── Lineage side panel ───────────────────────────────────────────────────────
//
// Descent, which the relationships panel above deliberately cannot show: that
// table stores its endpoints in UUID order, so it has no way to say which of a
// pair came out of the other. A pair can appear in both panels at once, and a
// splinter set at war with the set it left is exactly that case.

const LINEAGE_KIND_LABEL: Record<SetLineageKind, string> = {
  SPLINTERED_FROM: 'splintered from',
  RENAMED_FROM: 'renamed from',
  MERGED_FROM: 'merged from',
  YOUNGER_GENERATION_OF: 'younger generation of',
}

/**
 * The row as a sentence that names both sets, so it reads the same from either page.
 * Every kind is stored as "child KIND parent"; `child` and `parent` are rendered nodes
 * (this set's name in bold, the other as a link).
 */
function lineageSentence(kind: SetLineageKind, child: React.ReactNode, parent: React.ReactNode): React.ReactNode {
  switch (kind) {
    case 'SPLINTERED_FROM':
      return <>{child} splintered from {parent}</>
    case 'RENAMED_FROM':
      return <>{parent} was renamed {child}</>
    case 'MERGED_FROM':
      return <>{parent} merged into {child}</>
    case 'YOUNGER_GENERATION_OF':
      return <>{child} is the younger generation of {parent}</>
  }
}

type Row = SetLineageItem | AllianceLineageItem
type Noun = 'set' | 'alliance'

const OTHER_ROUTE = { set: '/$universe/sets/$id', alliance: '/$universe/alliances/$id' } as const

interface LineageOps {
  rows: Row[]
  selfName: string
  noun: Noun
  onEnd: (lineageId: string) => void
  onRemove: (lineageId: string) => void
  /** What can be picked as the other side, already excluding this record. */
  candidates: { id: string; name: string }[]
  onAdd: (body: { other_id: string; kind: SetLineageKind; direction: 'parent' | 'child' }) => Promise<unknown>
  adding: boolean
}

/** A set's descent: which sets it came out of, and which came out of it. */
export function LineagePanel({ setId, setName, universeId }: { setId: string; setName: string; universeId: string }) {
  const { data: rows } = useSetLineage(setId, universeId)
  const end = useEndSetLineage(setId, universeId)
  const remove = useDeleteSetLineage(setId, universeId)
  const add = useAddSetLineage(setId, universeId)
  const { data: allSets } = useAllSets(universeId)
  // Police, Civilian and Unknown are placeholders, not organisations anything descends from.
  const candidates = useMemo(
    () => setPickerItems((allSets?.items ?? []).filter((s) => s.id !== setId && !s.is_reserved)),
    [allSets, setId],
  )
  return (
    <LineageBox
      rows={rows ?? []} selfName={setName} noun="set" candidates={candidates}
      onEnd={(lineageId) => end.mutate({ lineageId })} onRemove={(id) => remove.mutate(id)}
      onAdd={(body) => add.mutateAsync(body)} adding={add.isPending}
    />
  )
}

/** An alliance's descent: the blocs it came out of, and those that came out of it.
 *  The rows arrive in the alliance detail payload. */
export function AllianceLineagePanel({ allianceId, allianceName, universeId, rows }: {
  allianceId: string
  allianceName: string
  universeId: string
  rows: AllianceLineageItem[]
}) {
  const end = useEndAllianceLineage(allianceId, universeId)
  const remove = useDeleteAllianceLineage(allianceId, universeId)
  const add = useAddAllianceLineage(allianceId, universeId)
  const { data: alliances } = useAlliances(universeId)
  const candidates = useMemo(
    () => (alliances?.items ?? []).filter((a) => a.id !== allianceId).map((a) => ({ id: a.id, name: a.name })).sort((a, b) => a.name.localeCompare(b.name)),
    [alliances, allianceId],
  )
  return (
    <LineageBox
      rows={rows} selfName={allianceName} noun="alliance" candidates={candidates}
      onEnd={(lineageId) => end.mutate({ lineageId })} onRemove={(id) => remove.mutate(id)}
      onAdd={(body) => add.mutateAsync(body)} adding={add.isPending}
    />
  )
}

function LineageBox({ rows, selfName, noun, onEnd, onRemove, candidates, onAdd, adding: addPending }: LineageOps) {
  const [adding, setAdding] = useState(false)
  const ancestors = rows.filter((r) => r.direction === 'parent')
  const descendants = rows.filter((r) => r.direction === 'child')

  function renderRow(r: Row) {
    const self = <span className="font-medium text-zinc-200">{selfName}</span>
    const other = (
      <Link
        from="/$universe" to={OTHER_ROUTE[noun]}
        params={{ id: r.other_slug ?? r.other_id }}
        className="font-medium text-zinc-200 hover:text-violet-400 transition-colors"
      >
        {r.other_name}
      </Link>
    )
    // direction 'parent': the other side is the parent, this one the child.
    const sentence = r.direction === 'parent'
      ? lineageSentence(r.kind, self, other)
      : lineageSentence(r.kind, other, self)
    return (
      <div
        key={r.id}
        className={`group flex items-center justify-between gap-2 rounded px-1.5 py-1 hover:bg-zinc-800/50 ${
          r.is_current ? '' : 'opacity-60'
        }`}
      >
        <div className="min-w-0">
          <p className="text-xs text-zinc-400">{sentence}</p>
          <p className="truncate text-[10px] text-zinc-500">
            {r.from_date && <> · from <FuzzyDate value={r.from_date as FuzzyDateValue} /></>}
            {!r.is_current && (
              <> · until {r.until_date ? <FuzzyDate value={r.until_date as FuzzyDateValue} /> : 'unknown'}</>
            )}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 pointer-fine:opacity-0">
          {r.is_current && (
            <button
              type="button"
              title="Record that this stopped applying, keeping it as history"
              onClick={() => onEnd(r.id)}
              className="rounded p-1 text-zinc-500 hover:text-amber-400"
            >
              <X className="h-3 w-3" />
            </button>
          )}
          <button
            type="button"
            title="Delete, for a row entered in error"
            onClick={() => onRemove(r.id)}
            className="rounded p-1 text-zinc-500 hover:text-red-400"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 text-sm font-semibold text-white">
          <ListTree className="h-3.5 w-3.5 text-zinc-400" />
          Lineage
        </h3>
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-violet-400 transition-colors"
        >
          <Plus className="h-3 w-3" />Add
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="text-xs text-zinc-400">No lineage recorded.</p>
      ) : (
        <div className="space-y-3">
          {ancestors.length > 0 && (
            <div>
              <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-sky-400">
                Came out of ({ancestors.length})
              </span>
              <div className="space-y-0.5">{ancestors.map(renderRow)}</div>
            </div>
          )}
          {descendants.length > 0 && (
            <div>
              <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-violet-400">
                Gave rise to ({descendants.length})
              </span>
              <div className="space-y-0.5">{descendants.map(renderRow)}</div>
            </div>
          )}
        </div>
      )}

      <AddLineageDialog
        selfName={selfName}
        noun={noun}
        candidates={candidates}
        onAdd={onAdd}
        pending={addPending}
        open={adding}
        onClose={() => setAdding(false)}
      />
    </div>
  )
}

function AddLineageDialog({ selfName, noun, candidates, onAdd, pending, open, onClose }: {
  selfName: string
  noun: Noun
  candidates: { id: string; name: string }[]
  onAdd: LineageOps['onAdd']
  pending: boolean
  open: boolean
  onClose: () => void
}) {
  const [otherId, setOtherId] = useState('')
  const [kind, setKind] = useState<SetLineageKind>('SPLINTERED_FROM')
  const [direction, setDirection] = useState<'parent' | 'child'>('parent')
  const [error, setError] = useState<string | null>(null)
  const otherName = candidates.find((s) => s.id === otherId)?.name ?? `the other ${noun}`
  const Noun = noun === 'set' ? 'Set' : 'Alliance'

  // The sentence the row will read as, shown before saving, because the
  // direction of a descent edge is the easy thing to get backwards.
  const sentence = direction === 'parent'
    ? lineageSentence(kind, selfName, otherName)
    : lineageSentence(kind, otherName, selfName)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!otherId) return
    setError(null)
    try {
      await onAdd({ other_id: otherId, kind, direction })
      setOtherId(''); setKind('SPLINTERED_FROM'); setDirection('parent')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add lineage')
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ListTree className="h-4 w-4 text-sky-400" />
            Add lineage
          </DialogTitle>
          <DialogDescription>
            Which {noun} came out of which. Separate from allies and enemies, so a {noun}
            can be recorded as both a splinter of another and at war with it.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">Direction</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDirection('parent')}
                className={`rounded-md border px-3 py-2 text-sm transition-colors ${
                  direction === 'parent'
                    ? 'border-sky-600 bg-sky-950/40 text-sky-300'
                    : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-300'
                }`}
              >
                {selfName} came out of it
              </button>
              <button
                type="button"
                onClick={() => setDirection('child')}
                className={`rounded-md border px-3 py-2 text-sm transition-colors ${
                  direction === 'child'
                    ? 'border-violet-600 bg-violet-950/40 text-violet-300'
                    : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-300'
                }`}
              >
                It came out of {selfName}
              </button>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">{Noun}</label>
            <AffiliationCombobox
              label={Noun}
              value={otherId}
              onChange={setOtherId}
              items={candidates}
              placeholder={`Select ${noun === 'set' ? 'a set' : 'an alliance'}…`}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">How</label>
            <Select value={kind} onValueChange={(v) => setKind(v as SetLineageKind)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {(Object.keys(LINEAGE_KIND_LABEL) as SetLineageKind[]).map((k) => (
                  <SelectItem key={k} value={k}>{LINEAGE_KIND_LABEL[k]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <p className="rounded border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-xs text-zinc-300">
            Will read: <span className="text-white">{sentence}</span>
          </p>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 justify-end">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={!otherId || pending}>
              {pending ? 'Adding…' : 'Add lineage'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
