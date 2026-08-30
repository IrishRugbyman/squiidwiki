import { beforeEach, describe, expect, it } from 'vitest'
import { HttpResponse, http, server } from '@/test/msw'
import { ApiError, api } from './api'

const BASE = '/api/v1'

beforeEach(() => {
  localStorage.clear()
})

describe('request', () => {
  it('returns the parsed body', async () => {
    server.use(http.get(`${BASE}/members/1`, () => HttpResponse.json({ id: '1', name: 'x' })))
    await expect(api.get('/members/1')).resolves.toEqual({ id: '1', name: 'x' })
  })

  it('sends the stored token as a bearer header', async () => {
    localStorage.setItem('access_token', 'tok-abc')
    let seen: string | null = null
    server.use(
      http.get(`${BASE}/whoami`, ({ request }) => {
        seen = request.headers.get('authorization')
        return HttpResponse.json({ ok: true })
      }),
    )
    await api.get('/whoami')
    expect(seen).toBe('Bearer tok-abc')
  })

  it('sends no authorization header when there is no token', async () => {
    let seen: string | null = 'unset'
    server.use(
      http.get(`${BASE}/whoami`, ({ request }) => {
        seen = request.headers.get('authorization')
        return HttpResponse.json({ ok: true })
      }),
    )
    await api.get('/whoami')
    expect(seen).toBeNull()
  })

  it('returns undefined for 204 rather than trying to parse an empty body', async () => {
    server.use(http.delete(`${BASE}/members/1`, () => new HttpResponse(null, { status: 204 })))
    await expect(api.delete('/members/1')).resolves.toBeUndefined()
  })

  it('leaves Content-Type unset for FormData so the browser can add the boundary', async () => {
    // Setting it by hand omits the multipart boundary and the upload fails
    // server-side with a parse error, which is why the client special-cases it.
    let seen: string | null = 'unset'
    server.use(
      http.post(`${BASE}/media`, ({ request }) => {
        seen = request.headers.get('content-type')
        return HttpResponse.json({ id: 'm1' })
      }),
    )
    const fd = new FormData()
    fd.append('file', new Blob(['x']), 'x.txt')
    await api.postFormData('/media', fd)
    expect(seen).toMatch(/^multipart\/form-data; boundary=/)
  })

  it('sets application/json for a normal body', async () => {
    let seen: string | null = null
    server.use(
      http.post(`${BASE}/members`, ({ request }) => {
        seen = request.headers.get('content-type')
        return HttpResponse.json({ id: 'm1' })
      }),
    )
    await api.post('/members', { name: 'x' })
    expect(seen).toBe('application/json')
  })
})

describe('error handling', () => {
  it('uses a string detail as the message', async () => {
    server.use(
      http.get(`${BASE}/x`, () => HttpResponse.json({ detail: 'Nope' }, { status: 400 })),
    )
    await expect(api.get('/x')).rejects.toMatchObject({ status: 400, message: 'Nope' })
  })

  it('uses the first msg of a FastAPI validation detail array', async () => {
    server.use(
      http.get(`${BASE}/x`, () =>
        HttpResponse.json(
          { detail: [{ loc: ['body', 'year'], msg: 'Input should be a valid integer' }] },
          { status: 422 },
        ),
      ),
    )
    await expect(api.get('/x')).rejects.toMatchObject({
      status: 422,
      message: 'Input should be a valid integer',
    })
  })

  it('carries a machine-readable code when the server sends one', async () => {
    server.use(
      http.get(`${BASE}/x`, () =>
        HttpResponse.json({ detail: 'Taken', code: 'slug_conflict' }, { status: 409 }),
      ),
    )
    await expect(api.get('/x')).rejects.toMatchObject({ code: 'slug_conflict' })
  })

  it('falls back to the status text when the body is not JSON', async () => {
    server.use(
      http.get(`${BASE}/x`, () => new HttpResponse('<html>502</html>', { status: 502 })),
    )
    const err = await api.get('/x').catch((e) => e as ApiError)
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).status).toBe(502)
  })

  it('throws ApiError, not a bare Error, so callers can read .status', async () => {
    server.use(http.get(`${BASE}/x`, () => HttpResponse.json({ detail: 'no' }, { status: 403 })))
    await expect(api.get('/x')).rejects.toBeInstanceOf(ApiError)
  })
})

describe('401 refresh', () => {
  it('refreshes, then retries the original request with the new token', async () => {
    localStorage.setItem('access_token', 'stale')
    const seen: string[] = []
    server.use(
      http.get(`${BASE}/members`, ({ request }) => {
        const auth = request.headers.get('authorization')
        seen.push(auth ?? 'none')
        if (auth === 'Bearer fresh') return HttpResponse.json({ ok: true })
        return HttpResponse.json({ detail: 'expired' }, { status: 401 })
      }),
      http.post(`${BASE}/auth/refresh`, () => HttpResponse.json({ access_token: 'fresh' })),
    )

    await expect(api.get('/members')).resolves.toEqual({ ok: true })
    expect(seen).toEqual(['Bearer stale', 'Bearer fresh'])
    expect(localStorage.getItem('access_token')).toBe('fresh')
  })

  it('clears the token and reports an expired session when the refresh is rejected', async () => {
    localStorage.setItem('access_token', 'stale')
    server.use(
      http.get(`${BASE}/members`, () => HttpResponse.json({ detail: 'expired' }, { status: 401 })),
      http.post(`${BASE}/auth/refresh`, () => new HttpResponse(null, { status: 401 })),
    )

    await expect(api.get('/members')).rejects.toMatchObject({
      status: 401,
      code: 'unauthorized',
    })
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('shares one refresh across every request that 401s at the same moment', async () => {
    // The regression this guards: refresh rotates and revokes server-side, so
    // if each of the parallel callers POSTs /auth/refresh, the first wins and
    // the rest present a just-revoked token, 401 again, and wipe the session.
    localStorage.setItem('access_token', 'stale')
    let refreshCalls = 0
    server.use(
      http.get(`${BASE}/:resource`, ({ request }) =>
        request.headers.get('authorization') === 'Bearer fresh'
          ? HttpResponse.json({ ok: true })
          : HttpResponse.json({ detail: 'expired' }, { status: 401 }),
      ),
      http.post(`${BASE}/auth/refresh`, async () => {
        refreshCalls += 1
        // A real refresh is not instant. Without the delay every caller would
        // resolve before the next one started and the test would pass even
        // with the single-flight guard removed.
        await new Promise((r) => setTimeout(r, 20))
        return HttpResponse.json({ access_token: 'fresh' })
      }),
    )

    const results = await Promise.all([
      api.get('/members'),
      api.get('/sets'),
      api.get('/incidents'),
      api.get('/alliances'),
      api.get('/sources'),
    ])

    expect(refreshCalls).toBe(1)
    expect(results).toEqual(Array(5).fill({ ok: true }))
  })

  it('refreshes again on a later 401 rather than caching the first result forever', async () => {
    // The in-flight promise is cleared in a finally, so the guard must not turn
    // into a once-per-page-load latch.
    localStorage.setItem('access_token', 'stale')
    let refreshCalls = 0
    let acceptedToken = 'fresh-1'
    server.use(
      http.get(`${BASE}/:resource`, ({ request }) =>
        request.headers.get('authorization') === `Bearer ${acceptedToken}`
          ? HttpResponse.json({ ok: true })
          : HttpResponse.json({ detail: 'expired' }, { status: 401 }),
      ),
      http.post(`${BASE}/auth/refresh`, () => {
        refreshCalls += 1
        return HttpResponse.json({ access_token: acceptedToken })
      }),
    )

    await expect(api.get('/members')).resolves.toEqual({ ok: true })
    expect(refreshCalls).toBe(1)

    // Second expiry, a new token is now the valid one.
    acceptedToken = 'fresh-2'
    await expect(api.get('/sets')).resolves.toEqual({ ok: true })
    expect(refreshCalls).toBe(2)
  })

  it('does not retry more than once when the refreshed token is also rejected', async () => {
    localStorage.setItem('access_token', 'stale')
    let getCalls = 0
    server.use(
      http.get(`${BASE}/members`, () => {
        getCalls += 1
        return HttpResponse.json({ detail: 'expired' }, { status: 401 })
      }),
      http.post(`${BASE}/auth/refresh`, () => HttpResponse.json({ access_token: 'also-bad' })),
    )

    await expect(api.get('/members')).rejects.toBeInstanceOf(ApiError)
    expect(getCalls).toBe(2)
  })
})
