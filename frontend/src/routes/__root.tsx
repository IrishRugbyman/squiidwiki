import { type QueryClient } from '@tanstack/react-query'
import {
  createRootRouteWithContext,
  Link,
  Outlet,
  useRouter,
} from '@tanstack/react-router'
import { AlertTriangle, ArrowLeft, Home, RefreshCcw } from 'lucide-react'
import { ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'

interface RouterContext {
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: Root,
  errorComponent: RouteError,
  notFoundComponent: RouteNotFound,
})

function Root() {
  return <Outlet />
}

function RouteError({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter()
  const isAuth = error instanceof ApiError && error.status === 401
  const isForbidden = error instanceof ApiError && error.status === 403
  const isNotFound = error instanceof ApiError && error.status === 404

  const title = isAuth
    ? 'Session expired'
    : isForbidden
    ? 'Access denied'
    : isNotFound
    ? 'Not found'
    : 'Something went wrong'

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 p-6 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-950/60 text-red-400">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <h1 className="mt-6 text-xl font-semibold text-white">{title}</h1>
      <p className="mt-2 max-w-md text-sm text-zinc-400">{error.message || 'An unexpected error occurred.'}</p>
      <div className="mt-6 flex gap-2">
        <Button
          variant="outline"
          onClick={() => {
            reset()
            router.history.back()
          }}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go back
        </Button>
        <Button onClick={reset}>
          <RefreshCcw className="mr-2 h-4 w-4" />
          Try again
        </Button>
      </div>
    </div>
  )
}

function RouteNotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 p-6 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-zinc-900 text-zinc-500">
        <span className="text-xl font-semibold">404</span>
      </div>
      <h1 className="mt-6 text-xl font-semibold text-white">Page not found</h1>
      <p className="mt-2 max-w-md text-sm text-zinc-400">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link to="/" className="mt-6">
        <Button>
          <Home className="mr-2 h-4 w-4" />
          Back to dashboard
        </Button>
      </Link>
    </div>
  )
}
