import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient, ApiError } from './apiClient'

describe('apiClient', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('performs GET request and returns JSON', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'test' }),
    } as Response)

    const result = await apiClient.get('/test')
    expect(result).toEqual({ data: 'test' })
    expect(fetch).toHaveBeenCalledWith('/api/v1/test', expect.objectContaining({
      method: 'GET',
      credentials: 'include',
    }))
  })

  it('throws ApiError on non-ok response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({
        error: { code: 'AUTH_REQUIRED', message: 'Please log in', details: {} }
      }),
    } as Response)

    const error = await apiClient.get('/test').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      code: 'AUTH_REQUIRED',
      message: 'Please log in',
    })
  })

  it('handles 204 No Content', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 204,
    } as Response)

    const result = await apiClient.delete('/test')
    expect(result).toBeUndefined()
  })

  it('attaches X-CSRF-Token header on POST requests', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=test-csrf-token',
    })

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    } as Response)

    await apiClient.post('/test', { title: 'hello' })

    expect(fetch).toHaveBeenCalledWith('/api/v1/test', expect.objectContaining({
      method: 'POST',
    }))
    const callArgs = (fetch as any).mock.calls[0][1]
    expect(callArgs.headers.get('X-CSRF-Token')).toBe('test-csrf-token')
  })
})
