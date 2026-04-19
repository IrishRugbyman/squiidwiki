import { Link, Outlet, useNavigate } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth'
import { useUniverseStore } from '@/stores/universe'

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/sets', label: 'Sets' },
  { to: '/members', label: 'Members' },
  { to: '/alliances', label: 'Alliances' },
  { to: '/incidents', label: 'Incidents' },
  { to: '/sources', label: 'Sources' },
]

export function SidebarLayout() {
  const { username, clearAuth } = useAuthStore()
  const { active: universe } = useUniverseStore()
  const navigate = useNavigate()

  function handleLogout() {
    fetch('/auth/logout', { method: 'GET', credentials: 'include' })
    clearAuth()
    navigate({ to: '/login' })
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-56 border-r flex flex-col">
        <div className="p-4 border-b">
          <span className="font-bold text-lg">SquiidWiki</span>
          {universe && (
            <p className="text-xs text-muted-foreground mt-1 truncate">{universe.name}</p>
          )}
        </div>

        <nav className="flex-1 p-2 space-y-1">
          {navItems.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="flex items-center px-3 py-2 text-sm rounded hover:bg-accent hover:text-accent-foreground transition-colors"
              activeProps={{ className: 'bg-accent text-accent-foreground font-medium' }}
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t text-sm">
          <p className="text-muted-foreground truncate">{username}</p>
          <button
            onClick={handleLogout}
            className="mt-2 text-xs text-destructive hover:underline"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
