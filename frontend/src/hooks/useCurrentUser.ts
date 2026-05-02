import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AuthUser } from '@/stores/auth'
import { useAuthStore } from '@/stores/auth'

export function useCurrentUser() {
  const accessToken = useAuthStore((s) => s.accessToken)

  return useQuery<AuthUser>({
    queryKey: ['auth', 'me'],
    queryFn: () => api.get<AuthUser>('/auth/me'),
    enabled: !!accessToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}
