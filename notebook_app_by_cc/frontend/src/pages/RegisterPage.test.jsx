import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import RegisterPage from './RegisterPage'

const { mockNavigate, mockRegister } = vi.hoisted(() => ({
  mockNavigate: vi.fn(),
  mockRegister: vi.fn(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ register: mockRegister }),
}))

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders username, email, and password fields with a create-account button', () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>)
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('navigates to / on successful registration', async () => {
    mockRegister.mockResolvedValue({ id: 2, username: 'newuser' })
    const { container } = render(<MemoryRouter><RegisterPage /></MemoryRouter>)

    fireEvent.change(container.querySelector('input[type="text"]'), {
      target: { value: 'newuser' },
    })
    fireEvent.change(container.querySelector('input[type="password"]'), {
      target: { value: 'password123' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /create account/i }).closest('form'))

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'))
    expect(mockRegister).toHaveBeenCalledWith(
      expect.objectContaining({ username: 'newuser', password: 'password123' })
    )
  })

  it('displays field-level errors from the server response', async () => {
    mockRegister.mockRejectedValue({
      response: { data: { username: ['A user with that username already exists.'] } },
    })
    const { container } = render(<MemoryRouter><RegisterPage /></MemoryRouter>)

    fireEvent.change(container.querySelector('input[type="text"]'), {
      target: { value: 'taken' },
    })
    fireEvent.change(container.querySelector('input[type="password"]'), {
      target: { value: 'password123' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /create account/i }).closest('form'))

    await waitFor(() =>
      expect(
        screen.getByText('A user with that username already exists.')
      ).toBeInTheDocument()
    )
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('displays a generic error message when response has no data', async () => {
    mockRegister.mockRejectedValue(new Error('Network error'))
    const { container } = render(<MemoryRouter><RegisterPage /></MemoryRouter>)

    fireEvent.change(container.querySelector('input[type="text"]'), {
      target: { value: 'user' },
    })
    fireEvent.change(container.querySelector('input[type="password"]'), {
      target: { value: 'password123' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /create account/i }).closest('form'))

    await waitFor(() =>
      expect(
        screen.getByText('Registration failed. Please try again.')
      ).toBeInTheDocument()
    )
  })

  it('disables submit button while registration is in progress', async () => {
    let resolve
    mockRegister.mockReturnValue(new Promise((r) => { resolve = r }))
    const { container } = render(<MemoryRouter><RegisterPage /></MemoryRouter>)

    fireEvent.change(container.querySelector('input[type="text"]'), {
      target: { value: 'user' },
    })
    fireEvent.change(container.querySelector('input[type="password"]'), {
      target: { value: 'password123' },
    })
    fireEvent.submit(screen.getByRole('button', { name: /create account/i }).closest('form'))

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled()
    )
    resolve({ id: 1, username: 'user' })
  })

  it('has a link back to the login page', () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>)
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login')
  })
})
