import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  accessToken: string | null
  username: string | null
  isAdmin: boolean
  setAuth: (accessToken: string, username: string, isAdmin: boolean) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      username: null,
      isAdmin: false,
      setAuth: (accessToken, username, isAdmin) =>
        set({ accessToken, username, isAdmin }),
      clearAuth: () => set({ accessToken: null, username: null, isAdmin: false }),
      isAuthenticated: () => get().accessToken !== null,
    }),
    { name: 'squiidwiki-auth' },
  ),
)
