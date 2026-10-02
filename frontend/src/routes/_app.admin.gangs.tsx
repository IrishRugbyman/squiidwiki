import { createFileRoute, redirect } from '@tanstack/react-router'
import { useUniverseStore } from '@/stores/universe'

// Gangs are a page of their own now (/<universe>/gangs), with the admin actions on it.
// Kept so old bookmarks land somewhere.
export const Route = createFileRoute('/_app/admin/gangs')({
  beforeLoad: () => {
    const universe = useUniverseStore.getState().activeUniverse?.slug
    if (universe) throw redirect({ to: '/$universe/gangs', params: { universe } })
    throw redirect({ to: '/universes' })
  },
})
