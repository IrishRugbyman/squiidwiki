import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import type {
  AllianceListItem,
  AllianceRead,
  AllianceReadDetail,
  CursorPage,
  IncidentListItem,
  IncidentRead,
  IncidentReadDetail,
  MemberListItem,
  MemberRead,
  MemberReadDetail,
  MemberStats,
  MunicipalityListItem,
  MunicipalityRead,
  OffsetPage,
  SetListItem,
  SetRead,
  SetReadDetail,
  SetStats,
  SourceListItem,
  SourceRead,
  UUID,
} from './types'

// ─── Universe ────────────────────────────────────────────────────────────────

export const useUniverses = () =>
  useQuery({
    queryKey: ['universes'],
    queryFn: () => api.get<OffsetPage<{ id: UUID; name: string; slug: string }>>('/universes/'),
    staleTime: 60_000,
  })

export const useCreateUniverse = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { name: string; slug: string; description?: string | null }) =>
      api.post<{ id: UUID; name: string; slug: string; description: string | null }>('/universes/', body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['universes'] }) },
  })
}

// ─── Sets ─────────────────────────────────────────────────────────────────────

export const useSets = (universeId: UUID | null, offset = 0) =>
  useQuery({
    queryKey: ['sets', universeId, offset],
    queryFn: () => api.get<OffsetPage<SetListItem>>(`/sets/?universe_id=${universeId}&offset=${offset}`),
    enabled: !!universeId,
  })

export const useSetSearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['sets', 'search', universeId, q],
    queryFn: () => api.get<SetListItem[]>(`/sets/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
    enabled: !!universeId && q.length >= 2,
  })

export const useSet = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['sets', id],
    queryFn: () => api.get<SetReadDetail>(`/sets/${id}?universe_id=${universeId}`),
    enabled: !!universeId,
  })

export const useSetStats = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['sets', id, 'stats'],
    queryFn: () => api.get<SetStats>(`/sets/${id}/stats?universe_id=${universeId}`),
    enabled: !!universeId && !!id,
  })

export const useCreateSet = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<SetRead>('/sets/', body),
    onSuccess: (data) => { qc.invalidateQueries({ queryKey: ['sets', data.universe_id] }) },
  })
}

export const useUpdateSet = (id: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.patch<SetRead>(`/sets/${id}?universe_id=${body.universe_id}`, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sets', id] }) },
  })
}

export const useDeleteSet = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/sets/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sets', universeId] }) },
  })
}

export const useAddSetRelationship = (setId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { target_id: UUID; type: string }) =>
      api.post(`/sets/${setId}/relationships?universe_id=${universeId}`, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sets', setId] }) },
  })
}

export const useRemoveSetRelationship = (setId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (targetId: UUID) =>
      api.delete(`/sets/${setId}/relationships/${targetId}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sets', setId] }) },
  })
}

export const useSetMembers = (setId: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', 'set', setId],
    queryFn: () => api.get<CursorPage<MemberListItem>>(`/members/?universe_id=${universeId}&set_id=${setId}`),
    enabled: !!universeId && !!setId,
  })

export const useSetIncidents = (setId: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', 'set', setId],
    queryFn: () => api.get<CursorPage<IncidentListItem>>(`/incidents/?universe_id=${universeId}&set_id=${setId}`),
    enabled: !!universeId && !!setId,
  })

// ─── Alliances ────────────────────────────────────────────────────────────────

export const useAlliances = (universeId: UUID | null, offset = 0) =>
  useQuery({
    queryKey: ['alliances', universeId, offset],
    queryFn: () => api.get<OffsetPage<AllianceListItem>>(`/alliances/?universe_id=${universeId}&offset=${offset}`),
    enabled: !!universeId,
  })

export const useAlliance = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['alliances', id],
    queryFn: () => api.get<AllianceReadDetail>(`/alliances/${id}?universe_id=${universeId}`),
    enabled: !!universeId,
  })

export const useCreateAlliance = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<AllianceRead>('/alliances/', body),
    onSuccess: (data) => { qc.invalidateQueries({ queryKey: ['alliances', data.universe_id] }) },
  })
}

export const useUpdateAlliance = (id: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.patch<AllianceRead>(`/alliances/${id}?universe_id=${universeId}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alliances', id] })
      qc.invalidateQueries({ queryKey: ['alliances'] })
    },
  })
}

export const useDeleteAlliance = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/alliances/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alliances'] }) },
  })
}

// ─── Members ──────────────────────────────────────────────────────────────────

export const useMembers = (universeId: UUID | null, cursor?: string) =>
  useQuery({
    queryKey: ['members', universeId, cursor],
    queryFn: () => {
      const qs = cursor ? `?universe_id=${universeId}&cursor=${cursor}` : `?universe_id=${universeId}`
      return api.get<CursorPage<MemberListItem>>(`/members/${qs}`)
    },
    enabled: !!universeId,
  })

export const useMemberSearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['members', 'search', universeId, q],
    queryFn: () => api.get<MemberListItem[]>(`/members/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
    enabled: !!universeId && q.length >= 2,
  })

export const useMember = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', id],
    queryFn: () => api.get<MemberReadDetail>(`/members/${id}?universe_id=${universeId}`),
    enabled: !!universeId,
  })

export const useMemberStats = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', id, 'stats'],
    queryFn: () => api.get<MemberStats>(`/members/${id}/stats?universe_id=${universeId}`),
    enabled: !!universeId,
  })

export const useCreateMember = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<MemberRead>('/members/', body),
    onSuccess: (data) => { qc.invalidateQueries({ queryKey: ['members', data.universe_id] }) },
  })
}

export const useUpdateMember = (id: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.patch<MemberRead>(`/members/${id}?universe_id=${universeId}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['members', id] })
      qc.invalidateQueries({ queryKey: ['members'] })
    },
  })
}

export const useDeleteMember = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/members/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members'] }) },
  })
}

export const useMemberIncidents = (memberId: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', 'member', memberId],
    queryFn: () => api.get<CursorPage<IncidentListItem>>(`/incidents/?universe_id=${universeId}&member_id=${memberId}`),
    enabled: !!universeId,
  })

// ─── Incidents ────────────────────────────────────────────────────────────────

export const useIncidents = (universeId: UUID | null, cursor?: string) =>
  useQuery({
    queryKey: ['incidents', universeId, cursor],
    queryFn: () => {
      const qs = cursor ? `?universe_id=${universeId}&cursor=${cursor}` : `?universe_id=${universeId}`
      return api.get<CursorPage<IncidentListItem>>(`/incidents/${qs}`)
    },
    enabled: !!universeId,
  })

export const useIncident = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', id],
    queryFn: () => api.get<IncidentReadDetail>(`/incidents/${id}?universe_id=${universeId}`),
    enabled: !!universeId,
  })

export const useCreateIncident = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<IncidentRead>('/incidents/', body),
    onSuccess: (data) => { qc.invalidateQueries({ queryKey: ['incidents', data.universe_id] }) },
  })
}

// ─── Sources ──────────────────────────────────────────────────────────────────

export const useSources = (universeId: UUID | null, offset = 0) =>
  useQuery({
    queryKey: ['sources', universeId, offset],
    queryFn: () => api.get<OffsetPage<SourceListItem>>(`/sources/?universe_id=${universeId}&offset=${offset}`),
    enabled: !!universeId,
  })

export const useSource = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['sources', id],
    queryFn: () => api.get<SourceRead>(`/sources/${id}?universe_id=${universeId}`),
    enabled: !!universeId,
  })

export const useCreateSource = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<SourceRead>('/sources/', body),
    onSuccess: (data) => { qc.invalidateQueries({ queryKey: ['sources', data.universe_id] }) },
  })
}

// ─── Municipalities ───────────────────────────────────────────────────────────

export const useMunicipalities = (universeId: UUID | null, offset = 0) =>
  useQuery({
    queryKey: ['municipalities', universeId, offset],
    queryFn: () =>
      api.get<OffsetPage<MunicipalityListItem>>(`/municipalities/?universe_id=${universeId}&offset=${offset}`),
    enabled: !!universeId,
  })

export const useMunicipality = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['municipalities', id],
    queryFn: () => api.get<MunicipalityRead>(`/municipalities/${id}?universe_id=${universeId}`),
    enabled: !!universeId,
  })
