import { createFileRoute, Link } from '@tanstack/react-router'
import { MapPin, Plus } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { useMunicipalities } from '@/lib/queries'
import { api } from '@/lib/api'
import { useQueryClient, useMutation } from '@tanstack/react-query'
import { useUniverseStore } from '@/stores/universe'
import type { MunicipalityRead } from '@/lib/types'

export const Route = createFileRoute('/_app/municipalities/')({
  component: MunicipalitiesPage,
})

function CreateMunicipalitySheet({ universeId, open, onClose }: { universeId: string; open: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const create = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<MunicipalityRead>('/municipalities/', body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['municipalities', universeId] }) },
  })
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      await create.mutateAsync({ universe_id: universeId, name })
      setName('')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create municipality')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title="Add Municipality" description="Add a city or district">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="m-name">Name *</Label>
            <Input id="m-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Detroit" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={create.isPending} className="flex-1">
              {create.isPending ? 'Saving…' : 'Create'}
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

      <CreateMunicipalitySheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
