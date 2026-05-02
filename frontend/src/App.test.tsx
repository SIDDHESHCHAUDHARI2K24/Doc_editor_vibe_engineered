import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '@/App'

beforeEach(() => {
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('not authed'))
})

describe('App', () => {
  it('renders without crashing and shows LoginForm', async () => {
    render(<App />)
    expect(await screen.findByText('Use one of the demo accounts to sign in')).toBeDefined()
  })
})
