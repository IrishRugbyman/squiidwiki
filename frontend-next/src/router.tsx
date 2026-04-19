import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from '@tanstack/react-router'
import { SidebarLayout } from '@/layouts/SidebarLayout'
import { LoginPage } from '@/pages/auth/login'
import { UniversesPage } from '@/pages/universes/index'
import { SetsPage } from '@/pages/sets/index'
import { SetDetailPage } from '@/pages/sets/detail'
import { MembersPage } from '@/pages/members/index'
import { MemberDetailPage } from '@/pages/members/detail'
import { AlliancesPage } from '@/pages/alliances/index'
import { IncidentsPage } from '@/pages/incidents/index'

const rootRoute = createRootRoute({
  component: () => <Outlet />,
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
})

const appRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'app',
  component: SidebarLayout,
})

const indexRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/',
  component: UniversesPage,
})

const setsRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/sets',
  component: SetsPage,
})

const setDetailRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/sets/$id',
  component: SetDetailPage,
})

const membersRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/members',
  component: MembersPage,
})

const memberDetailRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/members/$id',
  component: MemberDetailPage,
})

const alliancesRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/alliances',
  component: AlliancesPage,
})

const incidentsRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/incidents',
  component: IncidentsPage,
})

const routeTree = rootRoute.addChildren([
  loginRoute,
  appRoute.addChildren([
    indexRoute,
    setsRoute,
    setDetailRoute,
    membersRoute,
    memberDetailRoute,
    alliancesRoute,
    incidentsRoute,
  ]),
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
