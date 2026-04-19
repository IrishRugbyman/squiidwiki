import { createFileRoute } from '@tanstack/react-router'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useUsers, useUpdateUserRole } from '@/lib/queries'
import { useAuthStore } from '@/stores/auth'
import { useState } from 'react'
import type { GlobalRole } from '@/lib/types'

export const Route = createFileRoute('/_app/admin/users')({
  component: AdminUsersPage,
})

const PAGE = 20

function AdminUsersPage() {
  const user = useAuthStore((s) => s.user)
  const [offset, setOffset] = useState(0)
  const { data, isLoading } = useUsers(offset)
  const updateRole = useUpdateUserRole()

  if (user?.global_role !== 'ADMIN') {
    return (
      <div className="py-24 text-center text-sm text-zinc-500">
        Admin access required.
      </div>
    )
  }

  const items = data?.items ?? []
  const total = data?.total ?? 0

  return (
    <div>
      <PageHeader title="Users" description={`${total} total`} />

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Email</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Role</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Joined</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Last login</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={4}><Skeleton className="h-4 w-64" /></td>
                  </tr>
                ))
              : items.map((u) => (
                  <tr key={u.id} className="hover:bg-zinc-900/30">
                    <td className="px-4 py-3 text-zinc-200">{u.email}</td>
                    <td className="px-4 py-3">
                      <Select
                        value={u.global_role}
                        onValueChange={(v) => updateRole.mutate({ userId: u.id, role: v as GlobalRole })}
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
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-500">
                      {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-sm text-zinc-500">No users found</td>
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
