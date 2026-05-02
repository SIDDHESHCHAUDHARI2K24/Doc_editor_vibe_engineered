import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DocumentListItem } from './DocumentListItem'
import { ToastProvider } from '@/components/ui/ToastContext'
import type { DocumentResponse } from '@/types/api'

const mockDoc: DocumentResponse = {
  id: 'abc-123',
  title: 'Test Document',
  owner_id: 'user-1',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: new Date().toISOString(),
  deleted_at: null,
}

function renderDocumentListItem() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <DocumentListItem document={mockDoc} onMutated={() => {}} />
      </ToastProvider>
    </MemoryRouter>
  )
}

describe('DocumentListItem', () => {
  it('renders document title', () => {
    renderDocumentListItem()
    expect(screen.getByText('Test Document')).toBeInTheDocument()
  })

  it('renders relative time', () => {
    renderDocumentListItem()
    expect(screen.getByText('just now')).toBeInTheDocument()
  })

  it('renders action buttons', () => {
    renderDocumentListItem()
    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.getByText('Rename')).toBeInTheDocument()
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })
})
