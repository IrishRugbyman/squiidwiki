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

const TAGLINE = 'Gang research database. Social networks, incidents and sources, scoped by metro area.'

function loginErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401 || err.status === 403) return 'Email or password is incorrect.'
    if (err.status === 429) return 'Too many attempts. Please wait a moment and try again.'
    if (err.status >= 500) return 'The server had a problem. Try again in a moment.'
    return err.message
  }
  return 'Login failed. Check your network connection and try again.'
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

  /* A failed login cannot be attributed to one field (the API deliberately
     will not say which half was wrong), so both fields carry the invalid
     state and both point at the same message. Editing either clears it. */
  const invalid = error !== null
  function clearError() {
    if (error) setError(null)
  }

  return (
    /* Asymmetric split rather than a centred card. The previous version was a
       centred card floating over a 48px grid-line texture, which is the single
       most templated auth-page composition there is. The logo is a strong,
       high-contrast asset and carries the page on its own: no texture, no mesh
       gradient, no glow behind it. */
    <div className="grid min-h-dvh grid-cols-1 bg-zinc-950 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">

      {/* Brand panel. Hidden below lg, where the compact mark in the form
          column stands in for it, so the brand is never stated twice. */}
      <aside className="relative hidden flex-col justify-center border-r border-zinc-800 bg-zinc-900/30 px-16 lg:flex">
        <img
          src="/logo.png"
          alt=""
          width={224}
          height={224}
          className="h-56 w-56 rounded-lg object-cover"
        />
        <p className="mt-8 text-3xl font-bold tracking-tight text-white">SquiidWiki</p>
        <p className="mt-3 max-w-sm text-sm leading-relaxed text-zinc-400">{TAGLINE}</p>
      </aside>

      {/* Form column. Left-aligned at lg to sit against the divider rather than
          floating in the middle of its own half. */}
      <main className="flex items-center justify-center px-6 py-12 lg:justify-start lg:px-16">
        <div className="w-full max-w-sm">

          {/* Compact mark, mobile and tablet only. */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <img
              src="/logo.png"
              alt=""
              width={44}
              height={44}
              className="h-11 w-11 shrink-0 rounded-md object-cover"
            />
            <div className="min-w-0">
              <p className="text-lg font-bold leading-tight tracking-tight text-white">SquiidWiki</p>
              <p className="truncate text-xs text-zinc-400">Gang research database</p>
            </div>
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-white">Sign in</h1>

          {/* No card chrome. The form owns its column; a bordered panel inside a
              dedicated half would be elevation that communicates nothing. */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                disabled={loading}
                aria-invalid={invalid || undefined}
                aria-describedby={invalid ? 'login-error' : undefined}
                value={email}
                onChange={(e) => { setEmail(e.target.value); clearError() }}
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
                disabled={loading}
                aria-invalid={invalid || undefined}
                aria-describedby={invalid ? 'login-error' : undefined}
                value={password}
                onChange={(e) => { setPassword(e.target.value); clearError() }}
              />
            </div>

            {error && (
              <p
                id="login-error"
                role="alert"
                className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300"
              >
                {error}
              </p>
            )}

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>

          <p className="mt-6 text-xs text-zinc-400">
            Lost your password? Contact an administrator.
          </p>
        </div>
      </main>
    </div>
  )
}
