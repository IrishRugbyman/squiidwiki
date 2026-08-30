import { Link } from '@tanstack/react-router'
import { ListTree, Plus, Trash2, X } from 'lucide-react'
import { useState } from 'react'

import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
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
  useAddSetLineage,
  useAllSets,
  useDeleteSetLineage,
  useEndSetLineage,
  useSetLineage,
} from '@/lib/queries'
import type { SetLineageItem, SetLineageKind } from '@/lib/types'

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

/** Every kind is stored as "child KIND parent", so the parent side reads inverted. */
const LINEAGE_KIND_INVERSE: Record<SetLineageKind, string> = {
  SPLINTERED_FROM: 'splintered off',
  RENAMED_FROM: 'renamed to',
  MERGED_FROM: 'merged into',
  YOUNGER_GENERATION_OF: 'older generation of',
}

export function LineagePanel({ setId, setName, universeId }: {
  setId: string
  setName: string
  universeId: string
}) {
  const { data: rows } = useSetLineage(setId, universeId)
  const endLink = useEndSetLineage(setId, universeId)
  const removeLink = useDeleteSetLineage(setId, universeId)
  const [adding, setAdding] = useState(false)

  const items = rows ?? []
  const ancestors = items.filter((r) => r.direction === 'parent')
  const descendants = items.filter((r) => r.direction === 'child')

  function renderRow(r: SetLineageItem) {
    const verb = r.direction === 'parent'
      ? LINEAGE_KIND_LABEL[r.kind]
      : LINEAGE_KIND_INVERSE[r.kind]
    return (
      <div
        key={r.id}
        className={`group flex items-center justify-between gap-2 rounded px-1.5 py-1 hover:bg-zinc-800/50 ${
          r.is_current ? '' : 'opacity-60'
        }`}
      >
        <div className="min-w-0">
          <Link
            to="/sets/$id"
            params={{ id: r.other_slug ?? r.other_id }}
            className="block truncate text-xs text-zinc-200 hover:text-violet-400 transition-colors"
          >
            {r.other_name}
          </Link>
          <p className="truncate text-[10px] text-zinc-500">
            {verb}
            {r.from_date && <> · from <FuzzyDate value={r.from_date as FuzzyDateValue} /></>}
            {!r.is_current && (
              <> · until {r.until_date ? <FuzzyDate value={r.until_date as FuzzyDateValue} /> : 'unknown'}</>
            )}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          {r.is_current && (
            <button
              type="button"
              title="Record that this stopped applying, keeping it as history"
              onClick={() => endLink.mutate({ lineageId: r.id })}
              className="rounded p-1 text-zinc-500 hover:text-amber-400"
            >
              <X className="h-3 w-3" />
            </button>
          )}
          <button
            type="button"
            title="Delete, for a row entered in error"
            onClick={() => removeLink.mutate(r.id)}
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

      {items.length === 0 ? (
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
        setId={setId}
        setName={setName}
        universeId={universeId}
        open={adding}
        onClose={() => setAdding(false)}
      />
    </div>
  )
}

function AddLineageDialog({ setId, setName, universeId, open, onClose }: {
  setId: string
  setName: string
  universeId: string
  open: boolean
  onClose: () => void
}) {
  const { data: allSets } = useAllSets(universeId)
  const add = useAddSetLineage(setId, universeId)
  const [otherId, setOtherId] = useState('')
  const [kind, setKind] = useState<SetLineageKind>('SPLINTERED_FROM')
  const [direction, setDirection] = useState<'parent' | 'child'>('parent')
  const [error, setError] = useState<string | null>(null)

  const available = (allSets?.items ?? []).filter((s) => s.id !== setId)
  const otherName = available.find((s) => s.id === otherId)?.name ?? 'the other set'

  // The sentence the row will read as, shown before saving, because the
  // direction of a descent edge is the easy thing to get backwards.
  const sentence = direction === 'parent'
    ? `${setName} ${LINEAGE_KIND_LABEL[kind]} ${otherName}`
    : `${otherName} ${LINEAGE_KIND_LABEL[kind]} ${setName}`

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!otherId) return
    setError(null)
    try {
      await add.mutateAsync({ other_id: otherId, kind, direction })
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
            Which set came out of which. Separate from allies and enemies, so a set
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
                {setName} came out of it
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
                It came out of {setName}
              </button>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-300">Set</label>
            <Select value={otherId} onValueChange={setOtherId}>
              <SelectTrigger><SelectValue placeholder="Select a set…" /></SelectTrigger>
              <SelectContent>
                {available.length === 0 ? (
                  <div className="px-2 py-4 text-center text-xs text-zinc-400">No available sets to link.</div>
                ) : (
                  available.map((s) => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
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
            <Button type="submit" disabled={!otherId || add.isPending}>
              {add.isPending ? 'Adding…' : 'Add lineage'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
