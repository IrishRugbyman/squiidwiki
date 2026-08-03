import { Link } from '@tanstack/react-router'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface BreadcrumbItem {
  label: string
  to?: string
  icon?: boolean
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn('mb-4 flex items-center text-xs text-zinc-400', className)}>
      <Link
        to="/"
        className="flex items-center gap-1 rounded px-1 py-0.5 text-zinc-400 transition-colors hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
        aria-label="Dashboard"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>
      {items.map((item, i) => {
        const isLast = i === items.length - 1
        return (
          <div key={`${item.label}-${i}`} className="flex items-center">
            <ChevronRight className="mx-1 h-3.5 w-3.5 text-zinc-500" />
            {item.to && !isLast ? (
              <Link
                to={item.to}
                className="rounded px-1 py-0.5 text-zinc-400 transition-colors hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
              >
                {item.label}
              </Link>
            ) : (
              <span
                className={cn(
                  'px-1 py-0.5',
                  isLast ? 'truncate font-medium text-zinc-200' : 'text-zinc-400',
                )}
                aria-current={isLast ? 'page' : undefined}
              >
                {item.label}
              </span>
            )}
          </div>
        )
      })}
    </nav>
  )
}
