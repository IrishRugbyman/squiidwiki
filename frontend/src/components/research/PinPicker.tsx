import { Plus } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { formatFuzzyDate } from '@/components/FuzzyDate'
import { useDebounce } from '@/hooks/useDebounce'
import { PIN_ICON } from '@/lib/notePins'
import { useAllianceSearch, useIncidentSearch, useMemberSearch, useSetSearch } from '@/lib/queries'
import type { NotePin, PinRef, UUID } from '@/lib/types'

const CAP = 6

interface PinPickerProps {
  universeId: UUID
  /** Pins already on the note, hidden from the results. */
  pinned: NotePin[]
  onPick: (pin: PinRef) => void
}

/**
 * Add a pin: one search box over members, sets, incidents and alliances (the
 * same four search endpoints the command palette uses), in a dialog.
 */
export function PinPicker({ universeId, pinned, onPick }: PinPickerProps) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const dq = useDebounce(q.trim(), 250)

  const members = useMemberSearch(universeId, dq).data
  const sets = useSetSearch(universeId, dq).data
  const incidents = useIncidentSearch(universeId, dq).data
  const alliances = useAllianceSearch(universeId, dq).data

  const taken = new Set(pinned.map((p) => `${p.kind}-${p.id}`))
  const fresh = (kind: NotePin['kind'], id: string) => !taken.has(`${kind}-${id}`)

  const memberRows = (members ?? []).filter((m) => fresh('member', m.id)).slice(0, CAP)
  const setRows = (sets ?? []).filter((s) => fresh('set', s.id)).slice(0, CAP)
  const incidentRows = (incidents ?? []).filter((i) => fresh('incident', i.id)).slice(0, CAP)
  const allianceRows = (alliances ?? []).filter((a) => fresh('alliance', a.id)).slice(0, CAP)
  const searching = dq.length >= 2
  const any = memberRows.length + setRows.length + incidentRows.length + allianceRows.length > 0

  function close() {
    setOpen(false)
    setQ('')
  }

  function pick(pin: PinRef) {
    onPick(pin)
    close()
  }

  const MemberIcon = PIN_ICON.member
  const SetIcon = PIN_ICON.set
  const IncidentIcon = PIN_ICON.incident
  const AllianceIcon = PIN_ICON.alliance

  return (
    <>
      <Button type="button" size="sm" variant="outline" onClick={() => setOpen(true)}>
        <Plus className="mr-1.5 h-3.5 w-3.5" />Pin
      </Button>
      <Dialog open={open} onOpenChange={(v) => !v && close()}>
        <DialogContent className="overflow-hidden p-0">
          <DialogHeader className="px-4 pt-4">
            <DialogTitle>Pin to an entity</DialogTitle>
            <DialogDescription>Search members, sets, incidents and alliances.</DialogDescription>
          </DialogHeader>
          <Command shouldFilter={false}>
            <CommandInput placeholder="Search…" value={q} onValueChange={setQ} autoFocus />
            <CommandList>
              {searching && !any && <CommandEmpty>No results for "{dq}"</CommandEmpty>}
              {!searching && <p className="px-4 py-6 text-center text-xs text-zinc-400">Type at least two letters.</p>}

              {memberRows.length > 0 && (
                <CommandGroup heading="Members">
                  {memberRows.map((m) => (
                    <CommandItem
                      key={m.id}
                      value={`member-${m.id}`}
                      onSelect={() => pick({ kind: 'member', id: m.id })}
                    >
                      <MemberIcon className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                      <span className="truncate">{m.display_name}</span>
                      {m.primary_set_name && <span className="ml-2 truncate text-[10px] text-zinc-500">{m.primary_set_name}</span>}
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}

              {setRows.length > 0 && (
                <CommandGroup heading="Sets">
                  {setRows.map((s) => (
                    <CommandItem
                      key={s.id}
                      value={`set-${s.id}`}
                      onSelect={() => pick({ kind: 'set', id: s.id })}
                    >
                      <SetIcon className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                      <span className="truncate">{s.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}

              {incidentRows.length > 0 && (
                <CommandGroup heading="Incidents">
                  {incidentRows.map((i) => (
                    <CommandItem
                      key={i.id}
                      value={`incident-${i.id}`}
                      onSelect={() => pick({ kind: 'incident', id: i.id })}
                    >
                      <IncidentIcon className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                      <span className="truncate">{i.location_text ?? i.type}</span>
                      {formatFuzzyDate(i.date) && (
                        <span className="ml-2 shrink-0 text-[10px] text-zinc-500">{formatFuzzyDate(i.date)}</span>
                      )}
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}

              {allianceRows.length > 0 && (
                <CommandGroup heading="Alliances">
                  {allianceRows.map((a) => (
                    <CommandItem
                      key={a.id}
                      value={`alliance-${a.id}`}
                      onSelect={() => pick({ kind: 'alliance', id: a.id })}
                    >
                      <AllianceIcon className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                      <span className="truncate">{a.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </DialogContent>
      </Dialog>
    </>
  )
}
