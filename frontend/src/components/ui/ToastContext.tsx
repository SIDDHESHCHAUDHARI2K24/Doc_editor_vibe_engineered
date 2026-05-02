import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

interface Toast {
  id: number
  message: string
  type: 'error' | 'success' | 'warning'
}

interface ToastContextType {
  toast: {
    error: (message: string) => void
    success: (message: string) => void
    warning: (message: string) => void
  }
}

const ToastContext = createContext<ToastContextType | null>(null)

let nextId = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const add = useCallback((message: string, type: Toast['type']) => {
    const id = nextId++
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 5000)
  }, [])

  const dismiss = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const value: ToastContextType = {
    toast: {
      error: (msg: string) => add(msg, 'error'),
      success: (msg: string) => add(msg, 'success'),
      warning: (msg: string) => add(msg, 'warning'),
    },
  }

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map(t => (
          <div
            key={t.id}
            onClick={() => dismiss(t.id)}
            className={`px-4 py-3 rounded-lg shadow-lg text-sm font-medium cursor-pointer max-w-sm
              ${t.type === 'error' ? 'bg-red-600 text-white' : ''}
              ${t.type === 'success' ? 'bg-green-600 text-white' : ''}
              ${t.type === 'warning' ? 'bg-yellow-500 text-white' : ''}`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
