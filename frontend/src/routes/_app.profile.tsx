import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

export const Route = createFileRoute('/_app/profile')({
  component: ProfilePage,
})

function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function handleChangePassword(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    if (newPassword !== confirm) {
      setError('New passwords do not match')
      return
    }
    setPending(true)
    try {
      await api.post('/auth/profile/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      setSuccess(true)
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

      <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 space-y-2">
        <div>
          <p className="text-xs text-zinc-500">Email</p>
          <p className="text-sm text-white">{user?.email}</p>
        </div>
        <div>
          <p className="text-xs text-zinc-500">Role</p>
          <p className="text-sm text-white">{user?.global_role}</p>
        </div>
      </div>

      <h2 className="mb-3 text-sm font-semibold text-zinc-300">Change Password</h2>
      <form onSubmit={handleChangePassword} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="p-current">Current password</Label>
          <Input
            id="p-current" type="password" required
            value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="p-new">New password</Label>
          <Input
            id="p-new" type="password" required minLength={8}
            value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="p-confirm">Confirm new password</Label>
          <Input
            id="p-confirm" type="password" required
            value={confirm} onChange={(e) => setConfirm(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        {success && <p className="text-sm text-emerald-400">Password changed successfully.</p>}
        <Button type="submit" disabled={pending}>
          {pending ? 'Saving…' : 'Change Password'}
        </Button>
      </form>
    </div>
  )
}
