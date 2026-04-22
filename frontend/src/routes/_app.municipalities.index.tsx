import { createFileRoute, Link } from '@tanstack/react-router'
import { MapPin, Pencil, Plus, Search, X } from 'lucide-react'
import { useState, useMemo } from 'react'
import { toast } from 'sonner'
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
import type { MunicipalityListItem, MunicipalityRead } from '@/lib/types'

export const Route = createFileRoute('/_app/municipalities/')({
  component: MunicipalitiesPage,
})

// ─── Form sheet (also exported for detail page) ───────────────────────────────

interface MunicipalityFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: MunicipalityRead
  allMunicipalities?: MunicipalityListItem[]
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
      if (isEdit) {
        await update.mutateAsync(body)
        toast.success(`Updated "${name}"`)
      } else {
        await create.mutateAsync(body)
        toast.success(`Added "${name}"`)
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

// ─── Row ──────────────────────────────────────────────────────────────────────

function MuniRow({
  m,
  indent = false,
  onEdit,
}: {
  m: MunicipalityListItem
  indent?: boolean
  onEdit: (m: MunicipalityListItem) => void
}) {
  return (
    <div className="group relative flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 transition-colors hover:border-zinc-700 hover:bg-zinc-900/60">
      {indent && (
        <div className="absolute left-0 top-0 bottom-0 w-px ml-6 bg-zinc-800" />
      )}
      {indent && <div className="w-4 shrink-0" />}
      <MapPin className={`h-4 w-4 shrink-0 ${indent ? 'text-zinc-600' : 'text-zinc-500'}`} />
      <Link
        to="/municipalities/$id"
        params={{ id: m.id }}
        className="min-w-0 flex-1"
      >
        <span className={`text-sm ${indent ? 'text-zinc-300' : 'font-medium text-zinc-100'}`}>
          {m.name}
        </span>
      </Link>
      <div className="flex shrink-0 items-center gap-2">
        {m.child_count > 0 && (
          <span className="rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[11px] text-zinc-500">
            {m.child_count} {m.child_count === 1 ? 'district' : 'districts'}
          </span>
        )}
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-medium tabular-nums ${
            m.incident_count > 0
              ? 'bg-amber-500/10 text-amber-400'
              : 'bg-zinc-800/60 text-zinc-600'
          }`}
        >
          {m.incident_count} {m.incident_count === 1 ? 'incident' : 'incidents'}
        </span>
        <button
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); onEdit(m) }}
          className="rounded-md p-1 text-zinc-600 opacity-0 transition-all hover:bg-zinc-700 hover:text-zinc-200 group-hover:opacity-100"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function MunicipalitiesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [creating, setCreating] = useState(false)
  const [editTarget, setEditTarget] = useState<MunicipalityListItem | null>(null)
  const [q, setQ] = useState('')

  const { data, isLoading } = useMunicipalities(universe?.id ?? null)

  if (!universe) return <NoUniverse />

  const items = data?.items ?? []

  const filtered = useMemo(() => {
    if (!q.trim()) return null
    const lower = q.toLowerCase()
    return items.filter((m) => m.name.toLowerCase().includes(lower))
  }, [items, q])

  // Build tree: top-level items, each with their children
  const topLevel = items.filter((m) => !m.parent_id)
  const childMap: Record<string, MunicipalityListItem[]> = {}
  for (const m of items) {
    if (m.parent_id) {
      if (!childMap[m.parent_id]) childMap[m.parent_id] = []
      childMap[m.parent_id].push(m)
    }
  }

  const editItem = editTarget
    ? (items.find((m) => m.id === editTarget.id) ?? editTarget)
    : null

  return (
    <div className="space-y-4">
      <PageHeader
        title="Municipalities"
        description={`${data?.total ?? 0} total`}
        action={
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus className="mr-1.5 h-4 w-4" />Add
          </Button>
        }
      />

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search municipalities…"
          className="pl-9 pr-9"
        />
        {q && (
          <button onClick={() => setQ('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="space-y-1.5">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : filtered !== null ? (
        // Search results — flat list
        <div className="space-y-1.5">
          {filtered.length === 0 ? (
            <p className="py-8 text-center text-sm text-zinc-500">No municipalities match "{q}"</p>
          ) : (
            filtered.map((m) => (
              <MuniRow key={m.id} m={m} onEdit={setEditTarget} />
            ))
          )}
        </div>
      ) : (
        // Tree view
        <div className="space-y-2">
          {topLevel.length === 0 && (
            <p className="py-12 text-center text-sm text-zinc-500">No municipalities yet</p>
          )}
          {topLevel.map((parent) => (
            <div key={parent.id} className="space-y-1">
              <MuniRow m={parent} onEdit={setEditTarget} />
              {(childMap[parent.id] ?? []).map((child) => (
                <MuniRow key={child.id} m={child} indent onEdit={setEditTarget} />
              ))}
            </div>
          ))}
          {/* Orphaned children (parent deleted) */}
          {items
            .filter((m) => m.parent_id && !items.find((p) => p.id === m.parent_id))
            .map((m) => (
              <MuniRow key={m.id} m={m} onEdit={setEditTarget} />
            ))}
        </div>
      )}

      {/* Create sheet */}
      <MunicipalityFormSheet
        universeId={universe.id}
        open={creating}
        onClose={() => setCreating(false)}
        allMunicipalities={items}
      />

      {/* Edit sheet */}
      {editItem && universe && (
        <MunicipalityFormSheet
          universeId={universe.id}
          open={!!editTarget}
          onClose={() => setEditTarget(null)}
          initial={editItem as MunicipalityRead}
          allMunicipalities={items}
        />
      )}
    </div>
  )
}
