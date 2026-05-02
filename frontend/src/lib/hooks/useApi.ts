import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient, ApiError } from '@/lib/api/apiClient'

interface UseApiQueryOptions {
  enabled?: boolean
}

interface UseApiQueryResult<T> {
  data: T | undefined
  error: ApiError | null
  isLoading: boolean
  refetch: () => Promise<void>
}

export function useApiQuery<T>(path: string, options: UseApiQueryOptions = {}): UseApiQueryResult<T> {
  const { enabled = true } = options
  const [data, setData] = useState<T>()
  const [error, setError] = useState<ApiError | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const mountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    if (!enabled) return
    setIsLoading(true)
    setError(null)
    try {
      const result = await apiClient.get<T>(path)
      if (mountedRef.current) {
        setData(result)
      }
    } catch (err) {
      if (mountedRef.current && err instanceof ApiError) {
        setError(err)
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [path, enabled])

  useEffect(() => {
    mountedRef.current = true
    fetchData()
    return () => { mountedRef.current = false }
  }, [fetchData])

  return { data, error, isLoading, refetch: fetchData }
}

interface UseApiMutationResult<T, Args extends unknown[]> {
  mutateAsync: (...args: Args) => Promise<T>
  isLoading: boolean
  error: ApiError | null
}

export function useApiMutation<T, Args extends unknown[] = []>(
  fn: (...args: Args) => Promise<T>
): UseApiMutationResult<T, Args> {
  const [error, setError] = useState<ApiError | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const mutateAsync = useCallback(async (...args: Args) => {
    setIsLoading(true)
    setError(null)
    try {
      return await fn(...args)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err)
      }
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [fn])

  return { mutateAsync, isLoading, error }
}
