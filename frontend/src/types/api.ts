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

export interface LoginRequest {
  identifier: string
  password: string
}

export interface UserResponse {
  id: string
  email: string
  username: string
  display_name: string
  created_at: string
}

export interface MeResponse {
  user: UserResponse
  csrf_token: string
}

export interface DocumentResponse {
  id: string
  title: string
  owner_id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface CreateDocumentRequest {
  title: string
}

export interface RenameDocumentRequest {
  title: string
}

export interface PaginatedResponse<T> {
  items: T[]
  next_cursor: string | null
}
