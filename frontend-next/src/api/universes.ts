import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface Universe {
  id: number
  name: string
  slug: string
}

export const universeKeys = {
  all: ['universes'] as const,
  detail: (slug: string) => ['universes', slug] as const,
}

export function useUniverses() {
  return useQuery({
    queryKey: universeKeys.all,
    queryFn: () => apiFetch<Universe[]>('/universes/'),
  })
}

export function useCreateUniverse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; slug: string }) =>
      apiFetch<Universe>('/universes/', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: universeKeys.all }),
  })
}
