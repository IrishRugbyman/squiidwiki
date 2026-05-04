import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api, ApiError } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import type { AuthUser } from '@/stores/auth'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

function loginErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401 || err.status === 403) return 'Email or password is incorrect.'
    if (err.status === 429) return 'Too many attempts. Please wait a moment and try again.'
    if (err.status >= 500) return 'The server had a problem. Try again in a moment.'
    return err.message
  }
  return 'Login failed — check your network connection and try again.'
}

function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token } = await api.post<{ access_token: string }>('/auth/login', { email, password })
      localStorage.setItem('access_token', access_token)
      const user = await api.get<AuthUser>('/auth/me')
      setAuth(user, access_token)
      navigate({ to: '/' })
    } catch (err) {
      setError(loginErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-zinc-950 p-4">
      {/* Subtle background glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute left-1/2 top-0 h-[400px] w-[600px] -translate-x-1/2 rounded-full bg-violet-600/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <img src="/logo.png" alt="SquiidWiki" className="mb-2 h-24 w-24 rounded-2xl object-cover shadow-lg shadow-black/40" />
          <h1 className="text-2xl font-bold tracking-tight text-white">SquiidWiki</h1>
          <p className="mt-1 text-sm text-zinc-500">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl shadow-black/30">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoFocus
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Signing in…' : 'Sign in'}
          </Button>

          <p className="pt-1 text-center text-[11px] text-zinc-600">
            Lost your password? Contact an administrator.
          </p>
        </form>
      </div>
    </div>
  )
}
