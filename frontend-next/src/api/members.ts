import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface Member {
  id: number
  name: string
  status: string
  description: string | null
  set_id: number | null
  universe_id: number | null
  birth_date: object | null
  birth_date_sortable: string | null
  death_date: object | null
  death_date_sortable: string | null
}

export const memberKeys = {
  all: (universeId?: number) => ['members', universeId] as const,
  detail: (id: number) => ['members', 'detail', id] as const,
}

export function useMembers(universeId?: number) {
  return useQuery({
    queryKey: memberKeys.all(universeId),
    queryFn: () => {
      const q = universeId ? `?universe_id=${universeId}` : ''
      return apiFetch<Member[]>(`/members/api${q}`)
    },
  })
}

export function useMember(id: number) {
  return useQuery({
    queryKey: memberKeys.detail(id),
    queryFn: () => apiFetch<Member>(`/members/api/${id}`),
    enabled: !!id,
  })
}

export function useCreateMember() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Member>) =>
      apiFetch<Member>('/members/api', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members'] }),
  })
}

export function useUpdateMember(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Member>) =>
      apiFetch<Member>(`/members/api/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['members'] })
      qc.invalidateQueries({ queryKey: memberKeys.detail(id) })
    },
  })
}

export function useDeleteMember(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch(`/members/api/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members'] }),
  })
}
