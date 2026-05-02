import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/AuthContext'
import { useApiQuery } from '@/lib/hooks/useApi'
import { listDocumentsApi } from './api'
import { DocumentListItem } from './DocumentListItem'
import { CreateDialog } from './CreateDialog'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import type { DocumentResponse } from '@/types/api'

export function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState<'owned' | 'shared'>('owned')
  const [showCreate, setShowCreate] = useState(false)
  const {
    data: ownedData,
    isLoading: ownedLoading,
    refetch: refetchOwned,
  } = useApiQuery<{ items: DocumentResponse[]; next_cursor: string | null }>(
    '/documents?scope=owned&limit=20',
    { enabled: tab === 'owned' }
  )

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const handleCreated = () => {
    setShowCreate(false)
    refetchOwned()
  }

  const handleMutated = () => {
    refetchOwned()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Document Editor</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.display_name || user?.email}</span>
            <Button variant="secondary" onClick={handleLogout}>Sign out</Button>
          </div>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setTab('owned')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${tab === 'owned' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Owned by me
            </button>
            <button
              onClick={() => setTab('shared')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${tab === 'shared' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Shared with me
            </button>
          </div>
          <Button onClick={() => setShowCreate(true)}>
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New document
          </Button>
        </div>

        {tab === 'shared' ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No shared documents yet</p>
            <p className="text-sm mt-1">Documents shared with you will appear here</p>
          </div>
        ) : ownedLoading ? (
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        ) : !ownedData?.items?.length ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No documents yet</p>
            <p className="text-sm mt-1">Create your first document to get started</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {ownedData.items.map(doc => (
              <DocumentListItem key={doc.id} document={doc} onMutated={handleMutated} />
            ))}
          </div>
        )}
      </main>

      <CreateDialog isOpen={showCreate} onClose={() => setShowCreate(false)} onCreated={handleCreated} />
    </div>
  )
}
