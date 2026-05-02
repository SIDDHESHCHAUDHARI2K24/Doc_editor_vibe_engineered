import { useState, useCallback } from 'react'
import type { ApiRequestError } from '@/lib/api/errors'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: ApiRequestError | null
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: (...args: unknown[]) => Promise<void>
  reset: () => void
}

export function useApi<T>(
  apiFunction: (...args: unknown[]) => Promise<T>,
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(
    async (...args: unknown[]) => {
      setState({ data: null, loading: true, error: null })
      try {
        const data = await apiFunction(...args)
        setState({ data, loading: false, error: null })
      } catch (err) {
        setState({
          data: null,
          loading: false,
          error: err instanceof Error ? (err as ApiRequestError) : null,
        })
      }
    },
    [apiFunction],
  )

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}
