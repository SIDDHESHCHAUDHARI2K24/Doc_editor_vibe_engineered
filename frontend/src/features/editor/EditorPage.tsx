import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Editor } from './Editor'
import { SaveStatusIndicator } from './SaveStatusIndicator'
import { useDocumentState } from './useDocumentState'
import { useToast } from '@/components/ui/ToastContext'
import { ArrowLeft } from 'lucide-react'

export function EditorPage() {
  const { docId } = useParams<{ docId: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()

  if (!docId) {
    navigate('/dashboard', { replace: true })
    return null
  }

  return <EditorPageContent docId={docId} />
}

function EditorPageContent({ docId }: { docId: string }) {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { ydoc, status, lastError, lastErrorStatus, hasPendingChanges, forceSave } = useDocumentState(docId)

  useEffect(() => {
    if (status === 'error' && lastErrorStatus) {
      if (lastErrorStatus === 403) {
        toast.error("You don't have access to that document.")
        navigate('/dashboard', { replace: true })
      } else if (lastErrorStatus === 404) {
        toast.error('Document not found.')
        navigate('/dashboard', { replace: true })
      }
    }
  }, [status, lastErrorStatus, lastError, navigate, toast])

  // beforeunload guard: warn when there are pending unsaved changes
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (hasPendingChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [hasPendingChanges])

  return (
    <div className="flex flex-col min-h-screen">
      <header className="flex items-center gap-4 px-8 py-4 border-b border-border-subtle bg-surface">
        <button
          onClick={() => navigate('/dashboard')}
          className="p-2 rounded-sm hover:bg-bg-hover text-text-secondary transition-colors"
          aria-label="Back to dashboard"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-h2 text-text-primary flex-1 truncate">
          {docId.slice(0, 8)}...
        </h1>
        <SaveStatusIndicator status={status} />
      </header>
      <main className="flex-1 py-12">
        <Editor ydoc={ydoc} status={status} lastError={lastError} lastErrorStatus={lastErrorStatus} forceSave={forceSave} />
      </main>
    </div>
  )
}
