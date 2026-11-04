import { Link } from '@tanstack/react-router'
import { Activity } from 'lucide-react'
import { EmptyState } from '@/components/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'

/** One audit row as the set and alliance feeds return it. */
export interface ActivityEntry {
  id: string
  entity_type: 'set' | 'member' | 'alliance'
  entity_id: string
  action: 'CREATE' | 'UPDATE' | 'DELETE'
  actor_email: string | null
  target_label: string | null
  target_slug: string | null
  diff_keys: string[]
  created_at: string
}

const ROUTE = {
  set: '/$universe/sets/$id',
  member: '/$universe/members/$id',
  alliance: '/$universe/alliances/$id',
} as const

/** Audit-log feed grouped by day, shared by the set and alliance pages. */
export function ActivityFeed({ entries, loading, emptyDescription }: {
  entries: ActivityEntry[]
  loading: boolean
  emptyDescription: string
}) {
  if (loading) return <Skeleton className="h-40 w-full" />
  if (entries.length === 0) {
    return <EmptyState icon={Activity} title="No activity yet" description={emptyDescription} />
  }
  // Group by YYYY-MM-DD (local time)
  const groups = new Map<string, ActivityEntry[]>()
  for (const e of entries) {
    const d = new Date(e.created_at)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(e)
  }
  return (
    <div className="space-y-4">
      {Array.from(groups.entries()).map(([day, items]) => {
        const date = new Date(items[0].created_at)
        const today = new Date()
        const isToday = date.toDateString() === today.toDateString()
        const yesterday = new Date(today.getTime() - 86_400_000)
        const isYesterday = date.toDateString() === yesterday.toDateString()
        const label = isToday ? 'Today' : isYesterday ? 'Yesterday' : date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
        return (
          <div key={day}>
            <h3 className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-zinc-400">{label}</h3>
            <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800 bg-zinc-900/30">
              {items.map((e) => {
                const verb = e.action === 'CREATE' ? 'created' : e.action === 'DELETE' ? 'deleted' : 'updated'
                const actor = e.actor_email ? e.actor_email.split('@')[0] : 'Someone'
                const target = e.target_label ?? '(deleted)'
                const time = new Date(e.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
                // The audit listener captures every column on CREATE, too noisy
                // to display; only render diff_keys for UPDATE actions.
                const showKeys = e.action === 'UPDATE' && e.diff_keys.length > 0
                return (
                  <li key={e.id} className="flex items-start gap-3 px-4 py-2.5 text-sm">
                    <span className={`mt-1 inline-block h-1.5 w-1.5 shrink-0 rounded-full ${
                      e.action === 'CREATE' ? 'bg-emerald-500' :
                      e.action === 'DELETE' ? 'bg-red-500' : 'bg-violet-500'
                    }`} aria-hidden />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-0.5">
                        <span className="text-zinc-300">{actor}</span>
                        <span className="text-zinc-400">{verb} {e.entity_type}</span>
                        <Link from="/$universe" to={ROUTE[e.entity_type]} params={{ id: e.target_slug ?? e.entity_id }} className="truncate font-medium text-violet-400 hover:underline">
                          {target}
                        </Link>
                        <span className="ml-auto font-mono text-[11px] tabular-nums text-zinc-400">{time}</span>
                      </div>
                      {showKeys && (
                        <div className="mt-0.5 flex flex-wrap gap-1 text-[10px] text-zinc-400">
                          {e.diff_keys.slice(0, 6).map((k) => (
                            <span key={k} className="rounded bg-zinc-800/60 px-1.5 py-0.5">{k}</span>
                          ))}
                          {e.diff_keys.length > 6 && <span className="text-zinc-400">+{e.diff_keys.length - 6}</span>}
                        </div>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        )
      })}
    </div>
  )
}
