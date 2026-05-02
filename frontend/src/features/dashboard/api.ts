import { apiClient } from '@/lib/api/apiClient'
import type { DocumentResponse, PaginatedResponse, CreateDocumentRequest, RenameDocumentRequest } from '@/types/api'

export function listDocumentsApi(scope: string = 'owned', cursor?: string, limit: number = 20) {
  const params = new URLSearchParams({ scope, limit: String(limit) })
  if (cursor) params.set('cursor', cursor)
  return apiClient.get<PaginatedResponse<DocumentResponse>>(`/documents?${params}`)
}

export function createDocumentApi(data: CreateDocumentRequest) {
  return apiClient.post<DocumentResponse>('/documents', data)
}

export function renameDocumentApi(id: string, data: RenameDocumentRequest) {
  return apiClient.patch<DocumentResponse>(`/documents/${id}`, data)
}

export function deleteDocumentApi(id: string) {
  return apiClient.delete<void>(`/documents/${id}`)
}
