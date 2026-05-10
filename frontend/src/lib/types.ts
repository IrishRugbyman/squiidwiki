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
export type SetRank = 'CEO' | 'CO_CEO'
export type AllianceStatus = 'ACTIVE' | 'EXTINCT' | 'DORMANT'
export type IncidentType = 'SHOOTING' | 'MURDER' | 'FIGHT'
export type ParticipantRole = 'SHOOTER' | 'ASSISTED' | 'BYSTANDER' | 'VICTIM'
export type ParticipantOutcome = 'KILLED' | 'INJURED' | 'UNHARMED' | 'UNKNOWN'
export type SourceReliability = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNVERIFIED'
export type SetRelationshipType = 'FRIEND' | 'ENEMY'
export type MediaKind = 'R2' | 'EXTERNAL_URL'
export type MediaEntityType = 'member' | 'incident' | 'source' | 'set' | 'alliance'

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
  incident_count: number
  child_count: number
  has_geometry: boolean
}

export interface MunicipalityRead extends MunicipalityListItem {
  // GeoJSON Polygon or MultiPolygon geometry object, null when not set
  geometry: GeoJSONGeometry | null
}

export interface GeoJSONGeometry {
  type: 'Polygon' | 'MultiPolygon'
  coordinates: number[][][] | number[][][][]
}

export interface MunicipalityGeoJSONFeature {
  type: 'Feature'
  id: string
  geometry: GeoJSONGeometry
  properties: {
    id: string
    name: string
    parent_id: string | null
    incident_count: number
    set_count: number
  }
}

export interface MunicipalityGeoJSON {
  type: 'FeatureCollection'
  features: MunicipalityGeoJSONFeature[]
}

// Source
export interface SourceListItem {
  id: UUID
  title: string
  url: string
  reliability: SourceReliability
}

// Research notes
export interface ResearchNoteRead {
  id: UUID
  universe_id: UUID
  title: string
  content: string
  created_at: string
  updated_at: string
}

export interface ResearchNoteListItem {
  id: UUID
  title: string
  content: string
  updated_at: string
}

export interface SourceRead extends SourceListItem {
  universe_id: UUID
  publication: string | null
  published_at: FuzzyDateValue | null
  accessed_at: string | null
  notes: string | null
  archive_url: string | null
  created_at: string
  updated_at: string
}

// Gang
export interface GangListItem {
  id: UUID
  universe_id: UUID
  name: string
  slug: string | null
  aliases: string[] | null
  description: string | null
}

export interface GangRead extends GangListItem {
  created_at: string
  updated_at: string
}

// Alliance
export interface AllianceListItem {
  id: UUID
  name: string
  aliases: string[] | null
  status: AllianceStatus
  gang_id: UUID | null
  universe_id: UUID
  slug: string | null
  primary_photo_url: string | null
  primary_photo_thumb_url: string | null
}

export interface AllianceRead extends AllianceListItem {
  description: string | null
  founded_at: FuzzyDateValue | null
  created_at: string
  updated_at: string
}

export interface AllianceReadDetail extends AllianceRead {
  territory_ids: UUID[]
  set_ids: UUID[]
}

// Set
export interface NameVariant {
  name: string | null
  initials: string | null
  number: string | null
  is_primary: boolean
  lead?: 'name' | 'initials' | 'number' | null
}

export interface SetListItem {
  id: UUID
  name: string
  slug: string | null
  name_variants: NameVariant[] | null
  status: SetStatus
  universe_id: UUID
  alliance_id: UUID | null
  alliance_name: string | null
  gang_id: UUID | null
  gang_name: string | null
  municipality_id: UUID | null
  municipality_name: string | null
  member_count: number
  is_reserved: boolean
  primary_photo_url: string | null
  primary_photo_thumb_url: string | null
}

export interface SetRead extends SetListItem {
  bio: string | null
  founder_id: UUID | null
  created_at: string
  updated_at: string
  territory_polygon: GeoJSON.Polygon | null
}

export interface SetReadDetail extends SetRead {
  territory_ids: UUID[]
  friend_ids: UUID[]
  enemy_ids: UUID[]
}

export interface SetTerritoryPolygon {
  id: UUID
  name: string
  slug: string | null
  status: 'ACTIVE' | 'EXTINCT'
  municipality_id: UUID | null
  alliance_id: UUID | null
  territory_polygon: GeoJSON.Polygon
}

export interface SetStats {
  set_id: UUID
  member_count: number
  dead_members: number
  total_shootings: number
  total_assists: number
  total_kills: number
  active_member_count: number
  last_incident_year: number | null
  first_incident_year: number | null
}

export interface SetRelatedSummary {
  id: UUID
  name: string
  slug: string | null
  status: 'ACTIVE' | 'EXTINCT'
  member_count: number
}

export interface SetTerritorySummary {
  id: UUID
  name: string
  slug: string | null
}

export interface IncidentsPerYear {
  year: number
  count: number
}

export interface SetActivityEntry {
  id: UUID
  entity_type: 'set' | 'member'
  entity_id: UUID
  action: 'CREATE' | 'UPDATE' | 'DELETE'
  actor_email: string | null
  target_label: string | null
  target_slug: string | null
  diff_keys: string[]
  created_at: string
}

export interface SetReadDetailFull extends SetReadDetail {
  alliance_name: string | null
  alliance_slug: string | null
  municipality_name: string | null
  municipality_slug: string | null
  founder_display_name: string | null
  founder_slug: string | null
  territories: SetTerritorySummary[]
  allies: SetRelatedSummary[]
  enemies: SetRelatedSummary[]
  stats: SetStats
  incidents_per_year: IncidentsPerYear[]
  lede: string
}

// Member
export interface MemberListItem {
  id: UUID
  display_name: string
  status: MemberStatus
  set_id: UUID | null
  set_rank: SetRank | null
  alliance_id: UUID | null
  gang_id: UUID | null
  universe_id: UUID
  slug: string | null
  primary_photo_url: string | null
  primary_photo_thumb_url: string | null
  aliases: string[] | null
  date_of_death: FuzzyDateValue | null
}

export interface MemberAliasRead {
  id: UUID
  member_id: UUID
  alias: string
  from_date: FuzzyDateValue | null
  until_date: FuzzyDateValue | null
  source_id: UUID | null
  created_at: string
}

export interface MdocProfile {
  legal_name: string
  dob: FuzzyDateValue
  earliest_release_date: FuzzyDateValue | null
  max_discharge_date: FuzzyDateValue | null
  facility: string | null
  photo_url: string | null
}

export interface MemberIncarcerationRead {
  id: UUID
  member_id: UUID
  from_date: FuzzyDateValue | null
  earliest_release_date: FuzzyDateValue | null
  max_discharge_date: FuzzyDateValue | null
  life_sentence: boolean
  facility: string | null
  case_id: string | null
  notes: string | null
  created_at: string
}

export interface MemberReleaseEvent {
  spell_id: UUID
  member_id: UUID
  member_display_name: string
  member_slug: string | null
  facility: string | null
  earliest_release_date: FuzzyDateValue | null
  max_discharge_date: FuzzyDateValue | null
  life_sentence: boolean
}

export interface MemberRead extends MemberListItem {
  nickname: string | null
  legal_name: string | null
  nickname_unknown: boolean
  aliases: string[] | null
  biography: string
  alliance_id: UUID | null
  dob: FuzzyDateValue | null
  date_of_death: FuzzyDateValue | null
  family: Record<string, string> | null
  social_media: Record<string, string> | null
  death_incident_id: UUID | null
  created_at: string
  updated_at: string
}

export interface MemberKilledInSummary {
  incident_id: UUID
  type: IncidentType
  date: FuzzyDateValue | null
  municipality_id: UUID | null
  municipality_name: string | null
}

export interface MemberReadDetail extends MemberRead {
  source_ids: UUID[]
  set_name: string | null
  set_slug: string | null
  alliance_name: string | null
  alliance_slug: string | null
  aliases_detail: MemberAliasRead[]
  incarcerations: MemberIncarcerationRead[]
  stats: MemberStats | null
  killed_in: MemberKilledInSummary | null
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

export interface SetParticipantRead {
  set_id: UUID
  role: ParticipantRole
  outcome: ParticipantOutcome
  notes: string | null
}

export interface IncidentListItem {
  id: UUID
  type: IncidentType
  date: FuzzyDateValue | null
  location_text: string | null
  municipality_id: UUID | null
  municipality_name: string | null
  lat: number | null
  lng: number | null
  verified: boolean
  universe_id: UUID
  victim_names: string[]
  shooter_names: string[]
}

export interface IncidentRead extends IncidentListItem {
  location_text: string | null
  narrative: string | null
  created_at: string
  updated_at: string
}

export interface IncidentReadDetail extends IncidentRead {
  participants: ParticipantRead[]
  set_participants: SetParticipantRead[]
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
  total_alliances: number
  total_incidents: number
  total_sources: number
  member_by_status: Record<string, number>
  incident_by_type: Record<string, number>
  top_sets_by_incidents: Array<{ id: string; name: string; incident_count: number }>
  top_sources_by_references: Array<{ id: string; title: string; ref_count: number }>
  incidents_by_month: Array<{ month: string; count: number }>
  source_by_reliability: Record<string, number>
  top_members_by_incidents: Array<{ id: string; display_name: string; incident_count: number }>
}

// Media
export interface MediaWithUrls {
  id: UUID
  universe_id: UUID
  member_id: UUID | null
  incident_id: UUID | null
  source_id: UUID | null
  set_id: UUID | null
  alliance_id: UUID | null
  kind: MediaKind
  r2_key: string | null
  thumb_r2_key: string | null
  external_url: string | null
  original_filename: string | null
  content_type: string | null
  size_bytes: number | null
  width: number | null
  height: number | null
  caption: string | null
  is_primary: boolean
  created_at: string
  url: string | null
  thumb_url: string | null
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

export type UniverseRole = 'ADMIN' | 'EDITOR' | 'VIEWER'

export interface UserUniverseAccessItem {
  universe_id: UUID
  slug: string
  name: string
  role: UniverseRole
  granted: boolean
}
