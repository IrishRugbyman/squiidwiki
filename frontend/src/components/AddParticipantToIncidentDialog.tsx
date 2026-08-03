import { UserPlus, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useDebounce } from '@/hooks/useDebounce'
import { useAllSets, useMemberSearch, useUpdateIncident } from '@/lib/queries'
import type { IncidentReadDetail, ParticipantOutcome, ParticipantRole, UUID } from '@/lib/types'

interface PendingParticipant {
  member_id: UUID
  member_name: string
  set_name?: string
  role: ParticipantRole
  outcome: ParticipantOutcome
}

interface AddParticipantToIncidentDialogProps {
  incident: IncidentReadDetail
  universeId: string
  open: boolean
  onClose: () => void
  onCreateNew: () => void
}

export function AddParticipantToIncidentDialog({
  incident, universeId, open, onClose, onCreateNew,
}: AddParticipantToIncidentDialogProps) {
  const update = useUpdateIncident(incident.id, universeId)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<ParticipantRole>('VICTIM')
  const [outcome, setOutcome] = useState<ParticipantOutcome>('UNKNOWN')
  const [pending, setPending] = useState<PendingParticipant[]>([])
  const debouncedSearch = useDebounce(search, 200)
  const { data: results } = useMemberSearch(universeId, debouncedSearch)
  const { data: setsPage } = useAllSets(universeId)
  const setNameById = useMemo(() => {
    const out: Record<string, string> = {}
    for (const s of setsPage?.items ?? []) out[s.id] = s.name
    return out
  }, [setsPage])

  const existingIds = new Set(incident.participants.map((p) => p.member_id))
  const pendingIds = new Set(pending.map((p) => p.member_id))

  function addPending(memberId: UUID, memberName: string, setId?: string | null) {
    if (existingIds.has(memberId) || pendingIds.has(memberId)) return
    const setName = setId ? setNameById[setId] : undefined
    setPending((prev) => [...prev, { member_id: memberId, member_name: memberName, set_name: setName, role, outcome }])
    setSearch('')
  }

  function removePending(memberId: UUID) {
    setPending((prev) => prev.filter((p) => p.member_id !== memberId))
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
    const merged = [
      ...incident.participants.map((p) => ({
        member_id: p.member_id,
        role: p.role,
        outcome: p.outcome,
        notes: p.notes,
      })),
      ...pending.map((p) => ({
        member_id: p.member_id,
        role: p.role,
        outcome: p.outcome,
      })),
    ]
    await update.mutateAsync({ participants: merged })
    handleClose()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-4 w-4 text-violet-400" />
            Add Participant
          </DialogTitle>
          <DialogDescription>
            Pick a role and outcome, then search for the member to add. Repeat to stage multiple.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-2 pt-2">
          <div className="space-y-1">
            <Label>Role</Label>
            <Select value={role} onValueChange={(v) => setRole(v as ParticipantRole)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {(['SHOOTER', 'ASSISTED', 'BYSTANDER', 'VICTIM'] as ParticipantRole[]).map((r) => (
                  <SelectItem key={r} value={r}>{r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>Outcome</Label>
            <Select value={outcome} onValueChange={(v) => setOutcome(v as ParticipantOutcome)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {(['KILLED', 'INJURED', 'UNHARMED', 'UNKNOWN'] as ParticipantOutcome[]).map((o) => (
                  <SelectItem key={o} value={o}>{o}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Input
            placeholder="Search member to add…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search.length >= 2 && results && (
            <div className="max-h-40 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
              {results.length === 0 ? (
                <div className="px-3 py-2 text-sm text-zinc-400">No matching members.</div>
              ) : (
                results.map((m) => {
                  const already = existingIds.has(m.id) || pendingIds.has(m.id)
                  return (
                    <button
                      key={m.id}
                      type="button"
                      disabled={already}
                      onClick={() => { const pa = m.affiliations.find((a) => a.is_primary) ?? m.affiliations[0]; addPending(m.id, m.display_name, pa?.set_id) }}
                      className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:cursor-not-allowed flex items-center justify-between gap-2"
                    >
                      <span className="truncate">{m.display_name}</span>
                      <span className="flex items-center gap-2 shrink-0">
                        {m.primary_set_name && (
                          <span className="text-[10px] text-zinc-400 truncate max-w-[120px]">{m.primary_set_name}</span>
                        )}
                        {already && <span className="text-xs text-zinc-400">already added</span>}
                      </span>
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
            <UserPlus className="mr-2 h-4 w-4" /> Create new member
          </Button>
        </div>

        {pending.length > 0 && (
          <div className="space-y-1.5 pt-2">
            <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Staged ({pending.length})
            </div>
            {pending.map((p) => (
              <div
                key={p.member_id}
                className="flex items-center justify-between rounded border border-zinc-800 px-3 py-1.5 text-sm gap-2"
              >
                <span className="min-w-0 flex items-baseline gap-1.5 truncate">
                  <span className="text-zinc-200 truncate">{p.member_name}</span>
                  {p.set_name && (
                    <span className="text-[10px] text-zinc-400 truncate">· {p.set_name}</span>
                  )}
                </span>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">{p.role}</Badge>
                  <Badge variant="outline" className="text-xs">{p.outcome}</Badge>
                  <button
                    type="button"
                    onClick={() => removePending(p.member_id)}
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
              ? 'Adding…'
              : pending.length === 0
                ? 'Add Participants'
                : `Add ${pending.length} Participant${pending.length === 1 ? '' : 's'}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
