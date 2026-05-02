import { Check, UserPlus, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useAllMembers, useReassignMembersToAlliance } from '@/lib/queries'

interface AddMemberToAllianceDialogProps {
  allianceId: string
  allianceName: string
  universeId: string
  open: boolean
  onClose: () => void
  onCreateNew: () => void
}

export function AddMemberToAllianceDialog({
  allianceId, allianceName, universeId, open, onClose, onCreateNew,
}: AddMemberToAllianceDialogProps) {
  const { data: allMembers, isLoading } = useAllMembers(universeId)
  const reassign = useReassignMembersToAlliance(allianceId, universeId)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const candidates = useMemo(
    () => (allMembers?.items ?? []).filter((m) => m.alliance_id === null),
    [allMembers],
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
    await reassign.mutateAsync(Array.from(selected))
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
            Add Member to {allianceName}
          </DialogTitle>
          <DialogDescription>
            Pick from members not yet in an alliance, or create a new one.
          </DialogDescription>
        </DialogHeader>

        <div className="pt-2">
          <Button
            type="button"
            variant="outline"
            className="w-full justify-start"
            onClick={handleCreateNew}
          >
            <UserPlus className="mr-2 h-4 w-4" /> Create new member in this alliance
          </Button>
        </div>

        <div className="space-y-2 pt-2">
          <div className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
            Or pick existing ({candidates.length} available)
          </div>
          <div className="rounded-md border border-zinc-800">
            <Command>
              <CommandInput placeholder="Search unaffiliated members…" />
              <CommandList className="max-h-[260px]">
                {isLoading ? (
                  <div className="py-6 text-center text-sm text-zinc-500">Loading…</div>
                ) : candidates.length === 0 ? (
                  <CommandEmpty>No unaffiliated members in this universe.</CommandEmpty>
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
            disabled={selected.size === 0 || reassign.isPending}
            onClick={handleSubmit}
          >
            {reassign.isPending
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
