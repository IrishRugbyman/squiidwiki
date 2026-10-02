import { createFileRoute, Link, notFound, Outlet, redirect } from '@tanstack/react-router'
import { Globe } from 'lucide-react'
import { universesQueryOptions } from '@/lib/queries'
import { SCOPED_SECTIONS } from '@/lib/universeRoutes'
import { useUniverseStore } from '@/stores/universe'

// The universe named in the URL is the active one. It is resolved here, before
// any page under it renders, and written to the store that every query reads
// its universe id from, so a page never fetches with the previous universe.
export const Route = createFileRoute('/_app/$universe')({
  beforeLoad: async ({ params, context, location }) => {
    const page = await context.queryClient.fetchQuery(universesQueryOptions)
    const universe = page.items.find((u) => u.slug === params.universe)
    if (universe) {
      const { activeUniverse, setActiveUniverse } = useUniverseStore.getState()
      // Compared field by field, not by id: the store is persisted, so a
      // universe renamed since the last visit would keep its old name and slug.
      if (
        activeUniverse?.id !== universe.id ||
        activeUniverse.name !== universe.name ||
        activeUniverse.slug !== universe.slug
      ) {
        setActiveUniverse({ id: universe.id, name: universe.name, slug: universe.slug })
      }
      return { universe }
    }
    // A link from before the universe was in the URL: "/members/ralph" parses
    // as universe "members". Send it into the active universe, path intact.
    if ((SCOPED_SECTIONS as readonly string[]).includes(params.universe)) {
      // Looked up by id in the fresh list: the stored slug may predate a rename.
      const activeId = useUniverseStore.getState().activeUniverse?.id
      const target =
        page.items.find((u) => u.id === activeId) ?? (page.items.length === 1 ? page.items[0] : null)
      if (target) throw redirect({ href: `/${target.slug}${location.href}`, replace: true })
      throw redirect({ to: '/universes', replace: true })
    }
    throw notFound()
  },
  component: Outlet,
  notFoundComponent: UniverseNotFound,
})

function UniverseNotFound() {
  const { universe } = Route.useParams()
  return (
    <div className="mx-auto mt-24 max-w-md space-y-4 text-center">
      <Globe className="mx-auto h-10 w-10 text-zinc-600" aria-hidden />
      <h1 className="text-xl font-semibold text-white">No universe called “{universe}”</h1>
      <p className="text-sm text-zinc-400">
        The link may be old, or you may not have access to that universe.
      </p>
      <Link to="/universes" className="inline-block text-sm text-violet-300 hover:text-violet-200">
        Pick a universe
      </Link>
    </div>
  )
}
