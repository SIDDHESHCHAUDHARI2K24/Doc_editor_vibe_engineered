import { ComponentType, ButtonHTMLAttributes } from 'react'

export interface ToolbarButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: ComponentType<{ size?: number; className?: string }>
  label: string
  active?: boolean
}

export function ToolbarButton({ icon: Icon, label, active, className = '', ...props }: ToolbarButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      aria-pressed={active}
      className={`h-8 w-8 inline-flex items-center justify-center rounded-sm transition-colors
        hover:bg-bg-hover focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none
        ${active ? 'bg-bg-selected text-accent' : 'text-text-secondary'}
        disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      {...props}
    >
      <Icon size={18} />
    </button>
  )
}
