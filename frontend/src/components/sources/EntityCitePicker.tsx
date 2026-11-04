import { Link2, Search, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { formatFuzzyDate } from '@/components/FuzzyDate'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useDebounce } from '@/hooks/useDebounce'
import {
  useAllianceSearch, useBatchCitations, useCourtCaseSearch, useIncidentSearch, useMemberSearch, useSetSearch,
} from '@/lib/queries'
import { LOOKUP_LABEL } from '@/lib/sourceMeta'
import type { CitableType, LookupSystem, UUID } from '@/lib/types'
import { cn } from '@/lib/utils'

type Pickable = Exclude<CitableType, 'municipality' | 'business'>
interface Hit { type: Pickable; id: UUID; label: string; detail: string | null }

const TABS: { type: Pickable; label: string }[] = [
  { type: 'member', label: 'Members' },
  { type: 'incident', label: 'Incidents' },
  { type: 'set', label: 'Sets' },
  { type: 'alliance', label: 'Alliances' },
  { type: 'court_case', label: 'Cases' },
]

function useHits(type: Pickable, universeId: UUID, q: string): Hit[] {
  const m = useMemberSearch(type === 'member' ? universeId : null, q)
  const i = useIncidentSearch(type === 'incident' ? universeId : null, q)
  const s = useSetSearch(type === 'set' ? universeId : null, q)
  const a = useAllianceSearch(type === 'alliance' ? universeId : null, q)
  const c = useCourtCaseSearch(type === 'court_case' ? universeId : null, q)
  switch (type) {
    case 'member':
      return (m.data ?? []).map((x) => ({ type, id: x.id, label: x.display_name, detail: x.primary_set_name }))
    case 'incident':
      return (i.data ?? []).map((x) => ({
        type, id: x.id, label: x.location_text || x.type, detail: [x.type, formatFuzzyDate(x.date)].filter(Boolean).join(' · '),
      }))
    case 'set':
      return (s.data ?? []).map((x) => ({ type, id: x.id, label: x.name, detail: null }))
    case 'alliance':
      return (a.data ?? []).map((x) => ({ type, id: x.id, label: x.name, detail: null }))
    case 'court_case':
      return (c.data ?? []).map((x) => ({ type, id: x.id, label: x.name, detail: x.docket ?? null }))
    default:
      return []
  }
}

/**
 * Cite one source on many records, from the source's page: stage members,
 * incidents, sets, alliances or cases, each with its own locator, and cite
 * them in one call that lands whole or not at all.
 */
export function EntityCitePicker({ universeId, sourceId, lookupSystem, open, onClose }: {
  universeId: UUID
  sourceId: UUID
  lookupSystem: LookupSystem | null
  open: boolean
  onClose: () => void
}) {
  const [tab, setTab] = useState<Pickable>('member')
  const [q, setQ] = useState('')
  const debounced = useDebounce(q.trim(), 200)
  const hits = useHits(tab, universeId, debounced.length >= 2 ? debounced : '')
  const [staged, setStaged] = useState<(Hit & { locator: string })[]>([])
  const batch = useBatchCitations(universeId)
  const stagedKeys = new Set(staged.map((h) => `${h.type}:${h.id}`))

  function close() {
    setStaged([]); setQ(''); onClose()
  }

  async function submit() {
    const r = await batch.mutateAsync({
      items: staged.map((h) => ({
        source_id: sourceId, entity_type: h.type, entity_id: h.id, locator: h.locator.trim() || null,
      })),
      on_conflict: 'update',
    })
    const parts = [
      r.created.length && `${r.created.length} cited`,
      r.updated.length && `${r.updated.length} updated`,
      r.skipped.length && `${r.skipped.length} already cited`,
    ].filter(Boolean)
    toast.success(parts.join(', '))
    close()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && close()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Link2 className="h-4 w-4 text-violet-400" /> Cite on records</DialogTitle>
          <DialogDescription>Find the records this source backs; stage as many as you like.</DialogDescription>
        </DialogHeader>
        <div className="flex gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-1">
          {TABS.map((t) => (
            <button key={t.type} type="button" onClick={() => setTab(t.type)}
              className={cn('flex-1 rounded-md px-2 py-1 text-xs', tab === t.type ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-200')}>
              {t.label}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
          <Input autoFocus className="pl-8" placeholder={`Search ${TABS.find((t) => t.type === tab)?.label.toLowerCase()}…`}
            value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        {debounced.length >= 2 && (
          <div className="max-h-56 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950">
            {hits.length === 0 ? <p className="px-3 py-3 text-sm text-zinc-500">No match.</p> : hits.map((h) => {
              const on = stagedKeys.has(`${h.type}:${h.id}`)
              return (
                <button key={h.id} type="button" disabled={on}
                  onClick={() => setStaged((s) => [...s, { ...h, locator: '' }])}
                  className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-zinc-800/70 disabled:opacity-40">
                  <span className="min-w-0 truncate text-zinc-200">{h.label}</span>
                  <span className="shrink-0 truncate text-xs text-zinc-500">{on ? 'staged' : h.detail}</span>
                </button>
              )
            })}
          </div>
        )}
        {staged.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-xs font-medium uppercase tracking-wider text-zinc-400">Staged ({staged.length})</div>
            {staged.map((h, n) => (
              <div key={`${h.type}:${h.id}`} className="flex items-center gap-2 rounded border border-zinc-800 px-2 py-1.5">
                <span className="w-16 shrink-0 text-[11px] uppercase text-zinc-500">{h.type.replace('_', ' ')}</span>
                <span className="min-w-0 flex-1 truncate text-sm text-zinc-200">{h.label}</span>
                <Input
                  className="h-7 w-36 text-xs"
                  placeholder={lookupSystem ? `${LOOKUP_LABEL[lookupSystem]} no.` : 'p. 12'}
                  value={h.locator}
                  onChange={(e) => setStaged((s) => s.map((x, i) => (i === n ? { ...x, locator: e.target.value } : x)))}
                />
                <button type="button" aria-label={`Unstage ${h.label}`} className="rounded p-1 text-zinc-500 hover:text-red-400"
                  onClick={() => setStaged((s) => s.filter((_, i) => i !== n))}>
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={close}>Cancel</Button>
          <Button disabled={staged.length === 0 || batch.isPending} onClick={submit}>
            {batch.isPending ? 'Citing…' : staged.length ? `Cite on ${staged.length}` : 'Cite'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
