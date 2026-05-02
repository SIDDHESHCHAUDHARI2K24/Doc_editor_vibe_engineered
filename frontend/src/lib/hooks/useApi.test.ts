import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useApiQuery, useApiMutation } from './useApi'
import * as apiClient from '../api/apiClient'

describe('useApiQuery', () => {
  it('returns data on successful fetch', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue({ items: [] })

    const { result } = renderHook(() => useApiQuery('/test'))

    expect(result.current.isLoading).toBe(true)
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    expect(result.current.data).toEqual({ items: [] })
    expect(result.current.error).toBeNull()
  })

  it('returns error on failed fetch', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockRejectedValue(
      new apiClient.ApiError('TEST_ERROR', 'Something went wrong')
    )

    const { result } = renderHook(() => useApiQuery('/test'))

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    expect(result.current.error).toBeInstanceOf(apiClient.ApiError)
    expect(result.current.error?.message).toBe('Something went wrong')
  })
})

describe('useApiMutation', () => {
  it('returns data on successful mutation', async () => {
    const mockFn = vi.fn().mockResolvedValue({ id: '1' })
    const { result } = renderHook(() => useApiMutation(mockFn))

    const data = await result.current.mutateAsync()
    expect(data).toEqual({ id: '1' })
    expect(result.current.error).toBeNull()
  })
})
