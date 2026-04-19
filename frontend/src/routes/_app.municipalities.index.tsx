import { createFileRoute, Link } from '@tanstack/react-router'
import { MapPin, Plus } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useCreateMunicipality, useUpdateMunicipality, useMunicipalities } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import type { MunicipalityRead } from '@/lib/types'

export const Route = createFileRoute('/_app/municipalities/')({
  component: MunicipalitiesPage,
})

interface MunicipalityFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: MunicipalityRead
  allMunicipalities?: MunicipalityRead[]
}

export function MunicipalityFormSheet({ universeId, open, onClose, initial, allMunicipalities }: MunicipalityFormProps) {
  const create = useCreateMunicipality()
  const update = useUpdateMunicipality(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const [name, setName] = useState(initial?.name ?? '')
  const [parentId, setParentId] = useState<string>(initial?.parent_id ?? '')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const body = { universe_id: universeId, name, parent_id: parentId || null }
    try {
      if (isEdit) await update.mutateAsync(body)
      else {
        await create.mutateAsync(body)
        setName(''); setParentId('')
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} municipality`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending
  const options = allMunicipalities?.filter((m) => m.id !== initial?.id) ?? []

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Municipality' : 'Add Municipality'}
        description={isEdit ? 'Update this municipality' : 'Add a city or district'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="m-name">Name *</Label>
            <Input id="m-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Detroit" />
          </div>
          {options.length > 0 && (
            <div className="space-y-1.5">
              <Label>Parent municipality</Label>
              <Select value={parentId || 'none'} onValueChange={(v) => setParentId(v === 'none' ? '' : v)}>
                <SelectTrigger><SelectValue placeholder="None (top-level)" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">— None —</SelectItem>
                  {options.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create'}
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

function MunicipalitiesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [creating, setCreating] = useState(false)

  const { data, isLoading } = useMunicipalities(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  const items = data?.items ?? []

  return (
    <div>
      <PageHeader
        title="Municipalities"
        description={`${data?.total ?? 0} total`}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add</Button>}
      />

      <div className="space-y-1">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full rounded-lg" />)
          : items.map((m) => (
              <Link key={m.id} to="/municipalities/$id" params={{ id: m.id }} className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2.5 hover:border-zinc-700 hover:bg-zinc-900/50 transition-colors">
                <MapPin className="h-4 w-4 shrink-0 text-zinc-600" />
                <span className="text-sm text-zinc-200">{m.name}</span>
                {m.parent_id && <span className="text-xs text-zinc-600">sub-district</span>}
              </Link>
            ))}
        {!isLoading && items.length === 0 && (
          <p className="py-12 text-center text-sm text-zinc-500">No municipalities yet</p>
        )}
      </div>

      <MunicipalityFormSheet
        universeId={universe.id}
        open={creating}
        onClose={() => setCreating(false)}
        allMunicipalities={items}
      />
    </div>
  )
}
