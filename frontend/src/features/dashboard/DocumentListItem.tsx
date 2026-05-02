import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { RenameDialog } from './RenameDialog'
import { DeleteConfirm } from './DeleteConfirm'
import type { DocumentResponse } from '@/types/api'

function relativeTime(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  return new Date(dateStr).toLocaleDateString()
}

interface Props {
  document: DocumentResponse
  onMutated: () => void
}

export function DocumentListItem({ document, onMutated }: Props) {
  const [showRename, setShowRename] = useState(false)
  const [showDelete, setShowDelete] = useState(false)
  const navigate = useNavigate()

  const handleOpen = () => {
    navigate(`/documents/${document.id}`)
  }

  return (
    <>
      <div className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 group">
        <div className="flex items-center gap-3 min-w-0 flex-1 cursor-pointer" onClick={handleOpen}>
          <svg className="w-5 h-5 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{document.title}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {document.updated_at ? relativeTime(document.updated_at) : '\u2014'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="secondary" onClick={(e) => { e.stopPropagation(); handleOpen() }} className="text-xs px-2 py-1">
            Open
          </Button>
          <Button variant="secondary" onClick={(e) => { e.stopPropagation(); setShowRename(true) }} className="text-xs px-2 py-1">
            Rename
          </Button>
          <Button variant="destructive" onClick={(e) => { e.stopPropagation(); setShowDelete(true) }} className="text-xs px-2 py-1">
            Delete
          </Button>
        </div>
      </div>
      <RenameDialog
        isOpen={showRename}
        onClose={() => setShowRename(false)}
        document={document}
        onRenamed={onMutated}
      />
      <DeleteConfirm
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        document={document}
        onDeleted={onMutated}
      />
    </>
  )
}
