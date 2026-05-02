import { FormEvent } from 'react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { useApiMutation } from '@/lib/hooks/useApi'
import { useToast } from '@/components/ui/ToastContext'
import { deleteDocumentApi } from './api'
import type { DocumentResponse } from '@/types/api'

interface Props {
  isOpen: boolean
  onClose: () => void
  document: DocumentResponse
  onDeleted: () => void
}

export function DeleteConfirm({ isOpen, onClose, document, onDeleted }: Props) {
  const { toast } = useToast()
  const { mutateAsync: deleteDoc, isLoading } = useApiMutation(
    (id: string) => deleteDocumentApi(id)
  )

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await deleteDoc(document.id)
      toast.success('Document deleted')
      onDeleted()
      onClose()
    } catch (err: any) {
      toast.error(err?.message || 'Failed to delete document')
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete document">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-gray-600">
          Delete <span className="font-semibold text-gray-900">'{document.title}'</span>? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" type="submit" isLoading={isLoading}>
            Delete
          </Button>
        </div>
      </form>
    </Modal>
  )
}
