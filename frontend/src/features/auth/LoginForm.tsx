import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { ApiError } from '@/lib/api/apiClient'

export function LoginForm() {
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await login(identifier, password)
      navigate('/dashboard')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === 'RATE_LIMITED') {
          const retryAfter = (err.details as any)?.retry_after
          setError(`Too many attempts. Try again in ${retryAfter ? Math.ceil(Number(retryAfter)) : 'a few'} seconds.`)
        } else {
          setError(err.message)
        }
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Sign in</h1>
        <p className="text-sm text-gray-500 mb-6">Use one of the demo accounts to sign in</p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email or username"
            type="text"
            value={identifier}
            onChange={e => setIdentifier(e.target.value)}
            placeholder="alice@example.com"
            required
            autoFocus
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password123!"
            required
          />
          <Button type="submit" isLoading={isLoading} className="w-full">
            Sign in
          </Button>
        </form>
      </div>
    </div>
  )
}
