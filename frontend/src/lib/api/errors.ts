import type { ApiError, ApiErrorResponse } from '@/types/api'

export class ApiRequestError extends Error {
  public code: string
  public details: Record<string, unknown>
  public requestId: string

  constructor(error: ApiError) {
    super(error.message)
    this.name = 'ApiRequestError'
    this.code = error.code
    this.details = error.details
    this.requestId = error.request_id
  }
}

export async function parseErrorResponse(response: Response): Promise<ApiRequestError> {
  try {
    const body: ApiErrorResponse = await response.json()
    return new ApiRequestError(body.error)
  } catch {
    return new ApiRequestError({
      code: 'PARSE_ERROR',
      message: `HTTP ${response.status}: ${response.statusText}`,
      details: {},
      request_id: '',
    })
  }
}
