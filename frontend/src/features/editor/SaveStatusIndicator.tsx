import type { SaveStatus } from './useDocumentState'

export interface SaveStatusIndicatorProps {
  status: SaveStatus
}

export function SaveStatusIndicator({ status }: SaveStatusIndicatorProps) {
  if (status === 'idle') return null

  const isError = status === 'error'
  const isSaving = status === 'saving'

  return (
    <span
      className={`text-small ${
        isError ? 'text-danger' : 'text-text-muted'
      }`}
    >
      {isSaving ? 'Saving...' : isError ? 'Save failed' : 'Saved'}
    </span>
  )
}
