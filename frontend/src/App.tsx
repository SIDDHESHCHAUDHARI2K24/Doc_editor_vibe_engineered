import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/features/auth/AuthContext'
import { ToastProvider } from '@/components/ui/ToastContext'
import { LoginForm } from '@/features/auth/LoginForm'
import { Dashboard } from '@/features/dashboard/DocumentList'
import { EditorPage } from '@/features/editor/EditorPage'
import { Spinner } from '@/components/ui/Spinner'

function ProtectedRoute() {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}

function UnauthenticatedRoute() {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner />
      </div>
    )
  }
  if (user) return <Navigate to="/dashboard" replace />
  return <Outlet />
}

function AppRoutes() {
  return (
    <Routes>
      <Route element={<UnauthenticatedRoute />}>
        <Route path="/login" element={<LoginForm />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/documents/:docId" element={<EditorPage />} />
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
