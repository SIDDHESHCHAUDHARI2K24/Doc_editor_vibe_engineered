import { ApiError } from './apiClient'
import type { ApiErrorResponse } from '@/types/api'

export { ApiError }
export type ApiRequestError = ApiError

export async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const body: ApiErrorResponse = await response.json()
    return new ApiError(
      body.error.code,
      body.error.message,
      body.error.details,
      response.status,
    )
  } catch {
    return new ApiError(
      'PARSE_ERROR',
      `HTTP ${response.status}: ${response.statusText}`,
      {},
      response.status,
    )
  }
}
