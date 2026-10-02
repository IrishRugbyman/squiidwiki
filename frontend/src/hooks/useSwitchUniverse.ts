import { useNavigate, useRouterState } from '@tanstack/react-router'
import { useCallback } from 'react'
import { pathInUniverse } from '@/lib/universeRoutes'

/** Switch universe by going to the same section in it: the URL is what names
 *  the active universe, and the `$universe` route syncs the store from it. */
export function useSwitchUniverse() {
  const navigate = useNavigate()
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  return useCallback(
    (universe: { slug: string }) => navigate({ href: pathInUniverse(pathname, universe.slug) }),
    [navigate, pathname],
  )
}
