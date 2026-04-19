import { useQuery } from '@tanstack/react-query'
import { ChevronsUpDown, Globe, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useCreateUniverse } from '@/lib/queries'
import { useUniverseStore, type Universe } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from './ui/command'
import { Sheet, SheetContent, SheetClose } from './Sheet'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

interface UniverseListResponse {
  items: Universe[]
  total: number
}

function slugify(s: string): string {
  return s.toLowerCase().trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function CreateUniverseSheet({ open, onClose }: { open: boolean; onClose: (created?: Universe) => void }) {
  const create = useCreateUniverse()
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [slugDirty, setSlugDirty] = useState(false)
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleNameChange(v: string) {
    setName(v)
    if (!slugDirty) setSlug(slugify(v))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      const created = await create.mutateAsync({
        name: name.trim(),
        slug: slug.trim(),
        description: description.trim() || null,
      })
      setName(''); setSlug(''); setSlugDirty(false); setDescription('')
      onClose({ id: created.id, name: created.name, slug: created.slug })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create universe')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title="New Universe" description="Create an isolated workspace for a city or region">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="u-name">Name *</Label>
            <Input id="u-name" required value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="e.g. Metro Chicago" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-slug">Slug *</Label>
            <Input
              id="u-slug" required value={slug}
              onChange={(e) => { setSlug(e.target.value); setSlugDirty(true) }}
              placeholder="metro-chicago"
              pattern="[a-z0-9\-]+"
            />
            <p className="text-xs text-zinc-500">Lowercase letters, numbers, and hyphens only.</p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-desc">Description</Label>
            <Textarea id="u-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional overview…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={create.isPending || !name || !slug} className="flex-1">
              {create.isPending ? 'Creating…' : 'Create Universe'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={() => onClose()}>Cancel</Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}

export function UniverseSwitcher({ className }: { className?: string }) {
  const [open, setOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const { activeUniverse, setActiveUniverse } = useUniverseStore()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.global_role === 'ADMIN'

  const { data } = useQuery({
    queryKey: ['universes'],
    queryFn: () => api.get<UniverseListResponse>('/universes/'),
    staleTime: 60_000,
  })

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((v) => !v)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  function select(universe: Universe) {
    setActiveUniverse(universe)
    setOpen(false)
  }

  function handleCreated(u?: Universe) {
    setCreating(false)
    if (u) {
      setActiveUniverse(u)
      setOpen(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors',
          className,
        )}
      >
        <Globe className="h-4 w-4 shrink-0" />
        <span className="flex-1 truncate text-left font-medium">
          {activeUniverse?.name ?? 'Select universe'}
        </span>
        <ChevronsUpDown className="h-3.5 w-3.5" />
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Search universes… (⌘K)" />
        <CommandList>
          <CommandEmpty>No universes found.</CommandEmpty>
          <CommandGroup heading="Universes">
            {data?.items.map((u: Universe) => (
              <CommandItem key={u.id} value={u.name} onSelect={() => select(u)}>
                <Globe className="mr-2 h-4 w-4" />
                {u.name}
              </CommandItem>
            ))}
          </CommandGroup>
          {isAdmin && (
            <>
              <CommandSeparator />
              <CommandGroup>
                <CommandItem value="__create__" onSelect={() => { setOpen(false); setCreating(true) }}>
                  <Plus className="mr-2 h-4 w-4" />
                  New universe…
                </CommandItem>
              </CommandGroup>
            </>
          )}
        </CommandList>
      </CommandDialog>

      <CreateUniverseSheet open={creating} onClose={handleCreated} />
    </>
  )
}
