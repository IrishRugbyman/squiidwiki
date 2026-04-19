import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth'

export const Route = createFileRoute('/_app')({
  beforeLoad: () => {
    const token = localStorage.getItem('access_token')
    if (!token) throw redirect({ to: '/login' })
  },
  component: AppLayout,
})

function AppLayout() {
  const user = useAuthStore((s) => s.user)
  const clearAuth = useAuthStore((s) => s.clearAuth)

  async function handleLogout() {
    await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
    clearAuth()
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex">
      <aside className="w-56 border-r border-zinc-800 flex flex-col p-4 shrink-0">
        <span className="text-lg font-bold mb-6">SquiidWiki</span>
        <nav className="flex-1 space-y-1 text-sm text-zinc-400">
          <a href="/" className="block hover:text-white py-1">Dashboard</a>
        </nav>
        <div className="text-xs text-zinc-500 mt-4">
          <p className="truncate">{user?.email}</p>
          <button onClick={handleLogout} className="mt-1 hover:text-white">Sign out</button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
