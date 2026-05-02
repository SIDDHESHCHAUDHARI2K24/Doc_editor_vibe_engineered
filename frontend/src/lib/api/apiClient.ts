function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

export class ApiError extends Error {
  constructor(
    public code: string,
    public message: string,
    public details?: unknown,
    public status?: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const API_PREFIX = '/api/v1'
const CSRF_COOKIE_NAME = 'csrf_token'
const STATE_CHANGING_METHODS = ['POST', 'PATCH', 'PUT', 'DELETE']

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, method = 'GET', headers: optHeaders, ...rest } = options

  const headers = new Headers(optHeaders as HeadersInit)

  if (STATE_CHANGING_METHODS.includes(method)) {
    const csrf = readCookie(CSRF_COOKIE_NAME)
    if (csrf) {
      headers.set('X-CSRF-Token', csrf)
    }
  }

  if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_PREFIX}${path}`, {
    ...rest,
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    let errorBody: any
    try {
      errorBody = await response.json()
    } catch {
      errorBody = {}
    }
    const err = errorBody?.error
    throw new ApiError(
      err?.code ?? 'UNKNOWN',
      err?.message ?? `Request failed with status ${response.status}`,
      err?.details,
      response.status,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const apiClient = {
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'GET' })
  },
  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'POST', body })
  },
  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'PUT', body })
  },
  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'PATCH', body })
  },
  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'DELETE' })
  },
}
