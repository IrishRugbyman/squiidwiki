import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AuthUser } from '@/stores/auth'
import { useAuthStore } from '@/stores/auth'

export function useCurrentUser() {
  const { accessToken, setAuth, clearAuth } = useAuthStore()

  return useQuery<AuthUser>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const user = await api.get<AuthUser>('/auth/me')
      return user
    },
    enabled: !!accessToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}
