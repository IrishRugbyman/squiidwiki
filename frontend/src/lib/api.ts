const BASE = '/api/v1'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...init, headers, credentials: 'include' })

  if (res.status === 401) {
    // Try to refresh
    const refreshed = await tryRefresh()
    if (refreshed) {
      headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`
      const retry = await fetch(`${BASE}${path}`, { ...init, headers, credentials: 'include' })
      if (!retry.ok) throw new ApiError(retry.status, await retry.text())
      return retry.json() as Promise<T>
    }
    throw new ApiError(401, 'Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

async function tryRefresh(): Promise<boolean> {
  const res = await fetch(`${BASE}/auth/refresh`, { method: 'POST', credentials: 'include' })
  if (!res.ok) {
    localStorage.removeItem('access_token')
    return false
  }
  const data = await res.json() as { access_token: string }
  localStorage.setItem('access_token', data.access_token)
  return true
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
