import { Check, Network, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useAllSets, useReassignSetsToAlliance } from '@/lib/queries'

interface AddSetToAllianceDialogProps {
  allianceId: string
  allianceName: string
  universeId: string
  /** Set ids already attached to this alliance — merged with the user's selection
   *  to PATCH the alliance with the full new list (atomic pairwise FRIEND sync). */
  currentSetIds: string[]
  open: boolean
  onClose: () => void
  onCreateNew: () => void
}

export function AddSetToAllianceDialog({
  allianceId, allianceName, universeId, currentSetIds, open, onClose, onCreateNew,
}: AddSetToAllianceDialogProps) {
  const { data: allSets, isLoading } = useAllSets(universeId)
  const reassign = useReassignSetsToAlliance(allianceId, universeId)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const candidates = useMemo(
    () => (allSets?.items ?? []).filter((s) => s.alliance_id === null),
    [allSets],
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
    await reassign.mutateAsync({ currentSetIds, newSetIds: Array.from(selected) })
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
            <Network className="h-4 w-4 text-violet-400" />
            Add Set to {allianceName}
          </DialogTitle>
          <DialogDescription>
            Pick from sets not yet in an alliance, or create a new one.
          </DialogDescription>
        </DialogHeader>

        <div className="pt-2">
          <Button
            type="button"
            variant="outline"
            className="w-full justify-start"
            onClick={handleCreateNew}
          >
            <Plus className="mr-2 h-4 w-4" /> Create new set in this alliance
          </Button>
        </div>

        <div className="space-y-2 pt-2">
          <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
            Or pick existing ({candidates.length} available)
          </div>
          <div className="rounded-md border border-zinc-800">
            <Command>
              <CommandInput placeholder="Search unaffiliated sets…" />
              <CommandList className="max-h-[260px]">
                {isLoading ? (
                  <div className="py-6 text-center text-sm text-zinc-400">Loading…</div>
                ) : candidates.length === 0 ? (
                  <CommandEmpty>No unaffiliated sets in this universe.</CommandEmpty>
                ) : (
                  candidates.map((s) => {
                    const isSelected = selected.has(s.id)
                    return (
                      <CommandItem
                        key={s.id}
                        value={`${s.name} ${(s.name_variants ?? []).flatMap((v) => [v.name, v.initials, v.number]).filter(Boolean).join(' ')}`}
                        onSelect={() => toggle(s.id)}
                        className="flex items-center justify-between"
                      >
                        <span>{s.name}</span>
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
                : `Add ${selected.size} Set${selected.size === 1 ? '' : 's'}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
