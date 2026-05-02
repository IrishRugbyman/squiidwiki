import { ChevronsUpDown, Globe } from 'lucide-react'
import { useUniverseStore } from '@/stores/universe'
import { cn } from '@/lib/utils'

interface UniverseSwitcherProps {
  className?: string
  onOpen?: () => void
}

export function UniverseSwitcher({ className, onOpen }: UniverseSwitcherProps) {
  const { activeUniverse } = useUniverseStore()

  return (
    <button
      onClick={() => onOpen?.()}
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
  )
}
