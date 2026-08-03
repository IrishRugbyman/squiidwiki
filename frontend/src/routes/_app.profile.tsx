import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { toast } from 'sonner'
import { Shield, User as UserIcon } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

export const Route = createFileRoute('/_app/profile')({
  component: ProfilePage,
})

function initials(email: string | undefined): string {
  if (!email) return '?'
  const local = email.split('@')[0]
  const parts = local.split(/[._-]/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return local.slice(0, 2).toUpperCase()
}

function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleChangePassword(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    if (newPassword !== confirm) {
      setError('New passwords do not match')
      return
    }
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters')
      return
    }
    setPending(true)
    try {
      await api.post('/auth/profile/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      toast.success('Password changed')
      setCurrentPassword('')
      setNewPassword('')
      setConfirm('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="max-w-md">
      <PageHeader title="Profile" />

      <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-violet-900/40 text-base font-bold text-violet-300 ring-1 ring-violet-700/60">
            {initials(user?.email)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-white">{user?.email}</p>
            <p className="mt-0.5 inline-flex items-center gap-1 text-xs text-zinc-400">
              {user?.global_role === 'ADMIN' ? <Shield className="h-3 w-3 text-amber-400" /> : <UserIcon className="h-3 w-3" />}
              {user?.global_role}
            </p>
          </div>
        </div>
      </div>

      <h2 className="mb-3 text-sm font-semibold text-zinc-300">Change password</h2>
      <form onSubmit={handleChangePassword} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="p-current">Current password</Label>
          <Input
            id="p-current" type="password" autoComplete="current-password" required
            value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="p-new">New password</Label>
          <Input
            id="p-new" type="password" autoComplete="new-password" required minLength={8}
            value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
            aria-describedby="p-new-hint"
          />
          <p id="p-new-hint" className="text-[11px] text-zinc-400">
            At least 8 characters. Use a unique password you don't use elsewhere.
          </p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="p-confirm">Confirm new password</Label>
          <Input
            id="p-confirm" type="password" autoComplete="new-password" required
            value={confirm} onChange={(e) => setConfirm(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-400" role="alert">{error}</p>}
        <Button type="submit" disabled={pending}>
          {pending ? 'Saving…' : 'Change password'}
        </Button>
      </form>
    </div>
  )
}
