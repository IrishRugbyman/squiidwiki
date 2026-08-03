import { Link } from '@tanstack/react-router'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  icon?: LucideIcon
  label: string
  value: string | number
  hint?: string
  to?: string
  accent?: 'default' | 'violet' | 'emerald' | 'amber' | 'red'
  className?: string
}

const ACCENT_RING: Record<NonNullable<StatCardProps['accent']>, string> = {
  default: 'hover:border-zinc-700',
  violet: 'hover:border-violet-500/40',
  emerald: 'hover:border-emerald-500/40',
  amber: 'hover:border-amber-500/40',
  red: 'hover:border-red-500/40',
}

const ACCENT_ICON: Record<NonNullable<StatCardProps['accent']>, string> = {
  default: 'text-zinc-400',
  violet: 'text-violet-400',
  emerald: 'text-emerald-400',
  amber: 'text-amber-400',
  red: 'text-red-400',
}

export function StatCard({ icon: Icon, label, value, hint, to, accent = 'default', className }: StatCardProps) {
  const content = (
    <div
      className={cn(
        'flex flex-col justify-between rounded-lg border border-zinc-800 bg-zinc-950 p-4 transition-colors',
        to && ACCENT_RING[accent],
        to && 'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50',
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-400">{label}</span>
        {Icon && <Icon className={cn('h-4 w-4', ACCENT_ICON[accent])} />}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-white">{value}</span>
      </div>
      {hint && <p className="mt-1 text-xs text-zinc-400">{hint}</p>}
    </div>
  )

  if (to) {
    return (
      <Link to={to} className="block">
        {content}
      </Link>
    )
  }
  return content
}
