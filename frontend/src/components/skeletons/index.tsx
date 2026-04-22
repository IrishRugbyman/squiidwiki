import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function StatCardSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded-lg border border-zinc-800 bg-zinc-950 p-4',
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-4 w-4 rounded" />
      </div>
      <Skeleton className="mt-4 h-8 w-16" />
      <Skeleton className="mt-2 h-3 w-24" />
    </div>
  )
}

export function TableRowSkeleton({ cols = 4, height = 56 }: { cols?: number; height?: number }) {
  return (
    <tr style={{ height }}>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton
            className={cn('h-4', i === 0 ? 'w-40' : 'w-24')}
          />
        </td>
      ))}
    </tr>
  )
}

export function TableSkeleton({ rows = 6, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <TableRowSkeleton key={i} cols={cols} />
      ))}
    </>
  )
}

export function MemberRowSkeleton() {
  return (
    <tr className="h-14">
      <td className="px-4 py-3">
        <Skeleton className="h-4 w-4 rounded" />
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-8 rounded-full" />
          <div className="space-y-1">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-20" />
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <Skeleton className="h-5 w-16 rounded-full" />
      </td>
      <td className="px-4 py-3">
        <Skeleton className="h-4 w-24" />
      </td>
      <td className="px-4 py-3">
        <Skeleton className="h-4 w-12" />
      </td>
    </tr>
  )
}

export function DetailHeaderSkeleton() {
  return (
    <div className="flex flex-col gap-4 border-b border-zinc-800 pb-6 md:flex-row md:items-center md:gap-6">
      <Skeleton className="h-24 w-24 rounded-lg md:h-32 md:w-32" />
      <div className="flex-1 space-y-3">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-4 w-40" />
        <div className="flex gap-2 pt-2">
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </div>
    </div>
  )
}

export function TabPanelSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3 py-4">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

export function TreeNodeSkeleton({ depth = 0 }: { depth?: number }) {
  return (
    <div
      className="flex items-center gap-3 py-2"
      style={{ paddingLeft: `${depth * 24 + 8}px` }}
    >
      <Skeleton className="h-4 w-4" />
      <Skeleton className="h-4 flex-1 max-w-sm" />
    </div>
  )
}

export function TreeSkeleton({ rows = 8 }: { rows?: number }) {
  const pattern = [0, 1, 1, 0, 1, 2, 0, 1]
  return (
    <div className="space-y-1">
      {Array.from({ length: rows }).map((_, i) => (
        <TreeNodeSkeleton key={i} depth={pattern[i % pattern.length]} />
      ))}
    </div>
  )
}

export function ListItemSkeleton() {
  return (
    <div className="flex items-center justify-between rounded-md border border-zinc-800 bg-zinc-950 px-4 py-3">
      <div className="flex items-center gap-3">
        <Skeleton className="h-8 w-8 rounded-full" />
        <div className="space-y-1.5">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
      <Skeleton className="h-5 w-12 rounded-full" />
    </div>
  )
}
