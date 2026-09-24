import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { toast } from 'sonner'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useCreateAlliance, useGangs, useUpdateAlliance } from '@/lib/queries'
import type { AllianceRead, AllianceStatus } from '@/lib/types'
import { textParam } from '@/lib/searchParams'

export type AllianceSortKey = 'name' | 'status' | 'set_count' | 'member_count'

export interface AlliancesSearch {
  q?: string
  status?: AllianceStatus
  sort?: AllianceSortKey
  order?: 'asc' | 'desc'
}

const SORT_KEYS: AllianceSortKey[] = ['name', 'status', 'set_count', 'member_count']

// The page is in _app.alliances.index.lazy.tsx, its own chunk; this file keeps
// the URL schema and the form sheet, which the alliance page imports.
export const Route = createFileRoute('/_app/alliances/')({
  validateSearch: (s: Record<string, unknown>): AlliancesSearch => ({
    q: textParam(s.q),
    status: s.status === 'ACTIVE' || s.status === 'DORMANT' || s.status === 'EXTINCT' ? s.status : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as AllianceSortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
  }),
})

interface AllianceFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: AllianceRead
  onSaved?: (data: AllianceRead) => void
}

const ALLIANCE_GANG_NONE = '__none__'

/**
 * Seeded from props at mount and never resynced, so one mounted sheet reused
 * for a second alliance kept the first's values in any field the second leaves
 * empty - and saving wrote them. Keying on the target forces a fresh instance.
 * See SetFormSheet in routes/_app.sets.index.tsx for the full note.
 */
export function AllianceFormSheet(props: AllianceFormProps) {
  return <AllianceFormSheetInner key={props.initial?.id ?? 'new'} {...props} />
}

function AllianceFormSheetInner({ universeId, open, onClose, initial, onSaved }: AllianceFormProps) {
  const create = useCreateAlliance()
  const update = useUpdateAlliance(initial?.id ?? '', universeId)
  const { data: gangsData } = useGangs(universeId)
  const isEdit = !!initial

  const [name, setName] = useState(initial?.name ?? '')
  const [aliases, setAliases] = useState(initial?.aliases?.join(', ') ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [status, setStatus] = useState<AllianceStatus>(initial?.status ?? 'ACTIVE')
  const [gangId, setGangId] = useState<string>(initial?.gang_id ?? ALLIANCE_GANG_NONE)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const aliasList = aliases.split(',').map((s) => s.trim()).filter(Boolean)
    const body = {
      universe_id: universeId,
      name,
      aliases: aliasList.length > 0 ? aliasList : null,
      description: description || null,
      status,
      gang_id: gangId === ALLIANCE_GANG_NONE ? null : gangId,
    }
    try {
      if (isEdit) {
        const updated = await update.mutateAsync(body)
        onSaved?.(updated)
        toast.success(`Updated "${name}"`)
      } else {
        await create.mutateAsync(body)
        setName(''); setAliases(''); setDescription(''); setStatus('ACTIVE'); setGangId(ALLIANCE_GANG_NONE)
        toast.success(`Created "${name}"`)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} alliance`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Alliance' : 'Add Alliance'}
        description={isEdit ? 'Update this alliance' : 'Create a new gang alliance'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="a-name">Name *</Label>
            <Input id="a-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Alliance name" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="a-aliases">Aliases <span className="text-zinc-400">(comma-separated)</span></Label>
            <Input id="a-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. EastSide, ESC" />
          </div>
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as AllianceStatus)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="DORMANT">Dormant</SelectItem>
                <SelectItem value="EXTINCT">Extinct</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Gang</Label>
            <Select value={gangId} onValueChange={setGangId}>
              <SelectTrigger><SelectValue placeholder="No gang" /></SelectTrigger>
              <SelectContent>
                <SelectItem value={ALLIANCE_GANG_NONE}>No gang</SelectItem>
                {(gangsData?.items ?? []).map((g) => (
                  <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="a-desc">Description</Label>
            <Textarea id="a-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Overview…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Alliance'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}
