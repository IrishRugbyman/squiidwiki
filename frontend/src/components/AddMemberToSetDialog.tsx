import { Check, UserPlus, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useAllMembers, useAddMembersToSet } from '@/lib/queries'
import { currentAffiliations } from '@/lib/utils'

interface AddMemberToSetDialogProps {
  setId: string
  setName: string
  universeId: string
  open: boolean
  onClose: () => void
  onCreateNew: () => void
}

export function AddMemberToSetDialog({
  setId, setName, universeId, open, onClose, onCreateNew,
}: AddMemberToSetDialogProps) {
  const { data: allMembers, isLoading } = useAllMembers(universeId)
  const addToSet = useAddMembersToSet(setId, universeId)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  // All members that aren't currently in this set (a former member can rejoin)
  const candidates = useMemo(
    () => (allMembers?.items ?? []).filter((m) => !currentAffiliations(m.affiliations).some((a) => a.set_id === setId)),
    [allMembers, setId],
  )

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function handleClose() {
    setSelected(new Set())
    onClose()
  }

  async function handleSubmit() {
    if (selected.size === 0) return
    const membersList = allMembers?.items ?? []
    await addToSet.mutateAsync(
      Array.from(selected).map((id) => {
        const m = membersList.find((x) => x.id === id)
        const existing = currentAffiliations(m?.affiliations)
        const isPrimary = existing.length === 0
        return {
          id,
          affiliations: [
            ...existing.map((a) => ({ set_id: a.set_id, rank: a.rank ?? null, is_primary: a.is_primary })),
            { set_id: setId, rank: null, is_primary: isPrimary },
          ],
        }
      }),
    )
    handleClose()
  }

  function handleCreateNew() {
    setSelected(new Set())
    onCreateNew()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-4 w-4 text-violet-400" />
            Add Member to {setName}
          </DialogTitle>
          <DialogDescription>
            Pick members to add to this set, or create a new one.
          </DialogDescription>
        </DialogHeader>

        <div className="pt-2">
          <Button
            type="button"
            variant="outline"
            className="w-full justify-start"
            onClick={handleCreateNew}
          >
            <UserPlus className="mr-2 h-4 w-4" /> Create new member in this set
          </Button>
        </div>

        <div className="space-y-2 pt-2">
          <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
            Or pick existing ({candidates.length} available)
          </div>
          <div className="rounded-md border border-zinc-800">
            <Command>
              <CommandInput placeholder="Search members…" />
              <CommandList className="max-h-[260px]">
                {isLoading ? (
                  <div className="py-6 text-center text-sm text-zinc-400">Loading…</div>
                ) : candidates.length === 0 ? (
                  <CommandEmpty>All members are already affiliated with this set.</CommandEmpty>
                ) : (
                  candidates.map((m) => {
                    const isSelected = selected.has(m.id)
                    return (
                      <CommandItem
                        key={m.id}
                        value={`${m.display_name} ${(m.aliases ?? []).join(' ')}`}
                        onSelect={() => toggle(m.id)}
                        className="flex items-center justify-between"
                      >
                        <span>{m.display_name}</span>
                        {isSelected && <Check className="h-4 w-4 text-violet-400" />}
                      </CommandItem>
                    )
                  })
                )}
              </CommandList>
            </Command>
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-4">
          <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
          <Button
            type="button"
            disabled={selected.size === 0 || addToSet.isPending}
            onClick={handleSubmit}
          >
            {addToSet.isPending
              ? 'Adding…'
              : selected.size === 0
                ? 'Add Selected'
                : `Add ${selected.size} Member${selected.size === 1 ? '' : 's'}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
