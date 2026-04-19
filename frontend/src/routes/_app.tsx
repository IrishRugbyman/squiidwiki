import { createFileRoute, Link, Outlet, redirect } from '@tanstack/react-router'
import {
  AlertTriangle,
  CalendarDays,
  FileText,
  Globe,
  Home,
  MapPin,
  Network,
  ScrollText,
  Shield,
  Skull,
  Users,
  UserCog,
} from 'lucide-react'
import { useEffect } from 'react'
import { UniverseSwitcher } from '@/components/UniverseSwitcher'
import { useAuthStore, type AuthState, type AuthUser } from '@/stores/auth'
import { api, ApiError } from '@/lib/api'

export const Route = createFileRoute('/_app')({
  beforeLoad: () => {
    const token = localStorage.getItem('access_token')
    if (!token) throw redirect({ to: '/login' })
  },
  component: AppLayout,
})

const NAV_ITEMS = [
  { to: '/', icon: Home, label: 'Dashboard', exact: true },
  { to: '/sets', icon: Shield, label: 'Sets' },
  { to: '/alliances', icon: Network, label: 'Alliances' },
  { to: '/members', icon: Users, label: 'Members' },
  { to: '/incidents', icon: AlertTriangle, label: 'Incidents' },
  { to: '/sources', icon: FileText, label: 'Sources' },
  { to: '/municipalities', icon: MapPin, label: 'Municipalities' },
  { to: '/calendar', icon: CalendarDays, label: 'Calendar' },
] as const

const ADMIN_NAV_ITEMS = [
  { to: '/universes', icon: Globe, label: 'Universes' },
  { to: '/audit', icon: ScrollText, label: 'Audit Log' },
  { to: '/admin/users', icon: UserCog, label: 'Users' },
] as const

function NavLink({ to, icon: Icon, label, exact }: { to: string; icon: typeof Home; label: string; exact?: boolean }) {
  return (
    <Link
      to={to}
      activeOptions={exact ? { exact: true } : undefined}
      className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
      activeProps={{ className: 'bg-zinc-800 !text-white' }}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {label}
    </Link>
  )
}

function AppLayout() {
  const user = useAuthStore((s: AuthState) => s.user)
  const setAuth = useAuthStore((s: AuthState) => s.setAuth)
  const clearAuth = useAuthStore((s: AuthState) => s.clearAuth)

  useEffect(() => {
    if (user) return
    const token = localStorage.getItem('access_token')
    if (!token) return
    api.get<AuthUser>('/auth/me')
      .then((u) => setAuth(u, token))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          clearAuth()
          window.location.href = '/login'
        }
      })
  }, [user, setAuth, clearAuth])

  async function handleLogout() {
    await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
    clearAuth()
    window.location.href = '/login'
  }

  return (
    <div className="flex min-h-screen bg-zinc-950">
      <aside className="flex w-56 shrink-0 flex-col border-r border-zinc-800">
        <div className="flex h-14 items-center border-b border-zinc-800 px-4">
          <Skull className="mr-2 h-5 w-5 text-violet-500" />
          <span className="font-bold tracking-tight text-white">SquiidWiki</span>
        </div>

        <div className="border-b border-zinc-800 p-2">
          <UniverseSwitcher />
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} {...item} />
          ))}
          {user?.global_role === 'ADMIN' && (
            <>
              <div className="my-1.5 border-t border-zinc-800" />
              {ADMIN_NAV_ITEMS.map((item) => (
                <NavLink key={item.to} {...item} />
              ))}
            </>
          )}
        </nav>

        <div className="border-t border-zinc-800 p-3">
          <Link to="/profile" className="block truncate text-xs text-zinc-500 hover:text-white transition-colors">
            {user?.email}
          </Link>
          <button
            onClick={handleLogout}
            className="mt-1 text-xs text-zinc-500 transition-colors hover:text-white"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
