import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuditLogs } from '@/lib/queries'
import { useAuthStore } from '@/stores/auth'
import type { AuditAction } from '@/lib/types'

export const Route = createFileRoute('/_app/audit')({
  component: AuditPage,
})

const ENTITY_TYPES = ['member', 'set', 'alliance', 'incident', 'source', 'municipality', 'universe']
const ACTIONS: AuditAction[] = ['CREATE', 'UPDATE', 'DELETE']
const PAGE = 50

function AuditPage() {
  const user = useAuthStore((s) => s.user)
  const [offset, setOffset] = useState(0)
  const [entityType, setEntityType] = useState('')
  const [action, setAction] = useState('')

  const { data, isLoading } = useAuditLogs({ offset, entity_type: entityType || undefined, action: action || undefined })

  if (user?.global_role !== 'ADMIN') {
    return (
      <div className="py-24 text-center text-sm text-zinc-500">
        Admin access required to view the audit log.
      </div>
    )
  }

  const items = data?.items ?? []
  const total = data?.total ?? 0

  function formatDiff(diff: Record<string, unknown> | null) {
    if (!diff) return null
    return JSON.stringify(diff, null, 2)
  }

  return (
    <div>
      <PageHeader title="Audit Log" description={`${total} entries`} />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <Label className="text-xs text-zinc-500">Entity type</Label>
          <Select value={entityType || 'all'} onValueChange={(v) => { setEntityType(v === 'all' ? '' : v); setOffset(0) }}>
            <SelectTrigger className="w-36 h-8 text-xs"><SelectValue placeholder="All" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {ENTITY_TYPES.map((t) => <SelectItem key={t} value={t} className="text-xs">{t}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-zinc-500">Action</Label>
          <Select value={action || 'all'} onValueChange={(v) => { setAction(v === 'all' ? '' : v); setOffset(0) }}>
            <SelectTrigger className="w-28 h-8 text-xs"><SelectValue placeholder="All" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All actions</SelectItem>
              {ACTIONS.map((a) => <SelectItem key={a} value={a} className="text-xs">{a}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">When</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Entity</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Action</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">User</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Changes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={5}><Skeleton className="h-4 w-64" /></td>
                  </tr>
                ))
              : items.map((entry) => (
                  <tr key={entry.id} className="hover:bg-zinc-900/30">
                    <td className="px-4 py-3 text-xs text-zinc-500 whitespace-nowrap">
                      {new Date(entry.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-mono text-zinc-400">{entry.entity_type}</span>
                      <span className="ml-1 text-xs text-zinc-600 font-mono">{entry.entity_id.slice(0, 8)}…</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold ${
                        entry.action === 'CREATE' ? 'text-emerald-400' :
                        entry.action === 'DELETE' ? 'text-red-400' : 'text-amber-400'
                      }`}>{entry.action}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-500 font-mono">
                      {entry.user_id ? entry.user_id.slice(0, 8) + '…' : '—'}
                    </td>
                    <td className="px-4 py-3 max-w-xs">
                      {entry.diff_json ? (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-zinc-500 hover:text-zinc-300">View diff</summary>
                          <pre className="mt-1 overflow-x-auto text-zinc-400 text-[10px] leading-tight">{formatDiff(entry.diff_json)}</pre>
                        </details>
                      ) : <span className="text-zinc-700">—</span>}
                    </td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-sm text-zinc-500">No audit entries found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > PAGE && (
        <div className="mt-4 flex items-center justify-between text-sm text-zinc-400">
          <span>Showing {offset + 1}–{Math.min(offset + PAGE, total)} of {total}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Prev</Button>
            <Button variant="outline" size="sm" disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>Next</Button>
          </div>
        </div>
      )}
    </div>
  )
}
