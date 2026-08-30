import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'

/**
 * A QueryClient with retries off and caching disabled.
 *
 * Retries are the important one: the default three-with-backoff turns an
 * asserted error state into a test that hangs until it times out, and the
 * failure then reads as "slow" rather than "the request 500ed".
 */
export function makeTestQueryClient({ gcTime = 0 }: { gcTime?: number } = {}) {
  return new QueryClient({
    defaultOptions: {
      // gcTime 0 keeps suites from leaking cache into each other, but it also
      // collects a query the moment its last observer unmounts. A test that
      // inspects cache state without mounting a hook has to raise it.
      queries: { retry: false, gcTime, staleTime: 0 },
      mutations: { retry: false },
    },
  })
}

export function renderWithClient(
  ui: ReactElement,
  options: Omit<RenderOptions, 'wrapper'> & { client?: QueryClient } = {},
) {
  const { client = makeTestQueryClient(), ...rest } = options
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return { client, ...render(ui, { wrapper, ...rest }) }
}
