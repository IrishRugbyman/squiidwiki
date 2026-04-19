import { createFileRoute } from '@tanstack/react-router'
import { useCurrentUser } from '@/hooks/useCurrentUser'

export const Route = createFileRoute('/_app/')({
  component: Dashboard,
})

function Dashboard() {
  const { data: user } = useCurrentUser()

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
      <p className="text-zinc-400 text-sm">Welcome back{user ? `, ${user.email}` : ''}.</p>
    </div>
  )
}
