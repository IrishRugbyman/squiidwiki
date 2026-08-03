import { FilePlus, Library } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { useDebounce } from '@/hooks/useDebounce'
import { useSourceSearch, useUpdateIncident } from '@/lib/queries'
import type { IncidentReadDetail, SourceListItem, UUID } from '@/lib/types'

interface AddSourceToIncidentDialogProps {
  incident: IncidentReadDetail
  universeId: string
  open: boolean
  onClose: () => void
  onCreateNew: () => void
}

export function AddSourceToIncidentDialog({
  incident, universeId, open, onClose, onCreateNew,
}: AddSourceToIncidentDialogProps) {
  const update = useUpdateIncident(incident.id, universeId)
  const [search, setSearch] = useState('')
  const [pending, setPending] = useState<SourceListItem[]>([])
  const debouncedSearch = useDebounce(search, 200)
  const { data: results } = useSourceSearch(universeId, debouncedSearch)

  const existingIds = new Set(incident.source_ids)
  const pendingIds = new Set(pending.map((s) => s.id))

  function addPending(source: SourceListItem) {
    if (existingIds.has(source.id) || pendingIds.has(source.id)) return
    setPending((prev) => [...prev, source])
    setSearch('')
  }

  function removePending(id: UUID) {
    setPending((prev) => prev.filter((s) => s.id !== id))
  }

  function reset() {
    setSearch('')
    setPending([])
  }

  function handleClose() {
    reset()
    onClose()
  }

  function handleCreateNew() {
    reset()
    onCreateNew()
  }

  async function handleSubmit() {
    if (pending.length === 0) return
    const merged = [...incident.source_ids, ...pending.map((s) => s.id)]
    await update.mutateAsync({ source_ids: merged })
    handleClose()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Library className="h-4 w-4 text-violet-400" />
            Attach Source
          </DialogTitle>
          <DialogDescription>
            Search existing sources to attach, or create a new one.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2 pt-2">
          <Input
            placeholder="Search sources by title…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search.length >= 2 && results && (
            <div className="max-h-48 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
              {results.length === 0 ? (
                <div className="px-3 py-2 text-sm text-zinc-400">No matching sources.</div>
              ) : (
                results.map((s) => {
                  const already = existingIds.has(s.id) || pendingIds.has(s.id)
                  return (
                    <button
                      key={s.id}
                      type="button"
                      disabled={already}
                      onClick={() => addPending(s)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:cursor-not-allowed flex items-center justify-between gap-3"
                    >
                      <span className="truncate text-zinc-300">{s.title}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        <ReliabilityBadge reliability={s.reliability} />
                        {already && <span className="text-xs text-zinc-400">already added</span>}
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          )}
        </div>

        <div className="pt-2">
          <Button
            type="button"
            variant="outline"
            className="w-full justify-start"
            onClick={handleCreateNew}
          >
            <FilePlus className="mr-2 h-4 w-4" /> Create new source
          </Button>
        </div>

        {pending.length > 0 && (
          <div className="space-y-1.5 pt-2">
            <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Staged ({pending.length})
            </div>
            {pending.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded border border-zinc-800 px-3 py-1.5 text-sm gap-3"
              >
                <span className="truncate text-zinc-200">{s.title}</span>
                <div className="flex items-center gap-2 shrink-0">
                  <ReliabilityBadge reliability={s.reliability} />
                  <button
                    type="button"
                    onClick={() => removePending(s.id)}
                    className="text-zinc-400 hover:text-red-400 transition-colors text-xs"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2 justify-end pt-4">
          <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
          <Button
            type="button"
            disabled={pending.length === 0 || update.isPending}
            onClick={handleSubmit}
          >
            {update.isPending
              ? 'Attaching…'
              : pending.length === 0
                ? 'Attach Sources'
                : `Attach ${pending.length} Source${pending.length === 1 ? '' : 's'}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
