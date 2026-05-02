import { parseErrorResponse } from './errors'

const BASE_URL = 'http://localhost:8000'

interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
}

async function request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { body, method, headers: optHeaders, ...rest } = options

  const headers: Record<string, string> = {
    ...(optHeaders as Record<string, string>),
  }

  const init: RequestInit = { ...rest, headers, credentials: 'include' }

  if (method) {
    init.method = method
  }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }

  const response = await fetch(`${BASE_URL}${path}`, init)

  if (!response.ok) {
    throw await parseErrorResponse(response)
  }

  return response.json()
}

export const apiClient = {
  get<T>(path: string, options?: ApiRequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'GET' })
  },
  post<T>(path: string, body?: unknown, options?: ApiRequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'POST', body })
  },
  put<T>(path: string, body?: unknown, options?: ApiRequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'PUT', body })
  },
  patch<T>(path: string, body?: unknown, options?: ApiRequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'PATCH', body })
  },
  delete<T>(path: string, options?: ApiRequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'DELETE' })
  },
}
