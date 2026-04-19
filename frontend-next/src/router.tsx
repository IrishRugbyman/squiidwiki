import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from '@tanstack/react-router'
import { SidebarLayout } from '@/layouts/SidebarLayout'
import { LoginPage } from '@/pages/auth/login'

const rootRoute = createRootRoute({
  component: () => <Outlet />,
})

const authRoute = createRoute({
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
  component: () => (
    <div className="p-6">
      <h1 className="text-2xl font-bold">SquiidWiki</h1>
      <p className="text-muted-foreground mt-2">Select a universe to get started.</p>
    </div>
  ),
})

const routeTree = rootRoute.addChildren([
  authRoute,
  appRoute.addChildren([indexRoute]),
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
