import { X } from 'lucide-react'
import type { ReactNode } from 'react'

interface BulkActionBarProps {
  count: number
  /** e.g. "member" → "12 members selected" */
  label: string
  onClear: () => void
  /** Action buttons placed between the divider and the close X. */
  children?: ReactNode
}

export function BulkActionBar({ count, label, onClear, children }: BulkActionBarProps) {
  if (count === 0) return null
  return (
    <div
      className="fixed left-1/2 z-40 flex -translate-x-1/2 items-center gap-3 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 shadow-2xl shadow-black/50"
      style={{ bottom: 'max(1.5rem, env(safe-area-inset-bottom))' }}
      role="region"
      aria-label={`Bulk actions for selected ${label}s`}
    >
      <span className="text-sm font-medium text-white">
        {count} {label}{count === 1 ? '' : 's'} selected
      </span>
      {children && (
        <>
          <div className="h-4 w-px bg-zinc-700" />
          {children}
        </>
      )}
      <button
        onClick={onClear}
        aria-label="Clear selection"
        className="text-zinc-400 transition-colors hover:text-white"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
