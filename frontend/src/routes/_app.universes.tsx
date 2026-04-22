import { createFileRoute } from '@tanstack/react-router'
import { Globe, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { PageHeader } from '@/components/PageHeader'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { CopyButton } from '@/components/CopyButton'
import { EmptyState } from '@/components/EmptyState'
import { ListItemSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useUniverses, useCreateUniverse, useUpdateUniverse, useDeleteUniverse } from '@/lib/queries'
import { useAuthStore } from '@/stores/auth'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/universes')({
  component: UniversesPage,
})

interface UniverseItem {
  id: string
  name: string
  slug: string
  description?: string | null
}

interface UniverseFormProps {
  open: boolean
  onClose: () => void
  initial?: UniverseItem
}

function UniverseFormSheet({ open, onClose, initial }: UniverseFormProps) {
  const isEdit = !!initial
  const create = useCreateUniverse()
  const update = useUpdateUniverse(initial?.id ?? '')

  const [name, setName] = useState(initial?.name ?? '')
  const [slug, setSlug] = useState(initial?.slug ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [error, setError] = useState<string | null>(null)

  function autoSlug(n: string) {
    return n.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const body = { name, slug, description: description || null }
    try {
      if (isEdit) await update.mutateAsync(body)
      else {
        await create.mutateAsync(body)
        setName(''); setSlug(''); setDescription('')
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} universe`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Universe' : 'Create Universe'}
        description={isEdit ? 'Update this universe' : 'Create a new isolated research namespace'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="u-name">Name *</Label>
            <Input
              id="u-name" required value={name}
              onChange={(e) => { setName(e.target.value); if (!isEdit) setSlug(autoSlug(e.target.value)) }}
              placeholder="e.g. Detroit Metro"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-slug">Slug *</Label>
            <Input id="u-slug" required value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="detroit-metro" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-desc">Description</Label>
            <Textarea id="u-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional notes…" />
          </div>
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

function UniversesPage() {
  const user = useAuthStore((s) => s.user)
  const activeUniverse = useUniverseStore((s) => s.activeUniverse)
  const { data, isLoading } = useUniverses()
  const deleteUniverse = useDeleteUniverse()

  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<UniverseItem | null>(null)
  const [deleting, setDeleting] = useState<UniverseItem | null>(null)

  const items = data?.items ?? []

  async function handleDelete() {
    if (!deleting) return
    try {
      await deleteUniverse.mutateAsync(deleting.id)
      setDeleting(null)
    } catch {
      setDeleting(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Universes"
        description={`${items.length} total`}
        action={
          user?.global_role === 'ADMIN'
            ? <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />New Universe</Button>
            : undefined
        }
      />

      <div className="space-y-2">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => <ListItemSkeleton key={i} />)
          : items.map((u) => {
              const isCurrent = activeUniverse?.id === u.id
              return (
                <div
                  key={u.id}
                  className={`flex items-center justify-between rounded-lg border px-4 py-3 transition-colors ${
                    isCurrent
                      ? 'border-violet-700/60 bg-violet-950/20'
                      : 'border-zinc-800 bg-zinc-900/30'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Globe className={`h-4 w-4 ${isCurrent ? 'text-violet-400' : 'text-zinc-500'}`} />
                      <span className="font-medium text-white">{u.name}</span>
                      {isCurrent && (
                        <span className="rounded-full bg-violet-900/60 px-2 py-0.5 text-xs text-violet-300">Current</span>
                      )}
                    </div>
                    <div className="mt-0.5 flex items-center gap-1">
                      <span className="text-xs text-zinc-600 font-mono">{u.slug}</span>
                      <CopyButton value={u.slug} label="Copy slug" className="opacity-50 hover:opacity-100" silent={false} />
                    </div>
                  </div>
                  {user?.global_role === 'ADMIN' && (
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="ghost" aria-label={`Edit ${u.name}`} onClick={() => setEditing(u)} className="h-7 px-2">
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button size="sm" variant="ghost" aria-label={`Delete ${u.name}`} onClick={() => setDeleting(u)} className="h-7 px-2 text-red-500 hover:text-red-400" disabled={isCurrent}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  )}
                </div>
              )
            })}
        {!isLoading && items.length === 0 && (
          <EmptyState
            icon={Globe}
            title="No universes yet"
            description="A universe is an isolated research namespace. Create one to start recording incidents."
            action={
              user?.global_role === 'ADMIN' ? (
                <Button size="sm" onClick={() => setCreating(true)}>
                  <Plus className="mr-1.5 h-4 w-4" /> Create the first universe
                </Button>
              ) : undefined
            }
          />
        )}
      </div>

      <UniverseFormSheet open={creating} onClose={() => setCreating(false)} />
      {editing && (
        <UniverseFormSheet open={!!editing} onClose={() => setEditing(null)} initial={editing} />
      )}

      <ConfirmDialog
        open={!!deleting}
        title="Delete Universe"
        description={`Permanently delete "${deleting?.name}"? All data in this universe will be lost.`}
        impact={
          <span>
            All sets, alliances, members, incidents, sources, and municipalities inside this universe will be
            permanently destroyed. This cannot be undone.
          </span>
        }
        confirmLabel="Delete universe"
        destructive
        pending={deleteUniverse.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  )
}
