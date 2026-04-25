import { render, screen, waitFor, act } from '@testing-library/react'
import { vi } from 'vitest'
import { AuthProvider, useAuth } from './AuthContext'

const { mockApiLogin, mockApiRegister, mockGetMe } = vi.hoisted(() => ({
  mockApiLogin: vi.fn(),
  mockApiRegister: vi.fn(),
  mockGetMe: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  login: mockApiLogin,
  register: mockApiRegister,
  getMe: mockGetMe,
}))

function TestConsumer() {
  const { user, loading, login, logout, register } = useAuth()
  return (
    <div>
      <span data-testid="loading">{loading ? 'loading' : 'ready'}</span>
      <span data-testid="user">{user ? user.username : 'no-user'}</span>
      <button onClick={() => login({ username: 'u', password: 'p' })}>Login</button>
      <button onClick={() => register({ username: 'u', password: 'p' })}>Register</button>
      <button onClick={logout}>Logout</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('finishes loading with no user when localStorage has no token', async () => {
    render(<AuthProvider><TestConsumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'))
    expect(screen.getByTestId('user')).toHaveTextContent('no-user')
  })

  it('hydrates user from stored access token on mount', async () => {
    localStorage.setItem('access', 'stored-token')
    mockGetMe.mockResolvedValue({ data: { id: 1, username: 'storeduser' } })

    render(<AuthProvider><TestConsumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('storeduser'))
    expect(screen.getByTestId('loading')).toHaveTextContent('ready')
  })

  it('clears tokens and sets no user when token hydration fails', async () => {
    localStorage.setItem('access', 'bad-token')
    localStorage.setItem('refresh', 'bad-refresh')
    mockGetMe.mockRejectedValue(new Error('401'))

    render(<AuthProvider><TestConsumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'))

    expect(screen.getByTestId('user')).toHaveTextContent('no-user')
    expect(localStorage.getItem('access')).toBeNull()
    expect(localStorage.getItem('refresh')).toBeNull()
  })

  it('sets user and stores tokens after login', async () => {
    mockApiLogin.mockResolvedValue({ data: { access: 'new-access', refresh: 'new-refresh' } })
    mockGetMe
      .mockResolvedValueOnce(new Promise(() => {})) // mount hydration (no token, skipped)
      .mockResolvedValue({ data: { id: 1, username: 'loginuser' } })

    render(<AuthProvider><TestConsumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'))

    await act(async () => {
      screen.getByText('Login').click()
    })

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('loginuser'))
    expect(localStorage.getItem('access')).toBe('new-access')
    expect(localStorage.getItem('refresh')).toBe('new-refresh')
  })

  it('sets user and stores tokens after register', async () => {
    mockApiRegister.mockResolvedValue({
      data: {
        access: 'reg-access',
        refresh: 'reg-refresh',
        user: { id: 2, username: 'newuser' },
      },
    })

    render(<AuthProvider><TestConsumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'))

    await act(async () => {
      screen.getByText('Register').click()
    })

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('newuser'))
    expect(localStorage.getItem('access')).toBe('reg-access')
  })

  it('clears user and tokens on logout', async () => {
    localStorage.setItem('access', 'token')
    localStorage.setItem('refresh', 'refresh-token')
    mockGetMe.mockResolvedValue({ data: { id: 1, username: 'user1' } })

    render(<AuthProvider><TestConsumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('user1'))

    act(() => {
      screen.getByText('Logout').click()
    })

    expect(screen.getByTestId('user')).toHaveTextContent('no-user')
    expect(localStorage.getItem('access')).toBeNull()
    expect(localStorage.getItem('refresh')).toBeNull()
  })
})
