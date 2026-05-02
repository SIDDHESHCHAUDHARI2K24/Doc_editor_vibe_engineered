import { useState, useEffect } from 'react'
import Quill from 'quill'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

interface LinkDialogProps {
  quill: Quill
  onClose: () => void
}

export function LinkDialog({ quill, onClose }: LinkDialogProps) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    // Pre-fill URL if selection already has a link
    const fmt = quill.getFormat()
    if (typeof fmt.link === 'string') {
      setUrl(fmt.link)
    }
  }, [quill])

  const isValidUrl = (value: string): boolean => {
    return /^(https?:\/\/|mailto:)/i.test(value.trim())
  }

  const handleSubmit = () => {
    const trimmed = url.trim()
    if (!trimmed) {
      setError('URL is required')
      return
    }
    if (!isValidUrl(trimmed)) {
      setError('URL must start with https://, http://, or mailto:')
      return
    }
    const range = quill.getSelection()
    if (!range || range.length === 0) return
    quill.format('link', trimmed)
    onClose()
  }

  const handleRemove = () => {
    const range = quill.getSelection()
    if (range) {
      quill.format('link', false)
    }
    onClose()
  }

  const hasLink = typeof quill.getFormat().link === 'string'

  return (
    <Modal isOpen={true} onClose={onClose} title={hasLink ? 'Edit link' : 'Insert link'}>
      <div className="space-y-4">
        <Input
          label="URL"
          value={url}
          onChange={(e) => { setUrl(e.target.value); setError('') }}
          placeholder="https://example.com"
          error={error}
          autoFocus
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
        />
        <div className="flex justify-end gap-2 pt-2">
          {hasLink && (
            <Button variant="destructive" onClick={handleRemove}>
              Remove link
            </Button>
          )}
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>
            {hasLink ? 'Update' : 'Insert'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
