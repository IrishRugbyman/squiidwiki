import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface IncidentParticipant {
  id: number
  member_id: number
  role: string
  outcome: string
}

export interface Incident {
  id: number
  incident_type: string
  date: object | null
  date_sortable: string | null
  location_type: string
  narrative: string | null
  verified: boolean
  universe_id: number | null
  participants: IncidentParticipant[]
}

export const incidentKeys = {
  all: (universeId?: number) => ['incidents', universeId] as const,
  detail: (id: number) => ['incidents', 'detail', id] as const,
}

export function useIncidents(universeId?: number) {
  return useQuery({
    queryKey: incidentKeys.all(universeId),
    queryFn: () => {
      const q = universeId ? `?universe_id=${universeId}` : ''
      return apiFetch<Incident[]>(`/incidents/${q}`)
    },
  })
}

export function useIncident(id: number) {
  return useQuery({
    queryKey: incidentKeys.detail(id),
    queryFn: () => apiFetch<Incident>(`/incidents/${id}`),
    enabled: !!id,
  })
}

export function useCreateIncident() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Incident>) =>
      apiFetch<Incident>('/incidents/', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incidents'] }),
  })
}

export function useDeleteIncident(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch(`/incidents/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incidents'] }),
  })
}
