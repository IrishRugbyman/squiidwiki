import { Link2 } from 'lucide-react'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { useDebounce } from '@/hooks/useDebounce'
import { useMemberSearch } from '@/lib/queries'
import { api } from '@/lib/api'
import type { MemberListItem, MemberReadDetail, UUID } from '@/lib/types'

interface AttachMembersToSourceDialogProps {
  sourceId: UUID
  universeId: string
  attachedMemberIds: UUID[]
  open: boolean
  onClose: () => void
}

export function AttachMembersToSourceDialog({
  sourceId, universeId, attachedMemberIds, open, onClose,
}: AttachMembersToSourceDialogProps) {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [pending, setPending] = useState<MemberListItem[]>([])
  const [submitting, setSubmitting] = useState(false)
  const debouncedSearch = useDebounce(search, 200)
  const { data: results } = useMemberSearch(universeId, debouncedSearch)

  const attachedIds = new Set(attachedMemberIds)
  const pendingIds = new Set(pending.map((m) => m.id))

  function addPending(m: MemberListItem) {
    if (attachedIds.has(m.id) || pendingIds.has(m.id)) return
    setPending((prev) => [...prev, m])
    setSearch('')
  }

  function removePending(id: UUID) {
    setPending((prev) => prev.filter((m) => m.id !== id))
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
      await Promise.all(pending.map(async (m) => {
        const detail = await api.get<MemberReadDetail>(`/members/${m.id}?universe_id=${universeId}`)
        if (detail.source_ids.includes(sourceId)) return
        const merged = [...detail.source_ids, sourceId]
        await api.patch<MemberReadDetail>(`/members/${m.id}?universe_id=${universeId}`, { source_ids: merged })
      }))
      qc.invalidateQueries({ queryKey: ['members'] })
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
            Attach to Members
          </DialogTitle>
          <DialogDescription>
            Search members to cite this source on their profile.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2 pt-2">
          <Input
            placeholder="Search members…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search.length >= 2 && results && (
            <div className="max-h-48 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
              {results.length === 0 ? (
                <div className="px-3 py-2 text-sm text-zinc-500">No matching members.</div>
              ) : (
                results.map((m) => {
                  const already = attachedIds.has(m.id) || pendingIds.has(m.id)
                  return (
                    <button
                      key={m.id}
                      type="button"
                      disabled={already}
                      onClick={() => addPending(m)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:cursor-not-allowed flex items-center justify-between gap-3"
                    >
                      <span className="truncate text-zinc-300">{m.display_name}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        <MemberStatusBadge status={m.status} />
                        {already && <span className="text-xs text-zinc-500">already cited</span>}
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          )}
        </div>

        {pending.length > 0 && (
          <div className="space-y-1.5 pt-2">
            <div className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
              Staged ({pending.length})
            </div>
            {pending.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded border border-zinc-800 px-3 py-1.5 text-sm gap-3"
              >
                <span className="truncate text-zinc-200">{m.display_name}</span>
                <div className="flex items-center gap-2 shrink-0">
                  <MemberStatusBadge status={m.status} />
                  <button
                    type="button"
                    onClick={() => removePending(m.id)}
                    className="text-zinc-600 hover:text-red-400 transition-colors text-xs"
                  >
                    ✕
                  </button>
                </div>
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
                ? 'Attach Members'
                : `Attach ${pending.length} Member${pending.length === 1 ? '' : 's'}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
