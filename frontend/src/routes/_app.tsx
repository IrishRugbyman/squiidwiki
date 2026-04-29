import { createFileRoute, Link, Outlet, redirect } from '@tanstack/react-router'
import {
  AlertTriangle,
  CalendarDays,
  Clock,
  FileText,
  Globe,
  Home,
  Map,
  MapPin,
  Menu,
  Network,
  NotebookText,
  ScrollText,
  Shield,
  Skull,
  Users,
  UserCog,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Drawer } from 'vaul'
import { UniverseSwitcher } from '@/components/UniverseSwitcher'
import { GlobalCommandPalette } from '@/components/GlobalCommandPalette'
import { useAuthStore, type AuthState, type AuthUser } from '@/stores/auth'
import { useUniverseStore } from '@/stores/universe'
import { useDbMode, useSetDbMode } from '@/lib/queries'
import { api, ApiError } from '@/lib/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Toaster } from '@/components/ui/sonner'
import { GO_TO_SHORTCUTS, useGoToNavigation } from '@/hooks/useKeymap'

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
  { to: '/map', icon: Map, label: 'Map' },
  { to: '/calendar', icon: CalendarDays, label: 'Calendar' },
  { to: '/timeline', icon: Clock, label: 'Timeline' },
  { to: '/research', icon: NotebookText, label: 'Research' },
] as const

const ADMIN_NAV_ITEMS = [
  { to: '/universes', icon: Globe, label: 'Universes' },
  { to: '/audit', icon: ScrollText, label: 'Audit Log' },
  { to: '/admin/users', icon: UserCog, label: 'Users' },
] as const

interface ShortcutGroup {
  title: string
  items: { keys: string; desc: string }[]
}

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: 'Global',
    items: [
      { keys: 'Ctrl+K', desc: 'Open global search / universe switcher' },
      { keys: '?', desc: 'Show keyboard shortcuts' },
      { keys: 'Esc', desc: 'Close dialogs / sheets' },
    ],
  },
  {
    title: 'Navigation',
    items: GO_TO_SHORTCUTS.map((s) => ({ keys: s.keys, desc: `Go to ${s.label}` })),
  },
  {
    title: 'On a detail page',
    items: [
      { keys: 'e', desc: 'Edit the current entity' },
    ],
  },
]

function renderKey(keys: string) {
  return keys.split(/[\s+]/).filter(Boolean).map((k, i, arr) => (
    <span key={i} className="inline-flex items-center">
      <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] font-mono text-zinc-300 shadow-sm">
        {k === 'Ctrl' ? '⌘' : k}
      </kbd>
      {i < arr.length - 1 && <span className="mx-0.5 text-zinc-600">{keys.includes('+') ? '+' : 'then'}</span>}
    </span>
  ))
}

function DbModeToggle() {
  const { data } = useDbMode()
  const { mutate, isPending } = useSetDbMode()
  const mode = data?.mode ?? 'prod'
  return (
    <button
      onClick={() => { useUniverseStore.getState().setActiveUniverse(null); mutate(mode === 'prod' ? 'test' : 'prod') }}
      disabled={isPending}
      className={`mt-2 w-full rounded px-2 py-1 text-left text-[11px] font-semibold tracking-widest transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 ${
        mode === 'test'
          ? 'bg-amber-500/15 text-amber-400 hover:bg-amber-500/25'
          : 'bg-zinc-800/60 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300'
      }`}
    >
      {mode === 'test' ? '⚠ TEST DB' : 'PROD DB'}
    </button>
  )
}

function NavLink({ to, icon: Icon, label, exact, onClick }: { to: string; icon: typeof Home; label: string; exact?: boolean; onClick?: () => void }) {
  return (
    <Link
      to={to}
      activeOptions={exact ? { exact: true } : undefined}
      className="flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:py-1.5"
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
  useGoToNavigation()

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

  // Edge swipe to open the mobile sidebar — detects a touch starting in the
  // leftmost ~20px and ending >50px to the right, mostly horizontal.
  useEffect(() => {
    let startX: number | null = null
    let startY: number | null = null
    function onTouchStart(e: TouchEvent) {
      if (window.innerWidth >= 1024) return
      const t = e.touches[0]
      if (t.clientX < 20) {
        startX = t.clientX
        startY = t.clientY
      }
    }
    function onTouchEnd(e: TouchEvent) {
      if (startX === null || startY === null) return
      const t = e.changedTouches[0]
      const dx = t.clientX - startX
      const dy = t.clientY - startY
      if (dx > 50 && Math.abs(dy) < 80) setSidebarOpen(true)
      startX = null
      startY = null
    }
    window.addEventListener('touchstart', onTouchStart, { passive: true })
    window.addEventListener('touchend', onTouchEnd, { passive: true })
    return () => {
      window.removeEventListener('touchstart', onTouchStart)
      window.removeEventListener('touchend', onTouchEnd)
    }
  }, [])

  async function handleLogout() {
    await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
    clearAuth()
    window.location.href = '/login'
  }

  const sidebar = (
    <aside className="flex w-56 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-4">
        <Link
          to="/"
          onClick={() => setSidebarOpen(false)}
          className="flex items-center rounded-md outline-none transition-colors hover:text-violet-300 focus-visible:ring-2 focus-visible:ring-violet-500/50"
          aria-label="Go to dashboard"
        >
          <Skull className="mr-2 h-5 w-5 text-violet-500" />
          <span className="font-bold tracking-tight text-white">SquiidWiki</span>
        </Link>
        <button
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation menu"
          className="lg:hidden inline-flex h-9 w-9 items-center justify-center rounded-md text-zinc-500 hover:bg-zinc-800 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
        >
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
        {user?.global_role === 'ADMIN' && <DbModeToggle />}
      </div>
    </aside>
  )

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950">
      {/* Skip-to-main link (accessibility) — visible only when focused */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-[100] focus:rounded-md focus:bg-violet-600 focus:px-3 focus:py-1.5 focus:text-sm focus:font-medium focus:text-white focus:shadow-lg"
      >
        Skip to main content
      </a>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex">{sidebar}</div>

      {/* Mobile sidebar drawer (vaul) — swipe right from the left edge to open, swipe left to close */}
      <Drawer.Root open={sidebarOpen} onOpenChange={setSidebarOpen} direction="left">
        <Drawer.Portal>
          <Drawer.Overlay className="fixed inset-0 z-40 bg-black/60 lg:hidden" />
          <Drawer.Content
            className="fixed inset-y-0 left-0 z-50 flex outline-none lg:hidden"
            aria-describedby={undefined}
          >
            <Drawer.Title className="sr-only">Main navigation</Drawer.Title>
            {sidebar}
          </Drawer.Content>
        </Drawer.Portal>
      </Drawer.Root>

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="flex h-14 items-center border-b border-zinc-800 px-4 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation menu"
            className="mr-3 inline-flex h-9 w-9 items-center justify-center rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
          >
            <Menu className="h-5 w-5" />
          </button>
          <Skull className="mr-2 h-5 w-5 text-violet-500" />
          <span className="font-bold tracking-tight text-white">SquiidWiki</span>
        </div>

        <main id="main-content" className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>

      <Toaster />
      <GlobalCommandPalette open={commandOpen} onClose={() => setCommandOpen(false)} />

      <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Keyboard shortcuts</DialogTitle>
            <DialogDescription>Move around SquiidWiki without touching the mouse.</DialogDescription>
          </DialogHeader>
          <div className="mt-2 space-y-5 max-h-[60vh] overflow-y-auto pr-1">
            {SHORTCUT_GROUPS.map((group) => (
              <section key={group.title}>
                <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{group.title}</h4>
                <ul className="space-y-1.5">
                  {group.items.map((s) => (
                    <li key={`${group.title}-${s.keys}`} className="flex items-center justify-between text-sm">
                      <span className="text-zinc-300">{s.desc}</span>
                      <span className="flex items-center gap-1">{renderKey(s.keys)}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
