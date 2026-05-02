import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '@/App'

beforeEach(() => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(
    vi.fn((input: RequestInfo | URL) => {
      const url = input.toString()
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            status: url.includes('localhost:8000') ? 'ok-direct' : 'ok-proxied',
          }),
      } as Response)
    }),
  )
})

describe('App', () => {
  it('renders the health check heading', async () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: /document editor.*health check/i,
      }),
    ).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    render(<App />)
    expect(screen.getByText(/checking backend health/i)).toBeInTheDocument()
  })
})
