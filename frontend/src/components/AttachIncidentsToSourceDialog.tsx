import { Link2 } from 'lucide-react'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FuzzyDate } from '@/components/FuzzyDate'
import { useDebounce } from '@/hooks/useDebounce'
import { useIncidentSearch } from '@/lib/queries'
import { api } from '@/lib/api'
import type { IncidentListItem, IncidentReadDetail, UUID } from '@/lib/types'

interface AttachIncidentsToSourceDialogProps {
  sourceId: UUID
  universeId: string
  attachedIncidentIds: UUID[]
  open: boolean
  onClose: () => void
}

export function AttachIncidentsToSourceDialog({
  sourceId, universeId, attachedIncidentIds, open, onClose,
}: AttachIncidentsToSourceDialogProps) {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [pending, setPending] = useState<IncidentListItem[]>([])
  const [submitting, setSubmitting] = useState(false)
  const debouncedSearch = useDebounce(search, 200)
  const { data: results } = useIncidentSearch(universeId, debouncedSearch)

  const attachedIds = new Set(attachedIncidentIds)
  const pendingIds = new Set(pending.map((i) => i.id))

  function addPending(inc: IncidentListItem) {
    if (attachedIds.has(inc.id) || pendingIds.has(inc.id)) return
    setPending((prev) => [...prev, inc])
    setSearch('')
  }

  function removePending(id: UUID) {
    setPending((prev) => prev.filter((i) => i.id !== id))
  }

  function reset() {
    setSearch('')
    setPending([])
  }

  function handleClose() {
    if (submitting) return
    reset()
    onClose()
  }

  async function handleSubmit() {
    if (pending.length === 0) return
    setSubmitting(true)
    try {
      await Promise.all(pending.map(async (inc) => {
        const detail = await api.get<IncidentReadDetail>(`/incidents/${inc.id}?universe_id=${universeId}`)
        if (detail.source_ids.includes(sourceId)) return
        const merged = [...detail.source_ids, sourceId]
        await api.patch<IncidentReadDetail>(`/incidents/${inc.id}?universe_id=${universeId}`, { source_ids: merged })
      }))
      qc.invalidateQueries({ queryKey: ['incidents'] })
      reset()
      onClose()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Link2 className="h-4 w-4 text-violet-400" />
            Attach to Incidents
          </DialogTitle>
          <DialogDescription>
            Search incidents to cite this source. Selected incidents will be updated to include this source.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2 pt-2">
          <Input
            placeholder="Search incidents…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search.length >= 2 && results && (
            <div className="max-h-48 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
              {results.length === 0 ? (
                <div className="px-3 py-2 text-sm text-zinc-400">No matching incidents.</div>
              ) : (
                results.map((inc) => {
                  const already = attachedIds.has(inc.id) || pendingIds.has(inc.id)
                  return (
                    <button
                      key={inc.id}
                      type="button"
                      disabled={already}
                      onClick={() => addPending(inc)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:cursor-not-allowed flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <Badge
                          variant="outline"
                          className={`text-xs shrink-0 ${inc.type === 'MURDER' ? 'border-rose-800 text-rose-400' : inc.type === 'FIGHT' ? 'border-violet-800 text-violet-400' : 'border-amber-800 text-amber-400'}`}
                        >
                          {inc.type}
                        </Badge>
                        <span className="truncate text-zinc-300">
                          <FuzzyDate value={inc.date} fallback="Unknown date" />
                          {inc.victim_names.length > 0 && (
                            <span className="text-zinc-400">: {inc.victim_names.slice(0, 2).join(', ')}{inc.victim_names.length > 2 ? ` +${inc.victim_names.length - 2}` : ''}</span>
                          )}
                        </span>
                      </div>
                      {already && <span className="text-xs text-zinc-400 shrink-0">already cited</span>}
                    </button>
                  )
                })
              )}
            </div>
          )}
        </div>

        {pending.length > 0 && (
          <div className="space-y-1.5 pt-2">
            <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Staged ({pending.length})
            </div>
            {pending.map((inc) => (
              <div
                key={inc.id}
                className="flex items-center justify-between rounded border border-zinc-800 px-3 py-1.5 text-sm gap-3"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Badge
                    variant="outline"
                    className={`text-xs shrink-0 ${inc.type === 'MURDER' ? 'border-rose-800 text-rose-400' : inc.type === 'FIGHT' ? 'border-violet-800 text-violet-400' : 'border-amber-800 text-amber-400'}`}
                  >
                    {inc.type}
                  </Badge>
                  <span className="truncate text-zinc-200">
                    <FuzzyDate value={inc.date} fallback="Unknown date" />
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => removePending(inc.id)}
                  className="text-zinc-400 hover:text-red-400 transition-colors text-xs"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2 justify-end pt-4">
          <Button type="button" variant="outline" onClick={handleClose} disabled={submitting}>Cancel</Button>
          <Button
            type="button"
            disabled={pending.length === 0 || submitting}
            onClick={handleSubmit}
          >
            {submitting
              ? 'Attaching…'
              : pending.length === 0
                ? 'Attach Incidents'
                : `Attach ${pending.length} Incident${pending.length === 1 ? '' : 's'}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
