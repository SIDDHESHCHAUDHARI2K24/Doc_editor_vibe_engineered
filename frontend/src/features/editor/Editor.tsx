import { useRef, useEffect, createContext, useContext, useState } from 'react'
import Quill from 'quill'
import 'quill/dist/quill.bubble.css'
import { QuillBinding } from 'y-quill'
import type * as Y from 'yjs'
import type { Awareness } from 'y-protocols/awareness'
import type { SaveStatus } from './useDocumentState'
import { EditorToolbar } from './EditorToolbar'
import { LinkDialog } from './LinkDialog'
import { Spinner } from '@/components/ui/Spinner'

interface EditorContextValue {
  quill: Quill | null
}

export const EditorContext = createContext<EditorContextValue>({ quill: null })

export function useEditorQuill(): Quill | null {
  return useContext(EditorContext).quill
}

export interface EditorProps {
  ydoc: Y.Doc | null
  status: SaveStatus
  lastError: string | null
  lastErrorStatus: number | null
  forceSave: () => void
}

export function Editor({ ydoc, status, lastError, lastErrorStatus, forceSave }: EditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const quillRef = useRef<Quill | null>(null)
  const bindingRef = useRef<QuillBinding | null>(null)
  const [showLinkDialog, setShowLinkDialog] = useState(false)

  useEffect(() => {
    if (!ydoc || !editorRef.current) return

    const editorNode = editorRef.current
    editorNode.innerHTML = ''

    const quill = new Quill(editorNode, {
      theme: 'bubble',
      modules: {
        toolbar: false,
        keyboard: {
          bindings: {
            undo: null,
            redo: null,
          },
        },
      },
      placeholder: 'Start writing\u2026',
    })

    quillRef.current = quill

    const ytext = ydoc.getText('quill')
    const binding = new QuillBinding(ytext, quill, null as unknown as Awareness)
    bindingRef.current = binding

    return () => {
      binding.destroy()
      bindingRef.current = null
      quillRef.current = null
    }
  }, [ydoc])

  // Loading state
  if (!ydoc) {
    if (status === 'error' && lastErrorStatus === 403) return null
    return <EditorLoadingState status={status} error={lastError} onRetry={forceSave} />
  }

  return (
    <EditorContext.Provider value={{ quill: quillRef.current }}>
      <div className="editor-shell flex flex-col max-w-[856px] mx-auto">
        <EditorToolbar
          quill={quillRef.current}
          ydoc={ydoc}
          onOpenLinkDialog={() => setShowLinkDialog(true)}
        />
        <div ref={editorRef} className="editor-body" />
      </div>
      {showLinkDialog && (
        <LinkDialog
          quill={quillRef.current!}
          onClose={() => setShowLinkDialog(false)}
        />
      )}
    </EditorContext.Provider>
  )
}

function EditorLoadingState({ status, error, onRetry }: { status: string; error: string | null; onRetry: () => void }) {
  if (status === 'error' && error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <p className="text-text-secondary text-body">{error}</p>
        <button
          onClick={onRetry}
          className="px-5 py-2.5 rounded-pill bg-brand hover:bg-brand-hover text-text-inverse font-semibold transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center py-24 gap-4">
      <Spinner />
      <p className="text-text-muted text-small">Loading document...</p>
    </div>
  )
}
