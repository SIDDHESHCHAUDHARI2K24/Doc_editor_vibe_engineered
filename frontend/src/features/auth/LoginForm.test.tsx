import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { LoginForm } from './LoginForm'
import { AuthProvider } from './AuthContext'

vi.mock('./api', () => ({
  loginApi: vi.fn(),
  logoutApi: vi.fn(),
  getMeApi: vi.fn().mockRejectedValue(new Error('not authed')),
}))

function renderLoginForm() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginForm />
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign in header', () => {
    renderLoginForm()
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
  })

  it('has email/username and password inputs', () => {
    renderLoginForm()
    expect(screen.getByLabelText('Email or username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
  })

  it('shows error message on failed login', async () => {
    const { loginApi } = await import('./api')
    const { ApiError } = await import('@/lib/api/apiClient')
    vi.mocked(loginApi).mockRejectedValue(
      new ApiError('INVALID_CREDENTIALS', 'Invalid credentials')
    )

    renderLoginForm()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Email or username'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
  })
})
