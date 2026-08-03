import { createFileRoute } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { TableRowSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuditLogs, useUsers } from '@/lib/queries'
import { useAuthStore } from '@/stores/auth'
import type { AuditAction, AuditLogRead } from '@/lib/types'

export const Route = createFileRoute('/_app/audit')({
  component: AuditPage,
})

const ENTITY_TYPES = ['member', 'set', 'alliance', 'incident', 'source', 'municipality', 'universe']
const ACTIONS: AuditAction[] = ['CREATE', 'UPDATE', 'DELETE']
const PAGE = 50

const TZ_LABEL = (() => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone
  } catch {
    return 'Local'
  }
})()

function DiffBlock({ diff }: { diff: Record<string, unknown> }) {
  const [showRaw, setShowRaw] = useState(false)

  // FastAPI audit diffs commonly look like { field: { before, after } } or
  // a flat "what changed" dict. We render a simple before/after table when
  // we can, fall back to JSON otherwise.
  const rows = useMemo(() => {
    const out: { field: string; before: unknown; after: unknown }[] = []
    for (const [k, v] of Object.entries(diff)) {
      if (
        v && typeof v === 'object' && !Array.isArray(v) &&
        ('before' in (v as object) || 'after' in (v as object))
      ) {
        const rec = v as { before?: unknown; after?: unknown }
        out.push({ field: k, before: rec.before, after: rec.after })
      } else {
        out.push({ field: k, before: undefined, after: v })
      }
    }
    return out
  }, [diff])

  function render(v: unknown) {
    if (v === undefined) return <span className="text-zinc-500">—</span>
    if (v === null) return <span className="text-zinc-500 italic">null</span>
    if (typeof v === 'string') return <span className="break-words">{v}</span>
    return <code className="font-mono text-[10px] text-zinc-400">{JSON.stringify(v)}</code>
  }

  return (
    <div className="mt-1 space-y-2">
      <div className="overflow-hidden rounded border border-zinc-800 bg-zinc-950">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="bg-zinc-900/60 text-zinc-400">
              <th className="px-2 py-1 text-left font-medium">Field</th>
              <th className="px-2 py-1 text-left font-medium">Before</th>
              <th className="px-2 py-1 text-left font-medium">After</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {rows.map((r) => (
              <tr key={r.field} className="align-top">
                <td className="px-2 py-1 font-mono text-zinc-400">{r.field}</td>
                <td className="px-2 py-1 text-rose-300/80">{render(r.before)}</td>
                <td className="px-2 py-1 text-emerald-300/80">{render(r.after)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button
        type="button"
        onClick={() => setShowRaw((v) => !v)}
        className="text-[10px] text-zinc-400 hover:text-zinc-300 transition-colors"
      >
        {showRaw ? 'Hide raw JSON' : 'Show raw JSON'}
      </button>
      {showRaw && (
        <pre className="overflow-x-auto rounded border border-zinc-800 bg-zinc-950 p-2 text-[10px] leading-tight text-zinc-400">
          {JSON.stringify(diff, null, 2)}
        </pre>
      )}
    </div>
  )
}

function AuditRow({ entry, email }: { entry: AuditLogRead; email: string | null }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <>
      <tr className="hover:bg-zinc-900/30">
        <td className="px-4 py-3 text-xs text-zinc-400 whitespace-nowrap">
          {new Date(entry.created_at).toLocaleString()}
        </td>
        <td className="px-4 py-3">
          <span className="text-xs font-mono text-zinc-400">{entry.entity_type}</span>
          <span className="ml-1 font-mono text-xs text-zinc-400">{entry.entity_id.slice(0, 8)}…</span>
        </td>
        <td className="px-4 py-3">
          <span className={`text-xs font-semibold ${
            entry.action === 'CREATE' ? 'text-emerald-400' :
            entry.action === 'DELETE' ? 'text-red-400' : 'text-amber-400'
          }`}>{entry.action}</span>
        </td>
        <td className="px-4 py-3 text-xs">
          {email ? (
            <span className="text-zinc-300">{email}</span>
          ) : entry.user_id ? (
            <span className="font-mono text-zinc-400">{entry.user_id.slice(0, 8)}…</span>
          ) : (
            <span className="text-zinc-500">—</span>
          )}
        </td>
        <td className="px-4 py-3">
          {entry.diff_json ? (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              aria-expanded={expanded}
              className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 focus-visible:outline-none focus-visible:text-zinc-200"
            >
              {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              {expanded ? 'Hide' : 'View'} diff
            </button>
          ) : (
            <span className="text-zinc-500">—</span>
          )}
        </td>
      </tr>
      {expanded && entry.diff_json && (
        <tr className="bg-zinc-950/40">
          <td colSpan={5} className="px-4 pb-4">
            <DiffBlock diff={entry.diff_json} />
          </td>
        </tr>
      )}
    </>
  )
}

function AuditPage() {
  const user = useAuthStore((s) => s.user)
  const [offset, setOffset] = useState(0)
  const [entityType, setEntityType] = useState('')
  const [action, setAction] = useState('')

  const { data, isLoading } = useAuditLogs({ offset, entity_type: entityType || undefined, action: action || undefined })
  // Load users to map user_id → email. Admin-only page already.
  const { data: usersData } = useUsers(0)

  if (user?.global_role !== 'ADMIN') {
    return (
      <div className="py-24 text-center text-sm text-zinc-400">
        Admin access required to view the audit log.
      </div>
    )
  }

  const items = data?.items ?? []
  const total = data?.total ?? 0

  const emailById = useMemo(() => {
    const m: Record<string, string> = {}
    for (const u of usersData?.items ?? []) m[u.id] = u.email
    return m
  }, [usersData])

  return (
    <div>
      <PageHeader
        title="Audit Log"
        description={`${total} entries · Times in ${TZ_LABEL}`}
      />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <Label className="text-xs text-zinc-400">Entity type</Label>
          <Select value={entityType || 'all'} onValueChange={(v) => { setEntityType(v === 'all' ? '' : v); setOffset(0) }}>
            <SelectTrigger className="w-36 h-8 text-xs"><SelectValue placeholder="All" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {ENTITY_TYPES.map((t) => <SelectItem key={t} value={t} className="text-xs">{t}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-zinc-400">Action</Label>
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
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">When</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Entity</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Action</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">User</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Changes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 10 }).map((_, i) => <TableRowSkeleton key={i} cols={5} height={44} />)
              : items.map((entry) => (
                  <AuditRow
                    key={entry.id}
                    entry={entry}
                    email={entry.user_id ? emailById[entry.user_id] ?? null : null}
                  />
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-sm text-zinc-400">No audit entries found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > PAGE && (
        <nav className="mt-4 flex items-center justify-between text-sm text-zinc-400" aria-label="Pagination">
          <span>Showing {offset + 1}–{Math.min(offset + PAGE, total)} of {total}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" aria-disabled={offset === 0} disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Prev</Button>
            <Button variant="outline" size="sm" aria-disabled={offset + PAGE >= total} disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>Next</Button>
          </div>
        </nav>
      )}
    </div>
  )
}
