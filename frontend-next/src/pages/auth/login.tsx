import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),
        credentials: 'include',
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? 'Login failed')
      }
      const data = await res.json()
      setAuth(data.access_token, username, data.is_admin ?? false)
      navigate({ to: '/' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 p-8 border rounded-lg shadow-sm">
        <h1 className="text-2xl font-bold text-center">SquiidWiki</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="username">Username</label>
            <input
              id="username"
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-primary-foreground rounded px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
