import { create } from 'zustand'

export type GlobalRole = 'ADMIN' | 'USER'

export interface AuthUser {
  id: string
  email: string
  global_role: GlobalRole
}

interface AuthState {
  user: AuthUser | null
  accessToken: string | null
  setAuth: (user: AuthUser, token: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: localStorage.getItem('access_token'),
  setAuth: (user, token) => {
    localStorage.setItem('access_token', token)
    set({ user, accessToken: token })
  },
  clearAuth: () => {
    localStorage.removeItem('access_token')
    set({ user: null, accessToken: null })
  },
}))
