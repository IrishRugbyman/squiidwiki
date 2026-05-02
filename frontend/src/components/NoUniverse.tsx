import { Globe } from 'lucide-react'

export function NoUniverse() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <Globe className="mb-4 h-12 w-12 text-zinc-700" />
      <p className="text-sm font-medium text-zinc-400">No universe selected</p>
      <p className="mt-1 text-xs text-zinc-600">Press Ctrl+K to open the universe switcher</p>
    </div>
  )
}
