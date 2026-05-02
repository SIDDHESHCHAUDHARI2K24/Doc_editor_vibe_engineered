export interface ApiError {
  code: string
  message: string
  details: Record<string, unknown>
  request_id: string
}

export interface ApiErrorResponse {
  error: ApiError
}

export interface HealthResponse {
  status: string
  version?: string
}

export interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
  created_at: string
}
