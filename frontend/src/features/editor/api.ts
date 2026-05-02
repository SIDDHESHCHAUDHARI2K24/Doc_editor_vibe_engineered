import { ApiError } from '@/lib/api/apiClient'

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

export async function getDocumentState(docId: string): Promise<Uint8Array> {
  const res = await fetch(`/api/v1/documents/${docId}/state`, { credentials: 'include' })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(
      body?.error?.code ?? 'UNKNOWN',
      body?.error?.message ?? 'Failed to load document state',
      body?.error?.details,
      res.status,
    )
  }
  const buf = await res.arrayBuffer()
  return new Uint8Array(buf)
}

export async function putDocumentState(docId: string, state: Uint8Array): Promise<void> {
  const csrf = readCookie('csrf_token')
  const res = await fetch(`/api/v1/documents/${docId}/state`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/octet-stream', 'X-CSRF-Token': csrf ?? '' },
    body: state,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(
      body?.error?.code ?? 'UNKNOWN',
      body?.error?.message ?? 'Save failed',
      body?.error?.details,
      res.status,
    )
  }
}
