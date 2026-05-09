import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { api } from './api'
import type {
  AllianceListItem,
  AllianceRead,
  AllianceReadDetail,
  AuditLogRead,
  CursorPage,
  GangListItem,
  GangRead,
  GlobalRole,
  IncidentListItem,
  UniverseAnalytics,
  IncidentRead,
  IncidentReadDetail,
  MdocProfile,
  MediaEntityType,
  MediaWithUrls,
  MemberAliasRead,
  MemberIncarcerationRead,
  MemberReleaseEvent,
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
  UserUniverseAccessItem,
  UniverseRole,
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

export type SetsListParams = {
  offset?: number
  limit?: number
  q?: string
  status?: 'ACTIVE' | 'EXTINCT'
  /** UUID, or 'none' for unassigned, or omit for no filter. */
  alliance_id?: string | 'none'
  gang_id?: string | 'none'
  municipality_id?: string | 'none'
  sort?: 'name' | 'status' | 'member_count' | 'updated_at' | 'created_at'
  order?: 'asc' | 'desc'
}

function buildSetsQuery(universeId: string, params?: SetsListParams): string {
  const qs = new URLSearchParams({ universe_id: universeId })
  if (params) {
    if (params.offset != null) qs.set('offset', String(params.offset))
    if (params.limit != null) qs.set('limit', String(params.limit))
    if (params.q && params.q.trim().length >= 2) qs.set('q', params.q.trim())
    if (params.status) qs.set('status', params.status)
    if (params.alliance_id) qs.set('alliance_id', params.alliance_id)
    if (params.gang_id) qs.set('gang_id', params.gang_id)
    if (params.municipality_id) qs.set('municipality_id', params.municipality_id)
    if (params.sort) qs.set('sort', params.sort)
    if (params.order) qs.set('order', params.order)
  }
  return qs.toString()
}

/**
 * Backwards-compatible: old callers pass `useSets(universeId)`. New callers can
 * pass an options object with filters/sort/pagination.
 */
export const useSets = (universeId: UUID | null, params?: SetsListParams) =>
  useQuery({
    queryKey: ['sets', universeId, params ?? null],
    queryFn: () => api.get<OffsetPage<SetListItem>>(`/sets/?${buildSetsQuery(universeId!, params)}`),
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

// Restore each cache to its captured pre-mutation value (per-key).
function restoreSnapshot(qc: QueryClient, prev: ReturnType<QueryClient['getQueriesData']>) {
  for (const [key, data] of prev) qc.setQueryData(key, data)
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
    onError: (_e, _id, ctx: any) => { if (ctx?.prev) restoreSnapshot(qc, ctx.prev) },
    onSettled: () => { qc.invalidateQueries({ queryKey: ['sets'] }) },
  })
}

export const useAddSetRelationship = (setId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { target_id: UUID; type: string }) =>
      api.post(`/sets/${setId}/relationships?universe_id=${universeId}`, body),
    onMutate: async ({ target_id, type }) => {
      await qc.cancelQueries({ queryKey: ['sets', setId] })
      const prev = qc.getQueriesData({ queryKey: ['sets', setId] })
      const field = type === 'FRIEND' ? 'friend_ids' : 'enemy_ids'
      qc.setQueriesData({ queryKey: ['sets', setId] }, (old: any) => {
        if (!old || !Array.isArray(old[field])) return old
        if (old[field].includes(target_id)) return old
        return { ...old, [field]: [...old[field], target_id] }
      })
      return { prev }
    },
    onError: (_e, _v, ctx: any) => { if (ctx?.prev) restoreSnapshot(qc, ctx.prev) },
    onSettled: () => { qc.invalidateQueries({ queryKey: ['sets', setId] }) },
  })
}

export const useRemoveSetRelationship = (setId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (targetId: UUID) =>
      api.delete(`/sets/${setId}/relationships/${targetId}?universe_id=${universeId}`),
    onMutate: async (targetId) => {
      await qc.cancelQueries({ queryKey: ['sets', setId] })
      const prev = qc.getQueriesData({ queryKey: ['sets', setId] })
      qc.setQueriesData({ queryKey: ['sets', setId] }, (old: any) => {
        if (!old) return old
        const friend_ids = (old.friend_ids ?? []).filter((x: string) => x !== targetId)
        const enemy_ids = (old.enemy_ids ?? []).filter((x: string) => x !== targetId)
        return { ...old, friend_ids, enemy_ids }
      })
      return { prev }
    },
    onError: (_e, _v, ctx: any) => { if (ctx?.prev) restoreSnapshot(qc, ctx.prev) },
    onSettled: () => { qc.invalidateQueries({ queryKey: ['sets', setId] }) },
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

// ─── Gangs ────────────────────────────────────────────────────────────────────

export const useGangs = (universeId: UUID | null) =>
  useQuery({
    queryKey: ['gangs', universeId],
    queryFn: () => api.get<OffsetPage<GangListItem>>(`/gangs/?universe_id=${universeId}`),
    enabled: !!universeId,
    staleTime: 60_000,
  })

export const useCreateGang = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { name: string; aliases?: string[] | null; description?: string | null }) =>
      api.post<GangRead>('/gangs/', { universe_id: universeId, ...body }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gangs', universeId] }) },
  })
}

export const useUpdateGang = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: UUID; name?: string; aliases?: string[] | null; description?: string | null }) =>
      api.patch<GangRead>(`/gangs/${id}?universe_id=${universeId}`, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gangs', universeId] }) },
  })
}

export const useDeleteGang = (universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/gangs/${id}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gangs', universeId] }) },
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

/**
 * Atomically attach one or more sets to an alliance by PATCHing the alliance
 * with the merged set_ids. This routes through `_sync_alliance_friend_relationships`
 * server-side so all pairwise FRIENDs are created in a single transaction —
 * avoids the race that occurs when issuing N parallel /sets PATCHes.
 */
export const useReassignSetsToAlliance = (allianceId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ currentSetIds, newSetIds }: { currentSetIds: UUID[]; newSetIds: UUID[] }) => {
      const merged = Array.from(new Set([...currentSetIds, ...newSetIds]))
      await api.patch(`/alliances/${allianceId}?universe_id=${universeId}`, {
        universe_id: universeId,
        set_ids: merged,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets'] })
      qc.invalidateQueries({ queryKey: ['alliances', allianceId] })
      qc.invalidateQueries({ queryKey: ['alliances'] })
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

export const useMemberAliases = (memberId: UUID | null, universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', memberId, 'aliases'],
    queryFn: () => api.get<MemberAliasRead[]>(`/members/${memberId}/aliases?universe_id=${universeId}`),
    enabled: !!memberId && !!universeId,
  })

export const useCreateMemberAlias = (memberId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { alias: string; from_date?: unknown; until_date?: unknown; source_id?: string | null }) =>
      api.post<MemberAliasRead>(`/members/${memberId}/aliases?universe_id=${universeId}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members', memberId, 'aliases'] }) },
  })
}

export const useDeleteMemberAlias = (memberId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (aliasId: UUID) =>
      api.delete(`/members/${memberId}/aliases/${aliasId}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members', memberId, 'aliases'] }) },
  })
}

export const useMemberIncarcerations = (memberId: UUID | null, universeId: UUID | null) =>
  useQuery({
    queryKey: ['members', memberId, 'incarcerations'],
    queryFn: () => api.get<MemberIncarcerationRead[]>(`/members/${memberId}/incarcerations?universe_id=${universeId}`),
    enabled: !!memberId && !!universeId,
  })

export const useCreateMemberIncarceration = (memberId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { from_date?: unknown; earliest_release_date?: unknown; max_discharge_date?: unknown; life_sentence?: boolean; facility?: string | null; case_id?: string | null; notes?: string | null }) =>
      api.post<MemberIncarcerationRead>(`/members/${memberId}/incarcerations?universe_id=${universeId}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members', memberId, 'incarcerations'] }) },
  })
}

export const useUpdateMemberIncarceration = (memberId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ spellId, data }: { spellId: UUID; data: { from_date?: unknown; earliest_release_date?: unknown; max_discharge_date?: unknown; life_sentence?: boolean; facility?: string | null; case_id?: string | null; notes?: string | null } }) =>
      api.patch<MemberIncarcerationRead>(`/members/${memberId}/incarcerations/${spellId}?universe_id=${universeId}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members', memberId, 'incarcerations'] }) },
  })
}

export const useMdocLookup = () =>
  useMutation({
    mutationFn: (url: string) => api.post<MdocProfile>('/mdoc/lookup', { url }),
  })

export const useMdocImportPhoto = () =>
  useMutation({
    mutationFn: (body: { photo_url: string; member_id: UUID; universe_id: UUID }) =>
      api.post('/mdoc/import-photo', body),
  })

export const useUniverseReleaseEvents = (universeId: UUID | null, year: number) =>
  useQuery({
    queryKey: ['release-events', universeId, year],
    queryFn: () => api.get<MemberReleaseEvent[]>(`/members/release-events?universe_id=${universeId}&year=${year}`),
    enabled: !!universeId,
  })

export const useDeleteMemberIncarceration = (memberId: UUID, universeId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (spellId: UUID) =>
      api.delete(`/members/${memberId}/incarcerations/${spellId}?universe_id=${universeId}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['members', memberId, 'incarcerations'] }) },
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
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: ['members'] })
      const prev = qc.getQueriesData({ queryKey: ['members'] })
      qc.setQueriesData({ queryKey: ['members'] }, (old: any) => {
        if (!old) return old
        // Member detail (single MemberRead/MemberReadDetail)
        if (old.id === id) return { ...old, status }
        // CursorPage<MemberListItem> (paginated lists, by-set, by-alliance, all, by-source)
        if (Array.isArray(old.items)) {
          return { ...old, items: old.items.map((m: any) => (m.id === id ? { ...m, status } : m)) }
        }
        // Search results (raw MemberListItem[])
        if (Array.isArray(old)) {
          return old.map((m: any) => (m.id === id ? { ...m, status } : m))
        }
        return old
      })
      return { prev }
    },
    onError: (_e, _v, ctx: any) => { if (ctx?.prev) restoreSnapshot(qc, ctx.prev) },
    onSettled: () => { qc.invalidateQueries({ queryKey: ['members'] }) },
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

export const useMemberIncidents = (memberId: UUID | null, universeId: UUID | null) =>
  useQuery({
    queryKey: ['incidents', 'member', memberId],
    queryFn: () => api.get<CursorPage<IncidentListItem>>(`/incidents/?universe_id=${universeId}&member_id=${memberId}`),
    enabled: !!universeId && !!memberId,
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
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['incidents', data.universe_id] })
      qc.invalidateQueries({ queryKey: ['incidents', 'municipality'] })
    },
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
    onSuccess: () => {
      qc.invalidateQueries({ predicate: (q) => q.queryKey[0] === 'incidents' })
    },
  })
}

// ─── Sources ──────────────────────────────────────────────────────────────────

export const useSources = (universeId: UUID | null, offset = 0) =>
  useQuery({
    queryKey: ['sources', universeId, offset],
    queryFn: () => api.get<OffsetPage<SourceListItem>>(`/sources/?universe_id=${universeId}&offset=${offset}`),
    enabled: !!universeId,
  })

export const useAllSources = (universeId: UUID | null) =>
  useQuery({
    queryKey: ['sources', 'all', universeId],
    queryFn: () => api.get<OffsetPage<SourceListItem>>(`/sources/?universe_id=${universeId}&limit=200`),
    enabled: !!universeId,
    staleTime: 30_000,
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

/**
 * GeoJSON for a universe's municipalities.
 *   parentFilter:
 *     undefined → all municipalities with geometry
 *     'top'     → only top-level (parent_id IS NULL)
 *     UUID      → only children of that municipality
 */
export const useMunicipalityGeoJSON = (
  universeId: UUID | null,
  parentFilter?: 'top' | UUID,
) =>
  useQuery({
    queryKey: ['municipalities', universeId, 'geojson', parentFilter ?? 'all'],
    queryFn: () => {
      const qp = parentFilter ? `&parent_id=${parentFilter}` : ''
      return api.get<MunicipalityGeoJSON>(
        `/municipalities/geojson?universe_id=${universeId}${qp}`,
      )
    },
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

export const useCreateUser = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { email: string; password: string; global_role: GlobalRole }) =>
      api.post<UserListItem>('/auth/register', body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }) },
  })
}

export const useUpdateUserRole = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: GlobalRole }) =>
      api.patch<UserListItem>(`/auth/users/${userId}/role`, { global_role: role }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }) },
  })
}

export const useUserUniverseAccess = (userId: string | null) =>
  useQuery({
    queryKey: ['user-universe-access', userId],
    queryFn: () => api.get<UserUniverseAccessItem[]>(`/auth/users/${userId}/universe-access`),
    enabled: !!userId,
    staleTime: 10_000,
  })

export const useGrantUniverseAccess = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, universeId, role = 'VIEWER' as UniverseRole }: {
      userId: string; universeId: string; role?: UniverseRole
    }) =>
      api.put<void>(`/auth/users/${userId}/universe-access/${universeId}`, { role }),
    onSuccess: (_, { userId }) =>
      qc.invalidateQueries({ queryKey: ['user-universe-access', userId] }),
  })
}

export const useRevokeUniverseAccess = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, universeId }: { userId: string; universeId: string }) =>
      api.delete<void>(`/auth/users/${userId}/universe-access/${universeId}`),
    onSuccess: (_, { userId }) =>
      qc.invalidateQueries({ queryKey: ['user-universe-access', userId] }),
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

// ─── Media ────────────────────────────────────────────────────────────────────

const mediaQueryKey = (entityType: MediaEntityType, entityId: UUID) =>
  ['media', entityType, entityId] as const

const mediaEntityField = (entityType: MediaEntityType): string => {
  if (entityType === 'member') return 'member_id'
  if (entityType === 'incident') return 'incident_id'
  if (entityType === 'source') return 'source_id'
  if (entityType === 'set') return 'set_id'
  return 'alliance_id'
}

export const useMedia = (
  entityType: MediaEntityType,
  entityId: UUID | null,
  universeId: UUID | null,
) =>
  useQuery({
    queryKey: ['media', entityType, entityId],
    queryFn: () => {
      const field = mediaEntityField(entityType)
      return api.get<MediaWithUrls[]>(
        `/media/?universe_id=${universeId}&${field}=${entityId}`,
      )
    },
    enabled: !!universeId && !!entityId,
    // Signed URLs expire — refetch before they go stale.
    staleTime: 30 * 60_000,
  })

export const useUploadMedia = (
  entityType: MediaEntityType,
  entityId: UUID,
  universeId: UUID,
) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: { file: File; caption?: string }) => {
      const fd = new FormData()
      fd.append('file', input.file)
      fd.append('universe_id', universeId)
      fd.append(mediaEntityField(entityType), entityId)
      if (input.caption) fd.append('caption', input.caption)
      return api.postFormData<MediaWithUrls>('/media/', fd)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: mediaQueryKey(entityType, entityId) })
      // Invalidate the parent so list-row avatars / detail headers refresh.
      qc.invalidateQueries({ queryKey: [`${entityType}s`] })
    },
  })
}

export const useUpdateMedia = (
  entityType: MediaEntityType,
  entityId: UUID,
  universeId: UUID,
) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: UUID; caption?: string | null; is_primary?: boolean }) =>
      api.patch<MediaWithUrls>(`/media/${id}?universe_id=${universeId}`, body),
    onMutate: async (vars) => {
      const key = mediaQueryKey(entityType, entityId)
      await qc.cancelQueries({ queryKey: key })
      const prev = qc.getQueriesData({ queryKey: key })
      // Optimistic: when toggling is_primary, demote other rows in this gallery.
      qc.setQueriesData({ queryKey: key }, (old: MediaWithUrls[] | undefined) => {
        if (!Array.isArray(old)) return old
        return old.map((m) => {
          if (m.id === vars.id) {
            return {
              ...m,
              caption: vars.caption !== undefined ? vars.caption : m.caption,
              is_primary: vars.is_primary !== undefined ? vars.is_primary : m.is_primary,
            }
          }
          if (vars.is_primary === true) return { ...m, is_primary: false }
          return m
        })
      })
      return { prev }
    },
    onError: (_e, _v, ctx: any) => { if (ctx?.prev) restoreSnapshot(qc, ctx.prev) },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: mediaQueryKey(entityType, entityId) })
      qc.invalidateQueries({ queryKey: [`${entityType}s`] })
    },
  })
}

export const useDeleteMedia = (
  entityType: MediaEntityType,
  entityId: UUID,
  universeId: UUID,
) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/media/${id}?universe_id=${universeId}`),
    onMutate: async (id) => {
      const key = mediaQueryKey(entityType, entityId)
      await qc.cancelQueries({ queryKey: key })
      const prev = qc.getQueriesData({ queryKey: key })
      qc.setQueriesData({ queryKey: key }, (old: MediaWithUrls[] | undefined) => {
        if (!Array.isArray(old)) return old
        const filtered = old.filter((m) => m.id !== id)
        const removedPrimary = old.find((m) => m.id === id)?.is_primary
        // If the deleted row was primary and others remain, optimistically promote
        // the most recent (matches the backend's auto-promote on delete).
        if (removedPrimary && filtered.length > 0 && !filtered.some((m) => m.is_primary)) {
          const sorted = [...filtered].sort((a, b) => b.created_at.localeCompare(a.created_at))
          return filtered.map((m) => (m.id === sorted[0].id ? { ...m, is_primary: true } : m))
        }
        return filtered
      })
      return { prev }
    },
    onError: (_e, _id, ctx: any) => { if (ctx?.prev) restoreSnapshot(qc, ctx.prev) },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: mediaQueryKey(entityType, entityId) })
      qc.invalidateQueries({ queryKey: [`${entityType}s`] })
    },
  })
}
