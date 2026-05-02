import { apiClient } from '@/lib/api/apiClient'
import type { LoginRequest, UserResponse, MeResponse } from '@/types/api'

export function loginApi(data: LoginRequest) {
  return apiClient.post<{ user: UserResponse }>('/auth/login', data)
}

export function logoutApi() {
  return apiClient.post<{ status: string }>('/auth/logout')
}

export function getMeApi() {
  return apiClient.get<MeResponse>('/auth/me')
}
