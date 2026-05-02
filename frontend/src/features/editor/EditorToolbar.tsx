import { useState, useEffect, useCallback } from 'react'
import Quill from 'quill'
import * as Y from 'yjs'
import { ToolbarButton } from '@/components/ui/ToolbarButton'
import { HeadingDropdown, type HeadingStyle } from '@/components/ui/HeadingDropdown'
import {
  Bold, Italic, Underline, Strikethrough,
  List, ListOrdered, Link2, RemoveFormatting,
  Undo2, Redo2,
} from 'lucide-react'

interface ToolbarProps {
  quill: Quill | null
  ydoc: Y.Doc | null
  onOpenLinkDialog: () => void
}

interface Formats {
  bold?: boolean
  italic?: boolean
  underline?: boolean
  strike?: boolean
  link?: string
  header?: number
  list?: 'ordered' | 'bullet'
}

export function EditorToolbar({ quill, ydoc, onOpenLinkDialog }: ToolbarProps) {
  const [formats, setFormats] = useState<Formats>({})
  const undoManagerRef = { current: null as Y.UndoManager | null }

  // Create Y.UndoManager when ydoc is available
  useEffect(() => {
    if (!ydoc) return
    const ytext = ydoc.getText('quill')
    undoManagerRef.current = new Y.UndoManager(ytext, { captureTimeout: 500 })
    return () => {
      undoManagerRef.current?.destroy()
      undoManagerRef.current = null
    }
  }, [ydoc])

  // Subscribe to Quill selection changes to track active formats
  useEffect(() => {
    if (!quill) return
    const handler = () => {
      const fmt = quill.getFormat() as Formats
      setFormats(fmt)
    }
    quill.on('editor-change', handler)
    return () => {
      quill.off('editor-change', handler)
    }
  }, [quill])

  const toggleInline = useCallback((format: 'bold' | 'italic' | 'underline' | 'strike') => {
    if (!quill) return
    const current = formats[format]
    quill.format(format, !current)
  }, [quill, formats])

  const toggleList = useCallback((kind: 'bullet' | 'ordered') => {
    if (!quill) return
    const current = formats.list
    if (current === kind) {
      quill.format('list', false)
    } else {
      quill.format('list', kind)
    }
  }, [quill, formats])

  const applyHeading = useCallback((style: HeadingStyle) => {
    if (!quill) return
    if (style === 'paragraph') {
      quill.format('header', false)
    } else {
      const level = style === 'h1' ? 1 : style === 'h2' ? 2 : 3
      quill.format('header', level)
    }
  }, [quill])

  const clearFormatting = useCallback(() => {
    if (!quill) return
    const range = quill.getSelection()
    if (!range) return
    quill.removeFormat(range.index, range.length)
    quill.formatLine(range.index, range.length, 'header', false)
    quill.formatLine(range.index, range.length, 'list', false)
  }, [quill])

  const undo = useCallback(() => {
    undoManagerRef.current?.undo()
  }, [])

  const redo = useCallback(() => {
    undoManagerRef.current?.redo()
  }, [])

  const handleLinkClick = useCallback(() => {
    const range = quill?.getSelection()
    if (!range || range.length === 0) return
    onOpenLinkDialog()
  }, [quill, onOpenLinkDialog])

  const headingStyle: HeadingStyle = formats.header === 1 ? 'h1' : formats.header === 2 ? 'h2' : formats.header === 3 ? 'h3' : 'paragraph'

  if (!quill) return null

  return (
    <div className="sticky top-0 z-40 bg-surface border-b border-border-subtle">
      <div className="flex items-center gap-0.5 px-2 py-1">
        {/* Undo / Redo */}
        <ToolbarButton icon={Undo2} label="Undo" onClick={undo} />
        <ToolbarButton icon={Redo2} label="Redo" onClick={redo} />

        {/* Separator */}
        <div className="w-px h-6 bg-border-subtle mx-2" />

        {/* Heading dropdown */}
        <HeadingDropdown value={headingStyle} onChange={applyHeading} />

        {/* Separator */}
        <div className="w-px h-6 bg-border-subtle mx-2" />

        {/* Bold / Italic / Underline / Strikethrough */}
        <ToolbarButton icon={Bold} label="Bold" active={formats.bold === true} onClick={() => toggleInline('bold')} />
        <ToolbarButton icon={Italic} label="Italic" active={formats.italic === true} onClick={() => toggleInline('italic')} />
        <ToolbarButton icon={Underline} label="Underline" active={formats.underline === true} onClick={() => toggleInline('underline')} />
        <ToolbarButton icon={Strikethrough} label="Strikethrough" active={formats.strike === true} onClick={() => toggleInline('strike')} />

        {/* Separator */}
        <div className="w-px h-6 bg-border-subtle mx-2" />

        {/* Link */}
        <ToolbarButton icon={Link2} label="Link" active={typeof formats.link === 'string'} onClick={handleLinkClick} />

        {/* Separator */}
        <div className="w-px h-6 bg-border-subtle mx-2" />

        {/* Lists */}
        <ToolbarButton icon={List} label="Bulleted list" active={formats.list === 'bullet'} onClick={() => toggleList('bullet')} />
        <ToolbarButton icon={ListOrdered} label="Numbered list" active={formats.list === 'ordered'} onClick={() => toggleList('ordered')} />

        {/* Separator */}
        <div className="w-px h-6 bg-border-subtle mx-2" />

        {/* Clear formatting */}
        <ToolbarButton icon={RemoveFormatting} label="Clear formatting" onClick={clearFormatting} />
      </div>
    </div>
  )
}
