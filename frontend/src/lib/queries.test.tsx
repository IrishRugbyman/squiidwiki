import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { HttpResponse, http, server } from '@/test/msw'
import { makeTestQueryClient } from '@/test/utils'
import {
  useCreateMemberIncarceration,
  useMemberIncarcerations,
  useUniverseReleaseEvents,
} from './queries'

const MEMBER = '11111111-1111-1111-1111-111111111111'
const UNIVERSE = '22222222-2222-2222-2222-222222222222'

function wrap(opts: { gcTime?: number } = {}) {
  const client = makeTestQueryClient(opts)
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return { client, wrapper }
}

describe('useMemberIncarcerations', () => {
  it('does not fire until both the member and the universe are known', async () => {
    // Without `enabled` this fires with "null" in the path on first paint and
    // the 422 surfaces as an error state on a page that is merely still loading.
    // An unhandled request is a hard failure in setup.ts, so a fired request
    // fails this test rather than silently hitting the network.
    const { wrapper } = wrap()
    const { result } = renderHook(() => useMemberIncarcerations(null, UNIVERSE), { wrapper })
    expect(result.current.fetchStatus).toBe('idle')

    const second = renderHook(() => useMemberIncarcerations(MEMBER, null), { wrapper })
    expect(second.result.current.fetchStatus).toBe('idle')
  })

  it('passes the universe as a query parameter, not just the member in the path', async () => {
    let seenUrl = ''
    server.use(
      http.get(`/api/v1/members/${MEMBER}/incarcerations`, ({ request }) => {
        seenUrl = request.url
        return HttpResponse.json([])
      }),
    )
    const { wrapper } = wrap()
    const { result } = renderHook(() => useMemberIncarcerations(MEMBER, UNIVERSE), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(new URL(seenUrl).searchParams.get('universe_id')).toBe(UNIVERSE)
  })

  it('surfaces a server error rather than an empty list', async () => {
    server.use(
      http.get(`/api/v1/members/${MEMBER}/incarcerations`, () =>
        HttpResponse.json({ detail: 'Universe mismatch' }, { status: 403 }),
      ),
    )
    const { wrapper } = wrap()
    const { result } = renderHook(() => useMemberIncarcerations(MEMBER, UNIVERSE), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toMatchObject({ status: 403, message: 'Universe mismatch' })
  })
})

describe('useCreateMemberIncarceration', () => {
  it('sends to_date through to the API', async () => {
    // The column is new; a create body that silently drops it would leave every
    // imported historical spell looking like it is still running.
    let body: unknown = null
    server.use(
      http.post(`/api/v1/members/${MEMBER}/incarcerations`, async ({ request }) => {
        body = await request.json()
        return HttpResponse.json({ id: 'spell-1' })
      }),
    )
    const { wrapper } = wrap()
    const { result } = renderHook(() => useCreateMemberIncarceration(MEMBER, UNIVERSE), { wrapper })

    result.current.mutate({
      from_date: { year: 2009, precision: 'Y', approx: false },
      to_date: { year: 2014, precision: 'Y', approx: false },
      life_sentence: false,
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(body).toMatchObject({ to_date: { year: 2014, precision: 'Y' } })
  })

  it('refetches the spell list after a create, so the new row appears', async () => {
    let getCalls = 0
    server.use(
      http.get(`/api/v1/members/${MEMBER}/incarcerations`, () => {
        getCalls += 1
        return HttpResponse.json([])
      }),
      http.post(`/api/v1/members/${MEMBER}/incarcerations`, () =>
        HttpResponse.json({ id: 'spell-1' }),
      ),
    )
    const { client, wrapper } = wrap()

    const list = renderHook(() => useMemberIncarcerations(MEMBER, UNIVERSE), { wrapper })
    await waitFor(() => expect(list.result.current.isSuccess).toBe(true))
    expect(getCalls).toBe(1)

    const create = renderHook(() => useCreateMemberIncarceration(MEMBER, UNIVERSE), { wrapper })
    create.result.current.mutate({ life_sentence: false })
    await waitFor(() => expect(create.result.current.isSuccess).toBe(true))

    await waitFor(() => expect(getCalls).toBe(2))
    client.clear()
  })

  it('also invalidates the member itself, which carries a derived status', async () => {
    // The member row shows a derived incarceration status, so it has to be
    // marked stale too. It is asserted as invalidation rather than as a refetch
    // because an unmounted query is marked and refetched on next mount, not now.
    server.use(
      http.post(`/api/v1/members/${MEMBER}/incarcerations`, () =>
        HttpResponse.json({ id: 'spell-1' }),
      ),
    )
    // gcTime raised: this query has no mounted observer, and the default 0
    // would collect it before the assertion could read its state.
    const { client, wrapper } = wrap({ gcTime: Infinity })
    client.setQueryData(['members', MEMBER], { id: MEMBER })
    expect(client.getQueryState(['members', MEMBER])?.isInvalidated).toBe(false)

    const create = renderHook(() => useCreateMemberIncarceration(MEMBER, UNIVERSE), { wrapper })
    create.result.current.mutate({ life_sentence: false })
    await waitFor(() => expect(create.result.current.isSuccess).toBe(true))

    expect(client.getQueryState(['members', MEMBER])?.isInvalidated).toBe(true)
    client.clear()
  })

  it('refetches the list exactly once, not once per invalidation call', async () => {
    // invalidateQueries matches by key prefix, so invalidating both
    // ['members', id] and ['members', id, 'incarcerations'] hits the same query
    // twice and fires two identical GETs. Only the broader key is needed.
    let getCalls = 0
    server.use(
      http.get(`/api/v1/members/${MEMBER}/incarcerations`, () => {
        getCalls += 1
        return HttpResponse.json([])
      }),
      http.post(`/api/v1/members/${MEMBER}/incarcerations`, () =>
        HttpResponse.json({ id: 'spell-1' }),
      ),
    )
    const { client, wrapper } = wrap()

    const list = renderHook(() => useMemberIncarcerations(MEMBER, UNIVERSE), { wrapper })
    await waitFor(() => expect(list.result.current.isSuccess).toBe(true))
    expect(getCalls).toBe(1)

    const create = renderHook(() => useCreateMemberIncarceration(MEMBER, UNIVERSE), { wrapper })
    create.result.current.mutate({ life_sentence: false })
    await waitFor(() => expect(create.result.current.isSuccess).toBe(true))
    await waitFor(() => expect(getCalls).toBe(2))

    // Settle, then confirm nothing further arrives.
    await new Promise((r) => setTimeout(r, 50))
    expect(getCalls).toBe(2)
    client.clear()
  })
})

describe('useUniverseReleaseEvents', () => {
  it('keys the cache by year, so switching years does not show the old one', async () => {
    // A key that omitted the year would serve 2025's events for 2026.
    const byYear: Record<string, number> = {}
    server.use(
      http.get('/api/v1/members/release-events', ({ request }) => {
        const year = new URL(request.url).searchParams.get('year') ?? '?'
        byYear[year] = (byYear[year] ?? 0) + 1
        return HttpResponse.json([{ year }])
      }),
    )
    const { wrapper } = wrap()

    const a = renderHook(() => useUniverseReleaseEvents(UNIVERSE, 2025), { wrapper })
    await waitFor(() => expect(a.result.current.isSuccess).toBe(true))
    const b = renderHook(() => useUniverseReleaseEvents(UNIVERSE, 2026), { wrapper })
    await waitFor(() => expect(b.result.current.isSuccess).toBe(true))

    expect(byYear).toEqual({ '2025': 1, '2026': 1 })
    expect(a.result.current.data).toEqual([{ year: '2025' }])
    expect(b.result.current.data).toEqual([{ year: '2026' }])
  })

  it('stays idle without a universe', () => {
    const { wrapper } = wrap()
    const { result } = renderHook(() => useUniverseReleaseEvents(null, 2026), { wrapper })
    expect(result.current.fetchStatus).toBe('idle')
  })
})
