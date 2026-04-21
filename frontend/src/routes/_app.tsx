import { createFileRoute, Link, Outlet, redirect } from '@tanstack/react-router'
import {
  AlertTriangle,
  CalendarDays,
  FileText,
  Globe,
  Home,
  MapPin,
  Menu,
  Network,
  ScrollText,
  Shield,
  Skull,
  Users,
  UserCog,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { UniverseSwitcher } from '@/components/UniverseSwitcher'
import { GlobalCommandPalette } from '@/components/GlobalCommandPalette'
import { useAuthStore, type AuthState, type AuthUser } from '@/stores/auth'
import { api, ApiError } from '@/lib/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Toaster } from '@/components/ui/sonner'

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

const SHORTCUTS = [
  { keys: 'Ctrl+K', desc: 'Open global search / universe switcher' },
  { keys: '?', desc: 'Show keyboard shortcuts' },
  { keys: 'Esc', desc: 'Close dialogs / sheets' },
]

function NavLink({ to, icon: Icon, label, exact, onClick }: { to: string; icon: typeof Home; label: string; exact?: boolean; onClick?: () => void }) {
  return (
    <Link
      to={to}
      activeOptions={exact ? { exact: true } : undefined}
      className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
      activeProps={{ className: 'bg-zinc-800 !text-white' }}
      onClick={onClick}
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
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)
  const [commandOpen, setCommandOpen] = useState(false)

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

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandOpen((v) => !v)
        return
      }
      const tag = (e.target as HTMLElement).tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
      if (e.key === '?') { e.preventDefault(); setHelpOpen(true) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  async function handleLogout() {
    await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
    clearAuth()
    window.location.href = '/login'
  }

  const sidebar = (
    <aside className="flex w-56 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-4">
        <div className="flex items-center">
          <Skull className="mr-2 h-5 w-5 text-violet-500" />
          <span className="font-bold tracking-tight text-white">SquiidWiki</span>
        </div>
        <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-zinc-500 hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="border-b border-zinc-800 p-2">
        <UniverseSwitcher onOpen={() => setCommandOpen(true)} />
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} {...item} onClick={() => setSidebarOpen(false)} />
        ))}
        {user?.global_role === 'ADMIN' && (
          <>
            <div className="my-1.5 border-t border-zinc-800" />
            {ADMIN_NAV_ITEMS.map((item) => (
              <NavLink key={item.to} {...item} onClick={() => setSidebarOpen(false)} />
            ))}
          </>
        )}
      </nav>

      <div className="border-t border-zinc-800 p-3">
        <Link to="/profile" className="block truncate text-xs text-zinc-500 hover:text-white transition-colors" onClick={() => setSidebarOpen(false)}>
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
  )

  return (
    <div className="flex min-h-screen bg-zinc-950">
      {/* Desktop sidebar */}
      <div className="hidden lg:flex">{sidebar}</div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSidebarOpen(false)} />
          <div className="relative z-10 flex">{sidebar}</div>
        </div>
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="flex h-14 items-center border-b border-zinc-800 px-4 lg:hidden">
          <button onClick={() => setSidebarOpen(true)} className="mr-3 text-zinc-400 hover:text-white">
            <Menu className="h-5 w-5" />
          </button>
          <Skull className="mr-2 h-5 w-5 text-violet-500" />
          <span className="font-bold tracking-tight text-white">SquiidWiki</span>
        </div>

        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>

      <Toaster />
      <GlobalCommandPalette open={commandOpen} onClose={() => setCommandOpen(false)} />

      <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Keyboard shortcuts</DialogTitle>
          </DialogHeader>
          <div className="mt-2 space-y-2">
            {SHORTCUTS.map((s) => (
              <div key={s.keys} className="flex items-center justify-between text-sm">
                <span className="text-zinc-300">{s.desc}</span>
                <kbd className="rounded bg-zinc-800 px-2 py-0.5 text-xs font-mono text-zinc-400">{s.keys}</kbd>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
