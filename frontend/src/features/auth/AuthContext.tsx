import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import type { UserResponse } from '@/types/api'
import { getMeApi, loginApi, logoutApi } from './api'

interface AuthState {
  user: UserResponse | null
  loading: boolean
  csrfToken: string | null
}

interface AuthContextType extends AuthState {
  login: (identifier: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    csrfToken: null,
  })

  useEffect(() => {
    getMeApi()
      .then(data => {
        setState({ user: data.user, loading: false, csrfToken: data.csrf_token })
      })
      .catch(() => {
        setState({ user: null, loading: false, csrfToken: null })
      })
  }, [])

  const login = useCallback(async (identifier: string, password: string) => {
    const data = await loginApi({ identifier, password })
    setState(prev => ({ ...prev, user: data.user }))
    const csrf = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/)?.[1] || null
    setState(prev => ({ ...prev, csrfToken: csrf }))
  }, [])

  const logout = useCallback(async () => {
    await logoutApi()
    setState({ user: null, loading: false, csrfToken: null })
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
