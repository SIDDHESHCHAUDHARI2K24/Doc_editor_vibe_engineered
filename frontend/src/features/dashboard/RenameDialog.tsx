import { useState, FormEvent, useEffect } from 'react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiMutation } from '@/lib/hooks/useApi'
import { useToast } from '@/components/ui/ToastContext'
import { renameDocumentApi } from './api'
import type { DocumentResponse } from '@/types/api'

interface Props {
  isOpen: boolean
  onClose: () => void
  document: DocumentResponse
  onRenamed: () => void
}

export function RenameDialog({ isOpen, onClose, document, onRenamed }: Props) {
  const [title, setTitle] = useState(document.title)
  const { toast } = useToast()
  const { mutateAsync: renameDoc, isLoading } = useApiMutation(
    (data: { id: string; title: string }) => renameDocumentApi(data.id, { title: data.title })
  )

  useEffect(() => {
    setTitle(document.title)
  }, [document.title, isOpen])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed || trimmed.length > 255) {
      toast.error('Title must be between 1 and 255 characters')
      return
    }
    try {
      await renameDoc({ id: document.id, title: trimmed })
      toast.success('Document renamed')
      onRenamed()
      onClose()
    } catch (err: any) {
      toast.error(err?.message || 'Failed to rename document')
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Rename document">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Title"
          value={title}
          onChange={e => setTitle(e.target.value)}
          required
          autoFocus
          maxLength={255}
        />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isLoading}>
            Rename
          </Button>
        </div>
      </form>
    </Modal>
  )
}
