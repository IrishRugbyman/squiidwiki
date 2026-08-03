import { Heart, UserPlus } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useDebounce } from '@/hooks/useDebounce'
import { useMemberSearch, useUpdateMember } from '@/lib/queries'
import {
  FAMILY_ROLES, ROLE_LABEL, familyDictToEntries, familyEntriesToDict,
  type FamilyRole,
} from '@/routes/_app.members.index'
import type { MemberRead, UUID } from '@/lib/types'

interface PendingRelative {
  member_id: UUID
  member_name: string
  role: FamilyRole
}

interface AddFamilyRelativeDialogProps {
  member: MemberRead
  universeId: string
  open: boolean
  onClose: () => void
}

export function AddFamilyRelativeDialog({
  member, universeId, open, onClose,
}: AddFamilyRelativeDialogProps) {
  const update = useUpdateMember(member.id, universeId)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<FamilyRole>('brother')
  const [pending, setPending] = useState<PendingRelative[]>([])
  const debouncedSearch = useDebounce(search, 200)
  const { data: results } = useMemberSearch(universeId, debouncedSearch)

  const existingEntries = familyDictToEntries(member.family as Record<string, unknown> | null)
  const existingPairs = new Set(existingEntries.map((e) => `${e.memberId}:${e.role}`))
  const existingMemberIds = new Set(existingEntries.map((e) => e.memberId))
  const pendingPairs = new Set(pending.map((p) => `${p.member_id}:${p.role}`))
  const pendingMemberIds = new Set(pending.map((p) => p.member_id))

  const hasFather =
    existingEntries.some((e) => e.role === 'father') ||
    pending.some((p) => p.role === 'father')

  function addPending(memberId: UUID, memberName: string) {
    if (memberId === member.id) return
    const pairKey = `${memberId}:${role}`
    if (existingPairs.has(pairKey) || pendingPairs.has(pairKey)) return
    if (role === 'father' && hasFather) return
    setPending((prev) => [...prev, { member_id: memberId, member_name: memberName, role }])
    setSearch('')
  }

  function removePending(memberId: UUID, removedRole: FamilyRole) {
    setPending((prev) => prev.filter((p) => !(p.member_id === memberId && p.role === removedRole)))
  }

  function reset() {
    setSearch('')
    setPending([])
    setRole('brother')
  }

  function handleClose() {
    reset()
    onClose()
  }

  async function handleSubmit() {
    if (pending.length === 0) return
    const mergedEntries = [
      ...existingEntries,
      ...pending.map((p) => ({ role: p.role, memberId: p.member_id })),
    ]
    const mergedDict = familyEntriesToDict(mergedEntries)
    await update.mutateAsync({ family: mergedDict })
    handleClose()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Heart className="h-4 w-4 text-violet-400" />
            Add Family Member
          </DialogTitle>
          <DialogDescription>
            Pick a role and search for the relative. The reverse link is written automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-1 pt-2">
          <Label>Role</Label>
          <Select value={role} onValueChange={(v) => setRole(v as FamilyRole)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {FAMILY_ROLES.map((r) => {
                const disabled = r === 'father' && hasFather
                return (
                  <SelectItem key={r} value={r} disabled={disabled}>
                    {ROLE_LABEL[r]}{disabled ? ' (already set)' : ''}
                  </SelectItem>
                )
              })}
            </SelectContent>
          </Select>
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
                  const isSelf = m.id === member.id
                  const samePair = existingPairs.has(`${m.id}:${role}`) || pendingPairs.has(`${m.id}:${role}`)
                  const fatherBlock = role === 'father' && hasFather
                  const disabled = isSelf || samePair || fatherBlock
                  const note = isSelf
                    ? '(self)'
                    : samePair
                      ? `already ${ROLE_LABEL[role].toLowerCase()}`
                      : existingMemberIds.has(m.id) || pendingMemberIds.has(m.id)
                        ? '(other relation)'
                        : ''
                  return (
                    <button
                      key={m.id}
                      type="button"
                      disabled={disabled}
                      onClick={() => addPending(m.id, m.display_name)}
                      className="w-full px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:cursor-not-allowed flex items-center justify-between gap-3"
                    >
                      <span className="truncate">{m.display_name}</span>
                      {note && <span className="text-xs text-zinc-400 shrink-0">{note}</span>}
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
            {pending.map((p) => (
              <div
                key={`${p.member_id}:${p.role}`}
                className="flex items-center justify-between rounded border border-zinc-800 px-3 py-1.5 text-sm"
              >
                <span className="text-zinc-200">{p.member_name}</span>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    <UserPlus className="mr-1 h-3 w-3" />
                    {ROLE_LABEL[p.role]}
                  </Badge>
                  <button
                    type="button"
                    onClick={() => removePending(p.member_id, p.role)}
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
                ? 'Add Relatives'
                : `Add ${pending.length} Relative${pending.length === 1 ? '' : 's'}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
