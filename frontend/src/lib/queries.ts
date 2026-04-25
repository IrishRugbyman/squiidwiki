import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import type {
  AllianceListItem,
  AllianceRead,
  AllianceReadDetail,
  AuditLogRead,
  CursorPage,
  GlobalRole,
  IncidentListItem,
  UniverseAnalytics,
  IncidentRead,
  IncidentReadDetail,
  MemberListItem,
  MemberRead,
  MemberReadDetail,
  MemberStats,
  MunicipalityGeoJSON,
  MunicipalityListItem,
  MunicipalityRead,
  OffsetPage,
  ResearchNoteListItem,
  ResearchNoteRead,
  SetListItem,
  SetRead,
  SetReadDetail,
  SetStats,
  SourceListItem,
  SourceRead,
  UserListItem,
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

export const useUpdateUniverse = (id: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { name?: string; slug?: string; description?: string | null }) =>
      api.patch<{ id: UUID; name: string; slug: string; description: string | null }>(`/universes/${id}`, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['universes'] }) },
  })
}

export const useDeleteUniverse = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/universes/${id}`),
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

export const useAllSets = (universeId: UUID | null) =>
  useQuery({
    queryKey: ['sets', 'all', universeId],
    queryFn: () => api.get<OffsetPage<SetListItem>>(`/sets/?universe_id=${universeId}&limit=200`),
    enabled: !!universeId,
    staleTime: 30_000,
  })

export const useSetSearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['sets', 'search', universeId, q],
    queryFn: () => api.get<SetListItem[]>(`/sets/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
    enabled: !!universeId && q.length >= 2,
  })

export const useAllianceSearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['alliances', 'search', universeId, q],
    queryFn: () => api.get<AllianceListItem[]>(`/alliances/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
    enabled: !!universeId && q.length >= 2,
  })

export const useIncidentSearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['incidents', 'search', universeId, q],
    queryFn: () => api.get<IncidentListItem[]>(`/incidents/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
    enabled: !!universeId && q.length >= 2,
  })

export const useSourceSearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['sources', 'search', universeId, q],
    queryFn: () => api.get<SourceListItem[]>(`/sources/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
    enabled: !!universeId && q.length >= 2,
  })

export const useMunicipalitySearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['municipalities', 'search', universeId, q],
    queryFn: () => api.get<MunicipalityListItem[]>(`/municipalities/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
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
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['sets', data.universe_id] })
      qc.invalidateQueries({ queryKey: ['alliances'] })
    },
  })
}

export const useUpdateSet = (id: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.patch<SetRead>(`/sets/${id}?universe_id=${body.universe_id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets', id] })
      qc.invalidateQueries({ queryKey: ['sets'] })
      qc.invalidateQueries({ queryKey: ['alliances'] })
    },
  })
}

export const useDeleteSet = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/sets/${id}?universe_id=${universeId}`),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ['sets', universeId] })
      const prev = qc.getQueriesData({ queryKey: ['sets', universeId] })
      qc.setQueriesData({ queryKey: ['sets', universeId] }, (old: any) =>
        old?.items ? { ...old, items: old.items.filter((s: any) => s.id !== id), total: Math.max(0, (old.total ?? 1) - 1) } : old
      )
      return { prev }
    },
    onError: (_e, _id, ctx: any) => { if (ctx?.prev) qc.setQueriesData({ queryKey: ['sets', universeId] }, ctx.prev) },
    onSettled: () => { qc.invalidateQueries({ queryKey: ['sets'] }) },
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

export const useAllianceMembers = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', 'alliance', id],
    queryFn: () => api.get<CursorPage<MemberListItem>>(`/alliances/${id}/members?universe_id=${universeId}`),
    enabled: !!universeId && !!id,
  })

export const useAllianceIncidents = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', 'alliance', id],
    queryFn: () => api.get<CursorPage<IncidentListItem>>(`/alliances/${id}/incidents?universe_id=${universeId}`),
    enabled: !!universeId && !!id,
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

export const useAllMembers = (universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', 'all', universeId],
    queryFn: () => api.get<CursorPage<MemberListItem>>(`/members/?universe_id=${universeId}&limit=200`),
    enabled: !!universeId,
    staleTime: 30_000,
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
    enabled: !!universeId && !!id,
  })

export const useCreateMember = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<MemberRead>('/members/', body),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['members', data.universe_id] })
      qc.invalidateQueries({ queryKey: ['members'] })
    },
  })
}

export const useReassignMembersToSet = (setId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (memberIds: UUID[]) => {
      await Promise.all(
        memberIds.map((id) =>
          api.patch<MemberRead>(`/members/${id}?universe_id=${universeId}`, { set_id: setId }),
        ),
      )
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['members'] })
      qc.invalidateQueries({ queryKey: ['sets', setId, 'stats'] })
    },
  })
}

export const useReassignMembersToAlliance = (allianceId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (memberIds: UUID[]) => {
      await Promise.all(
        memberIds.map((id) =>
          api.patch<MemberRead>(`/members/${id}?universe_id=${universeId}`, { alliance_id: allianceId }),
        ),
      )
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['members'] })
      qc.invalidateQueries({ queryKey: ['alliances', allianceId] })
    },
  })
}

export const useReassignSetsToAlliance = (allianceId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (setIds: UUID[]) => {
      await Promise.all(
        setIds.map((id) =>
          api.patch<SetRead>(`/sets/${id}?universe_id=${universeId}`, { universe_id: universeId, alliance_id: allianceId }),
        ),
      )
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets'] })
      qc.invalidateQueries({ queryKey: ['alliances', allianceId] })
    },
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

export const useBulkMemberStatus = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { member_ids: UUID[]; status: string }) =>
      api.post<{ updated: number }>(`/members/bulk-status?universe_id=${universeId}`, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members'] }) },
  })
}

// Single-row status toggles for list tables. Take {id, status} at call time
// so a list page can use one hook for N rows.

export const useUpdateMemberStatus = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: UUID; status: string }) =>
      api.patch<MemberRead>(`/members/${id}?universe_id=${universeId}`, { status }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members'] }) },
  })
}

export const useUpdateSetStatus = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: UUID; status: string }) =>
      api.patch<SetRead>(`/sets/${id}?universe_id=${universeId}`, { universe_id: universeId, status }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sets'] }) },
  })
}

export const useUpdateAllianceStatus = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: UUID; status: string }) =>
      api.patch<AllianceRead>(`/alliances/${id}?universe_id=${universeId}`, { status }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alliances'] }) },
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

export const useAllIncidents = (universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', 'all', universeId],
    queryFn: () => api.get<CursorPage<IncidentListItem>>(`/incidents/?universe_id=${universeId}&limit=200`),
    enabled: !!universeId,
    staleTime: 30_000,
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

export const useUpdateIncident = (id: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.patch<IncidentRead>(`/incidents/${id}?universe_id=${universeId}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['incidents', id] })
      qc.invalidateQueries({ queryKey: ['incidents'] })
    },
  })
}

export const useDeleteIncident = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/incidents/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['incidents'] }) },
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

export const useSourceIncidents = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', 'source', id],
    queryFn: () => api.get<CursorPage<IncidentListItem>>(`/sources/${id}/incidents?universe_id=${universeId}`),
    enabled: !!universeId && !!id,
  })

export const useSourceMembers = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', 'source', id],
    queryFn: () => api.get<CursorPage<MemberListItem>>(`/sources/${id}/members?universe_id=${universeId}`),
    enabled: !!universeId && !!id,
  })

export const useCreateSource = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<SourceRead>('/sources/', body),
    onSuccess: (data) => { qc.invalidateQueries({ queryKey: ['sources', data.universe_id] }) },
  })
}

export const useUpdateSource = (id: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.patch<SourceRead>(`/sources/${id}?universe_id=${universeId}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sources', id] })
      qc.invalidateQueries({ queryKey: ['sources'] })
    },
  })
}

export const useDeleteSource = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/sources/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sources'] }) },
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

export const useMunicipalityGeoJSON = (universeId: UUID | null) =>
  useQuery({
    queryKey: ['municipalities', universeId, 'geojson'],
    queryFn: () => api.get<MunicipalityGeoJSON>(`/municipalities/geojson?universe_id=${universeId}`),
    enabled: !!universeId,
    staleTime: 60_000,
  })

export const useMunicipality = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['municipalities', id],
    queryFn: () => api.get<MunicipalityRead>(`/municipalities/${id}?universe_id=${universeId}`),
    enabled: !!universeId,
  })

export const useIncidentsByMunicipality = (municipalityId: UUID | null, universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', 'municipality', municipalityId, universeId],
    queryFn: () =>
      api.get<CursorPage<IncidentListItem>>(
        `/incidents/?universe_id=${universeId}&municipality_id=${municipalityId}`
      ),
    enabled: !!municipalityId && !!universeId,
  })

export const useCreateMunicipality = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<MunicipalityRead>('/municipalities/', body),
    onSuccess: (data) => { qc.invalidateQueries({ queryKey: ['municipalities', data.universe_id] }) },
  })
}

export const useUpdateMunicipality = (id: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.patch<MunicipalityRead>(`/municipalities/${id}?universe_id=${universeId}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['municipalities', id] })
      qc.invalidateQueries({ queryKey: ['municipalities'] })
    },
  })
}

export const useDeleteMunicipality = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/municipalities/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['municipalities'] }) },
  })
}

// ─── Research notes ───────────────────────────────────────────────────────────

export const useResearchNotes = (universeId: UUID | null, offset = 0) =>
  useQuery({
    queryKey: ['research', universeId, offset],
    queryFn: () =>
      api.get<OffsetPage<ResearchNoteListItem>>(`/research/?universe_id=${universeId}&offset=${offset}`),
    enabled: !!universeId,
  })

export const useResearchNote = (id: UUID, universeId: UUID | null) =>
  useQuery({
    queryKey: ['research', id],
    queryFn: () => api.get<ResearchNoteRead>(`/research/${id}?universe_id=${universeId}`),
    enabled: !!universeId && !!id,
  })

export const useResearchSearch = (universeId: UUID | null, q: string) =>
  useQuery({
    queryKey: ['research', 'search', universeId, q],
    queryFn: () => api.get<ResearchNoteListItem[]>(`/research/search?universe_id=${universeId}&q=${encodeURIComponent(q)}`),
    enabled: !!universeId && q.length >= 2,
  })

export const useCreateResearchNote = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { universe_id: UUID; title: string; content: string }) =>
      api.post<ResearchNoteRead>('/research/', body),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['research', data.universe_id] })
      qc.invalidateQueries({ queryKey: ['research'] })
    },
  })
}

export const useUpdateResearchNote = (id: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { title?: string; content?: string }) =>
      api.patch<ResearchNoteRead>(`/research/${id}?universe_id=${universeId}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['research', id] })
      qc.invalidateQueries({ queryKey: ['research'] })
    },
  })
}

export const useDeleteResearchNote = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/research/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['research'] }) },
  })
}

// ─── Audit ────────────────────────────────────────────────────────────────────

export const useAuditLogs = (filters: {
  offset?: number
  entity_type?: string
  user_id?: string
  action?: string
} = {}) =>
  useQuery({
    queryKey: ['audit', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.offset) params.set('offset', String(filters.offset))
      if (filters.entity_type) params.set('entity_type', filters.entity_type)
      if (filters.user_id) params.set('user_id', filters.user_id)
      if (filters.action) params.set('action', filters.action)
      return api.get<OffsetPage<AuditLogRead>>(`/audit/?${params}`)
    },
    staleTime: 10_000,
  })

// ─── Users (admin) ────────────────────────────────────────────────────────────

export const useUsers = (offset = 0) =>
  useQuery({
    queryKey: ['users', offset],
    queryFn: () => api.get<OffsetPage<UserListItem>>(`/auth/users?offset=${offset}`),
    staleTime: 30_000,
  })

export const useUpdateUserRole = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: GlobalRole }) =>
      api.patch<UserListItem>(`/auth/users/${userId}/role`, { global_role: role }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }) },
  })
}

// ─── DB mode ──────────────────────────────────────────────────────────────────

export type DbMode = 'prod' | 'test'

export const useDbMode = () =>
  useQuery({
    queryKey: ['db-mode'],
    queryFn: () => api.get<{ mode: DbMode }>('/admin/db-mode'),
    staleTime: Infinity,
  })

export const useSetDbMode = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (mode: DbMode) =>
      api.post<{ mode: DbMode }>(`/admin/db-mode?mode=${mode}`, {}),
    onSuccess: () => qc.invalidateQueries(),
  })
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export const useUniverseAnalytics = (universeId: UUID | null) =>
  useQuery({
    queryKey: ['analytics', universeId],
    queryFn: () => api.get<UniverseAnalytics>(`/universes/${universeId}/analytics`),
    enabled: !!universeId,
    staleTime: 60_000,
  })
