import { createFileRoute } from '@tanstack/react-router'
import { Flag, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { PageHeader } from '@/components/PageHeader'
import { TableRowSkeleton } from '@/components/skeletons'
import { Sheet, SheetClose, SheetContent } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  useCreateGang,
  useDeleteGang,
  useGangs,
  useUpdateGang,
} from '@/lib/queries'
import { useAuthStore } from '@/stores/auth'
import { useUniverseStore } from '@/stores/universe'
import type { GangListItem, UUID } from '@/lib/types'

export const Route = createFileRoute('/_app/admin/gangs')({
  component: AdminGangsPage,
})

function GangFormSheet({
  open,
  onClose,
  initial,
  universeId,
}: {
  open: boolean
  onClose: () => void
  initial: GangListItem | null
  universeId: UUID
}) {
  const create = useCreateGang(universeId)
  const update = useUpdateGang(universeId)
  const [name, setName] = useState(initial?.name ?? '')
  const [aliases, setAliases] = useState((initial?.aliases ?? []).join(', '))
  const [description, setDescription] = useState(initial?.description ?? '')
  const [color, setColor] = useState(initial?.color ?? '')

  const isEdit = !!initial

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const aliasList = aliases
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
    const body = {
      name: name.trim(),
      aliases: aliasList.length ? aliasList : null,
      description: description.trim() || null,
      color: color.trim() || null,
    }
    if (isEdit && initial) {
      await update.mutateAsync({ id: initial.id, ...body })
      toast.success(`Updated ${body.name}`)
    } else {
      await create.mutateAsync(body)
      toast.success(`Created ${body.name}`)
    }
    onClose()
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? `Edit ${initial?.name}` : 'New gang'}
        description="Top-level affiliation referenced by sets, alliances, and members."
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="gang-name">Name *</Label>
            <Input
              id="gang-name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Gangster Disciples"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gang-aliases">Aliases (comma-separated)</Label>
            <Input
              id="gang-aliases"
              value={aliases}
              onChange={(e) => setAliases(e.target.value)}
              placeholder="GD, Growth & Development"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gang-color">Color</Label>
            <div className="flex items-center gap-2">
              <input
                id="gang-color"
                type="color"
                value={color || '#7c3aed'}
                onChange={(e) => setColor(e.target.value)}
                className="h-9 w-12 cursor-pointer rounded border border-zinc-700 bg-zinc-900 p-0.5"
              />
              <Input
                value={color}
                onChange={(e) => setColor(e.target.value)}
                placeholder="#7c3aed"
                className="font-mono text-xs"
              />
              {color && (
                <Button type="button" variant="ghost" size="sm" onClick={() => setColor('')}>
                  Clear
                </Button>
              )}
            </div>
            <p className="text-[11px] text-zinc-500">
              Tints sets, alliances, and the territory map for everything tagged with this gang.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gang-desc">Description</Label>
            <Textarea
              id="gang-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
            />
          </div>
          <div className="flex gap-2 pt-2">
            <Button
              type="submit"
              disabled={create.isPending || update.isPending}
              className="flex-1"
            >
              {isEdit ? 'Save' : 'Create'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}

function AdminGangsPage() {
  const user = useAuthStore((s) => s.user)
  const universeId = useUniverseStore((s) => s.activeUniverse?.id ?? null)
  const { data, isLoading } = useGangs(universeId)
  const del = useDeleteGang(universeId ?? '')

  const [editing, setEditing] = useState<GangListItem | null>(null)
  const [creating, setCreating] = useState(false)
  const [pendingDelete, setPendingDelete] = useState<GangListItem | null>(null)

  if (user?.global_role !== 'ADMIN') {
    return (
      <div className="py-24 text-center text-sm text-zinc-500">
        Admin access required.
      </div>
    )
  }

  if (!universeId) {
    return (
      <div className="py-24 text-center text-sm text-zinc-500">
        Select a universe to manage its gangs.
      </div>
    )
  }

  const items = data?.items ?? []

  function confirmDelete() {
    if (!pendingDelete) return
    del.mutate(pendingDelete.id, {
      onSuccess: () => {
        toast.success(`Deleted ${pendingDelete.name}`)
        setPendingDelete(null)
      },
      onError: () => setPendingDelete(null),
    })
  }

  return (
    <div>
      <PageHeader
        title="Gangs"
        description={`${items.length} gang${items.length === 1 ? '' : 's'} in this universe`}
        action={
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            New gang
          </Button>
        }
      />

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Name</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Aliases</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Description</th>
              <th className="px-4 py-2.5 text-right font-medium text-zinc-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRowSkeleton key={i} cols={4} height={48} />
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8">
                  <EmptyState icon={Flag} title="No gangs yet" description="Create one to start tagging sets, alliances, and members." />
                </td>
              </tr>
            ) : (
              items.map((g) => (
                <tr key={g.id} className="hover:bg-zinc-900/30">
                  <td className="px-4 py-3 text-zinc-200">
                    <span className="inline-flex items-center gap-2">
                      {g.color ? (
                        <span
                          className="h-3.5 w-3.5 rounded-sm ring-1 ring-zinc-700"
                          style={{ backgroundColor: g.color }}
                          aria-hidden
                        />
                      ) : (
                        <Flag className="h-3.5 w-3.5 text-violet-400" />
                      )}
                      {g.name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-zinc-400">
                    {g.aliases?.length ? g.aliases.join(', ') : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-zinc-500 max-w-md truncate">
                    {g.description || '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => setEditing(g)}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-red-400 hover:text-red-300"
                        onClick={() => setPendingDelete(g)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {creating && (
        <GangFormSheet
          open
          onClose={() => setCreating(false)}
          initial={null}
          universeId={universeId}
        />
      )}
      {editing && (
        <GangFormSheet
          key={editing.id}
          open
          onClose={() => setEditing(null)}
          initial={editing}
          universeId={universeId}
        />
      )}
      {pendingDelete && (
        <ConfirmDialog
          open
          title={`Delete ${pendingDelete.name}?`}
          description="Sets, alliances, and members tagged with this gang will be unlinked. This action cannot be undone."
          confirmLabel="Delete"
          destructive
          pending={del.isPending}
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </div>
  )
}
