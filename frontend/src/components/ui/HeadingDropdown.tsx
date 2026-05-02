import { useState, useRef, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'

export type HeadingStyle = 'paragraph' | 'h1' | 'h2' | 'h3'

const ITEMS: Array<{ style: HeadingStyle; label: string; className: string }> = [
  { style: 'paragraph', label: 'Paragraph', className: 'text-body' },
  { style: 'h1', label: 'Heading 1', className: 'text-h1 font-bold' },
  { style: 'h2', label: 'Heading 2', className: 'text-h2 font-semibold' },
  { style: 'h3', label: 'Heading 3', className: 'text-h3 font-semibold' },
]

export interface HeadingDropdownProps {
  value: HeadingStyle
  onChange: (style: HeadingStyle) => void
}

export function HeadingDropdown({ value, onChange }: HeadingDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const current = ITEMS.find(i => i.style === value) ?? ITEMS[0]

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') { setOpen(false); return }
    if (e.key === 'Enter' || e.key === ' ') { setOpen(!open); return }
    if (e.key === 'ArrowDown' && open) {
      e.preventDefault()
      const idx = ITEMS.findIndex(i => i.style === value)
      const nextIdx = (idx + 1) % ITEMS.length
      onChange(ITEMS[nextIdx].style)
    }
    if (e.key === 'ArrowUp' && open) {
      e.preventDefault()
      const idx = ITEMS.findIndex(i => i.style === value)
      const prevIdx = (idx - 1 + ITEMS.length) % ITEMS.length
      onChange(ITEMS[prevIdx].style)
    }
  }

  return (
    <div ref={ref} className="relative" onKeyDown={handleKeyDown}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 px-2 py-1 rounded-sm hover:bg-bg-hover text-text-primary text-body min-w-[120px]"
      >
        <span className={current.className + ' truncate'}>{current.label}</span>
        <ChevronDown size={16} className="text-text-muted shrink-0" />
      </button>
      {open && (
        <div
          role="listbox"
          className="absolute top-full left-0 mt-1 min-w-[180px] bg-surface-raised border border-border-subtle rounded-md shadow-md py-1 z-50"
        >
          {ITEMS.map(item => (
            <div
              key={item.style}
              role="option"
              aria-selected={item.style === value}
              onClick={() => { onChange(item.style); setOpen(false) }}
              className={`px-3 py-2 cursor-pointer hover:bg-bg-hover ${item.style === value ? 'bg-bg-selected text-accent' : 'text-text-primary'} ${item.className}`}
            >
              {item.label}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
