import { useQuery } from '@tanstack/react-query'
import { ChevronsUpDown, Globe } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useUniverseStore, type Universe } from '@/stores/universe'
import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './ui/command'
import { cn } from '@/lib/utils'

interface UniverseListResponse {
  items: Universe[]
  total: number
}

export function UniverseSwitcher({ className }: { className?: string }) {
  const [open, setOpen] = useState(false)
  const { activeUniverse, setActiveUniverse } = useUniverseStore()

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
        </CommandList>
      </CommandDialog>
    </>
  )
}
