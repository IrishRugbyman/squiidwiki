const BASE = '/api/v1'

export class ApiError extends Error {
  status: number
  code?: string
  constructor(status: number, message: string, code?: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function parseError(res: Response): Promise<ApiError> {
  const body = await res.json().catch(() => null)
  let message: string = res.statusText
  let code: string | undefined
  if (body && typeof body === 'object') {
    const rec = body as Record<string, unknown>
    if (typeof rec.detail === 'string') message = rec.detail
    else if (Array.isArray(rec.detail) && rec.detail.length > 0) {
      const first = rec.detail[0] as Record<string, unknown>
      if (typeof first?.msg === 'string') message = first.msg
    }
    if (typeof rec.code === 'string') code = rec.code
  }
  return new ApiError(res.status, message, code)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  const isFormData = typeof FormData !== 'undefined' && init.body instanceof FormData
  // Browser sets Content-Type (with multipart boundary) automatically for FormData;
  // setting it manually breaks the upload.
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(init.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...init, headers, credentials: 'include' })

  if (res.status === 401) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`
      const retry = await fetch(`${BASE}${path}`, { ...init, headers, credentials: 'include' })
      if (!retry.ok) throw await parseError(retry)
      if (retry.status === 204) return undefined as T
      return retry.json() as Promise<T>
    }
    throw new ApiError(401, 'Session expired. Please sign in again.', 'unauthorized')
  }

  if (!res.ok) throw await parseError(res)
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
  postFormData: <T>(path: string, body: FormData) =>
    request<T>(path, { method: 'POST', body }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body !== undefined ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
