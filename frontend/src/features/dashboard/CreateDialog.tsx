import { useState, FormEvent } from 'react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiMutation } from '@/lib/hooks/useApi'
import { useToast } from '@/components/ui/ToastContext'
import { createDocumentApi } from './api'

interface Props {
  isOpen: boolean
  onClose: () => void
  onCreated: () => void
}

export function CreateDialog({ isOpen, onClose, onCreated }: Props) {
  const [title, setTitle] = useState('')
  const { toast } = useToast()
  const { mutateAsync: createDoc, isLoading } = useApiMutation(
    (title: string) => createDocumentApi({ title })
  )

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed || trimmed.length > 255) {
      toast.error('Title must be between 1 and 255 characters')
      return
    }
    try {
      await createDoc(trimmed)
      toast.success('Document created')
      setTitle('')
      onCreated()
    } catch (err: any) {
      toast.error(err?.message || 'Failed to create document')
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create document">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Title"
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="My document title"
          required
          autoFocus
          maxLength={255}
        />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isLoading}>
            Create
          </Button>
        </div>
      </form>
    </Modal>
  )
}
