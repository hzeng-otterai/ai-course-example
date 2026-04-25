import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import LoginPage from './LoginPage'

const { mockNavigate, mockLogin } = vi.hoisted(() => ({
  mockNavigate: vi.fn(),
  mockLogin: vi.fn(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ login: mockLogin }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders username and password fields with a sign-in button', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('navigates to / on successful login', async () => {
    mockLogin.mockResolvedValue({ id: 1, username: 'alice' })
    const { container } = render(<MemoryRouter><LoginPage /></MemoryRouter>)

    fireEvent.change(container.querySelector('input[type="text"]'), {
      target: { value: 'alice' },
    })
    fireEvent.change(container.querySelector('input[type="password"]'), {
      target: { value: 'password123' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }).closest('form'))

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'))
    expect(mockLogin).toHaveBeenCalledWith({ username: 'alice', password: 'password123' })
  })

  it('shows error message on login failure', async () => {
    mockLogin.mockRejectedValue(new Error('Unauthorized'))
    const { container } = render(<MemoryRouter><LoginPage /></MemoryRouter>)

    fireEvent.change(container.querySelector('input[type="text"]'), {
      target: { value: 'alice' },
    })
    fireEvent.change(container.querySelector('input[type="password"]'), {
      target: { value: 'wrong' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }).closest('form'))

    await waitFor(() =>
      expect(screen.getByText('Invalid username or password.')).toBeInTheDocument()
    )
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('disables submit button while login is in progress', async () => {
    let resolve
    mockLogin.mockReturnValue(new Promise((r) => { resolve = r }))
    const { container } = render(<MemoryRouter><LoginPage /></MemoryRouter>)

    fireEvent.change(container.querySelector('input[type="text"]'), {
      target: { value: 'alice' },
    })
    fireEvent.change(container.querySelector('input[type="password"]'), {
      target: { value: 'password' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }).closest('form'))

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
    )
    resolve({ id: 1, username: 'alice' })
  })

  it('has a link to the register page', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByRole('link', { name: /create one/i })).toHaveAttribute('href', '/register')
  })
})
