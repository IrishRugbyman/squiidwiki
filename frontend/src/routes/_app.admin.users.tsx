import { createFileRoute } from '@tanstack/react-router'
import { Search, Shield, User as UserIcon } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/PageHeader'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { TableRowSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useUsers, useUpdateUserRole } from '@/lib/queries'
import { useAuthStore } from '@/stores/auth'
import type { GlobalRole, UserListItem } from '@/lib/types'

export const Route = createFileRoute('/_app/admin/users')({
  component: AdminUsersPage,
})

const PAGE = 20

function relativeTime(iso: string | null): string {
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  const now = Date.now()
  const diffMs = now - then
  const hours = Math.round(diffMs / 3_600_000)
  if (hours < 1) return 'just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days}d ago`
  const months = Math.round(days / 30)
  if (months < 12) return `${months}mo ago`
  return `${Math.round(months / 12)}y ago`
}

function AdminUsersPage() {
  const user = useAuthStore((s) => s.user)
  const [offset, setOffset] = useState(0)
  const [q, setQ] = useState('')
  const [roleFilter, setRoleFilter] = useState<GlobalRole | 'ALL'>('ALL')
  const [pendingChange, setPendingChange] = useState<{ target: UserListItem; newRole: GlobalRole } | null>(null)

  const { data, isLoading } = useUsers(offset)
  const updateRole = useUpdateUserRole()

  if (user?.global_role !== 'ADMIN') {
    return (
      <div className="py-24 text-center text-sm text-zinc-500">
        Admin access required.
      </div>
    )
  }

  const allItems = data?.items ?? []
  const total = data?.total ?? 0

  const items = useMemo(() => {
    return allItems
      .filter((u) => !q || u.email.toLowerCase().includes(q.toLowerCase()))
      .filter((u) => roleFilter === 'ALL' || u.global_role === roleFilter)
  }, [allItems, q, roleFilter])

  function confirmRoleChange() {
    if (!pendingChange) return
    const { target, newRole } = pendingChange
    updateRole.mutate(
      { userId: target.id, role: newRole },
      {
        onSuccess: () => {
          toast.success(`${target.email} is now ${newRole}`)
          setPendingChange(null)
        },
        onError: () => {
          setPendingChange(null)
        },
      },
    )
  }

  return (
    <div>
      <PageHeader title="Users" description={`${total} total`} />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8 h-8 text-sm" placeholder="Filter by email…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <Select value={roleFilter} onValueChange={(v) => setRoleFilter(v as GlobalRole | 'ALL')}>
          <SelectTrigger className="h-8 w-32 text-xs"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All roles</SelectItem>
            <SelectItem value="ADMIN">Admins</SelectItem>
            <SelectItem value="USER">Users</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Email</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Role</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Joined</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400" scope="col">Last login</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => <TableRowSkeleton key={i} cols={4} height={48} />)
              : items.map((u) => (
                  <tr key={u.id} className="hover:bg-zinc-900/30">
                    <td className="px-4 py-3 text-zinc-200">
                      <span className="inline-flex items-center gap-2">
                        {u.global_role === 'ADMIN' ? <Shield className="h-3.5 w-3.5 text-amber-400" /> : <UserIcon className="h-3.5 w-3.5 text-zinc-500" />}
                        {u.email}
                        {u.id === user?.id && <span className="rounded-full bg-violet-900/40 px-1.5 py-0.5 text-[10px] text-violet-300">you</span>}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Select
                        value={u.global_role}
                        onValueChange={(v) => {
                          const newRole = v as GlobalRole
                          if (newRole === u.global_role) return
                          setPendingChange({ target: u, newRole })
                        }}
                        disabled={u.id === user?.id}
                      >
                        <SelectTrigger className="w-24 h-7 text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ADMIN" className="text-xs">ADMIN</SelectItem>
                          <SelectItem value="USER" className="text-xs">USER</SelectItem>
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-500">
                      <span title={new Date(u.created_at).toLocaleString()}>
                        {new Date(u.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-500">
                      {u.last_login_at ? (
                        <span title={new Date(u.last_login_at).toLocaleString()}>
                          {relativeTime(u.last_login_at)}
                        </span>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-sm text-zinc-500">
                  {q || roleFilter !== 'ALL' ? 'No users match the current filters' : 'No users found'}
                </td>
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

      {pendingChange && (
        <ConfirmDialog
          open
          title={`Change role for ${pendingChange.target.email}?`}
          description={`This user's role will change from ${pendingChange.target.global_role} to ${pendingChange.newRole}.`}
          impact={pendingChange.newRole === 'ADMIN' ? (
            <span>Admins can view audit logs, manage universes, change user roles, and delete entities.</span>
          ) : null}
          confirmLabel={`Set ${pendingChange.newRole}`}
          destructive={pendingChange.newRole === 'ADMIN'}
          pending={updateRole.isPending}
          onConfirm={confirmRoleChange}
          onCancel={() => setPendingChange(null)}
        />
      )}
    </div>
  )
}
