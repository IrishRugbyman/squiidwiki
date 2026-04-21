import type { FuzzyDateValue } from '@/components/FuzzyDate'

export type UUID = string

export interface OffsetPage<T> {
  items: T[]
  total: number
}

export interface CursorPage<T> {
  items: T[]
  next_cursor: string | null
  total: number | null
}

// Enums mirroring backend
export type MemberStatus = 'FREE' | 'LOCKED' | 'DEAD' | 'UNKNOWN' | 'ESCAPEE' | 'ABSCONDER'
export type SetStatus = 'ACTIVE' | 'EXTINCT'
export type AllianceStatus = 'ACTIVE' | 'EXTINCT' | 'DORMANT'
export type IncidentType = 'SHOOTING' | 'MURDER'
export type ParticipantRole = 'SHOOTER' | 'ASSISTED' | 'BYSTANDER' | 'VICTIM'
export type ParticipantOutcome = 'KILLED' | 'INJURED' | 'UNHARMED' | 'UNKNOWN'
export type SourceReliability = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNVERIFIED'
export type SetRelationshipType = 'FRIEND' | 'ENEMY'

// Universe
export interface UniverseListItem {
  id: UUID
  name: string
  slug: string
}

export interface UniverseRead extends UniverseListItem {
  description: string | null
  created_at: string
}

// Municipality
export interface MunicipalityListItem {
  id: UUID
  name: string
  parent_id: UUID | null
  universe_id: UUID
}

export interface MunicipalityRead extends MunicipalityListItem {}

// Source
export interface SourceListItem {
  id: UUID
  title: string
  url: string
  reliability: SourceReliability
}

export interface SourceRead extends SourceListItem {
  universe_id: UUID
  publication: string | null
  published_at: FuzzyDateValue | null
  accessed_at: string | null
  notes: string | null
  archive_url: string | null
  created_at: string
}

// Alliance
export interface AllianceListItem {
  id: UUID
  name: string
  status: AllianceStatus
  universe_id: UUID
  slug: string | null
}

export interface AllianceRead extends AllianceListItem {
  description: string | null
  founded_at: FuzzyDateValue | null
  created_at: string
}

export interface AllianceReadDetail extends AllianceRead {
  territory_ids: UUID[]
  set_ids: UUID[]
}

// Set
export interface SetListItem {
  id: UUID
  name: string
  slug: string | null
  status: SetStatus
  universe_id: UUID
  alliance_id: UUID | null
}

export interface SetRead extends SetListItem {
  alias: string | null
  bio: string | null
  founder_id: UUID | null
  created_at: string
}

export interface SetReadDetail extends SetRead {
  territory_ids: UUID[]
  friend_ids: UUID[]
  enemy_ids: UUID[]
}

export interface SetStats {
  set_id: UUID
  member_count: number
  dead_members: number
  total_shootings: number
  total_assists: number
  total_kills: number
}

// Member
export interface MemberListItem {
  id: UUID
  display_name: string
  status: MemberStatus
  set_id: UUID | null
  universe_id: UUID
  slug: string | null
  photo_url: string | null
  aliases: string[] | null
}

export interface MemberRead extends MemberListItem {
  nickname: string | null
  legal_name: string | null
  nickname_unknown: boolean
  aliases: string[] | null
  biography: string
  photo_url: string | null
  alliance_id: UUID | null
  dob: FuzzyDateValue | null
  date_of_death: FuzzyDateValue | null
  release_date: FuzzyDateValue | null
  family: Record<string, string> | null
  social_media: Record<string, string> | null
  created_at: string
  updated_at: string
}

export interface MemberReadDetail extends MemberRead {
  source_ids: UUID[]
}

export interface MemberStats {
  member_id: UUID
  shootings: number
  assists: number
  kills: number
  times_shot_survived: number
}

// Incident
export interface ParticipantRead {
  member_id: UUID
  role: ParticipantRole
  outcome: ParticipantOutcome
  notes: string | null
}

export interface IncidentListItem {
  id: UUID
  type: IncidentType
  date: FuzzyDateValue | null
  municipality_id: UUID | null
  verified: boolean
  universe_id: UUID
}

export interface IncidentRead extends IncidentListItem {
  location_text: string | null
  narrative: string | null
  created_at: string
}

export interface IncidentReadDetail extends IncidentRead {
  participants: ParticipantRead[]
  source_ids: UUID[]
}

// Audit
export type AuditAction = 'CREATE' | 'UPDATE' | 'DELETE'

export interface AuditLogRead {
  id: UUID
  user_id: UUID | null
  entity_type: string
  entity_id: UUID
  action: AuditAction
  diff_json: Record<string, unknown> | null
  created_at: string
}

// Analytics
export interface UniverseAnalytics {
  total_members: number
  total_sets: number
  total_incidents: number
  total_sources: number
  member_by_status: Record<string, number>
  incident_by_type: Record<string, number>
  top_sets_by_incidents: Array<{ id: string; name: string; incident_count: number }>
  top_sources_by_references: Array<{ id: string; title: string; ref_count: number }>
}

// Users
export type GlobalRole = 'ADMIN' | 'USER'

export interface UserListItem {
  id: UUID
  email: string
  global_role: GlobalRole
  created_at: string
  last_login_at: string | null
}
