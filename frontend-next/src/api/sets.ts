import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface Set {
  id: number
  name: string
  type: string
  description: string | null
  emoji: string | null
  universe_id: number | null
  founded_date: object | null
  founded_date_sortable: string | null
}

export const setKeys = {
  all: (universeId?: number) => ['sets', universeId] as const,
  detail: (id: number) => ['sets', 'detail', id] as const,
}

export function useSets(universeId?: number) {
  return useQuery({
    queryKey: setKeys.all(universeId),
    queryFn: () => {
      const q = universeId ? `?universe_id=${universeId}` : ''
      return apiFetch<Set[]>(`/sets/api${q}`)
    },
  })
}

export function useSet(id: number) {
  return useQuery({
    queryKey: setKeys.detail(id),
    queryFn: () => apiFetch<Set>(`/sets/api/${id}`),
    enabled: !!id,
  })
}

export function useCreateSet() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Set>) =>
      apiFetch<Set>('/sets/api', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sets'] }),
  })
}

export function useUpdateSet(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Set>) =>
      apiFetch<Set>(`/sets/api/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets'] })
      qc.invalidateQueries({ queryKey: setKeys.detail(id) })
    },
  })
}

export function useDeleteSet(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch(`/sets/api/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sets'] }),
  })
}
