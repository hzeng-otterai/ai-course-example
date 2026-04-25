import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { vi } from 'vitest'
import ProtectedRoute from './ProtectedRoute'

const { mockUseAuth } = vi.hoisted(() => ({ mockUseAuth: vi.fn() }))

vi.mock('../contexts/AuthContext', () => ({ useAuth: mockUseAuth }))

describe('ProtectedRoute', () => {
  it('shows loading indicator while auth is resolving', () => {
    mockUseAuth.mockReturnValue({ user: null, loading: true })
    render(
      <MemoryRouter>
        <ProtectedRoute><div>Protected Content</div></ProtectedRoute>
      </MemoryRouter>
    )
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when user is authenticated', () => {
    mockUseAuth.mockReturnValue({ user: { id: 1, username: 'alice' }, loading: false })
    render(
      <MemoryRouter>
        <ProtectedRoute><div>Protected Content</div></ProtectedRoute>
      </MemoryRouter>
    )
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('redirects to /login when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({ user: null, loading: false })
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route
            path="/dashboard"
            element={<ProtectedRoute><div>Protected Content</div></ProtectedRoute>}
          />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })
})
