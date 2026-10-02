import { createFileRoute, redirect } from '@tanstack/react-router'
import { universesQueryOptions } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'

// "/" has no universe of its own: it opens the one last used, the only one the
// viewer has, or the picker.
export const Route = createFileRoute('/_app/')({
  beforeLoad: async ({ context }) => {
    const page = await context.queryClient.fetchQuery(universesQueryOptions)
    const active = useUniverseStore.getState().activeUniverse
    const target =
      page.items.find((u) => u.id === active?.id) ?? (page.items.length === 1 ? page.items[0] : null)
    if (target) throw redirect({ to: '/$universe', params: { universe: target.slug }, replace: true })
    throw redirect({ to: '/universes', replace: true })
  },
})
