import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface Alliance {
  id: number
  name: string
  status: string
  description: string | null
  universe_id: number | null
  formed_date: string | null
}

export const allianceKeys = {
  all: (universeId?: number) => ['alliances', universeId] as const,
  detail: (id: number) => ['alliances', 'detail', id] as const,
}

export function useAlliances(universeId?: number) {
  return useQuery({
    queryKey: allianceKeys.all(universeId),
    queryFn: () => {
      const q = universeId ? `?universe_id=${universeId}` : ''
      return apiFetch<Alliance[]>(`/alliances/api${q}`)
    },
  })
}

export function useAlliance(id: number) {
  return useQuery({
    queryKey: allianceKeys.detail(id),
    queryFn: () => apiFetch<Alliance>(`/alliances/api/${id}`),
    enabled: !!id,
  })
}

export function useCreateAlliance() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Alliance>) =>
      apiFetch<Alliance>('/alliances/api', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alliances'] }),
  })
}

export function useDeleteAlliance(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch(`/alliances/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alliances'] }),
  })
}
