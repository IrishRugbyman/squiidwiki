import type {
  AllianceStatus,
  MemberStatus,
  SetStatus,
  SourceReliability,
  IncidentType,
} from './types'

export const MEMBER_STATUS_HEX: Record<MemberStatus, string> = {
  FREE: '#10b981',
  LOCKED: '#f97316',
  DEAD: '#71717a',
  UNKNOWN: '#52525b',
  ESCAPEE: '#f59e0b',
  ABSCONDER: '#eab308',
}

export const MEMBER_STATUS_CHIP: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-900 text-emerald-300',
  LOCKED: 'bg-orange-900 text-orange-300',
  DEAD: 'bg-zinc-800 text-zinc-400',
  UNKNOWN: 'bg-zinc-800 text-zinc-400 border border-zinc-700',
  ESCAPEE: 'bg-amber-900 text-amber-300',
  ABSCONDER: 'bg-yellow-900 text-yellow-300',
}

export const SET_STATUS_HEX: Record<SetStatus, string> = {
  ACTIVE: '#10b981',
  EXTINCT: '#52525b',
}

export const ALLIANCE_STATUS_HEX: Record<AllianceStatus, string> = {
  ACTIVE: '#10b981',
  DORMANT: '#f59e0b',
  EXTINCT: '#52525b',
}

export const RELIABILITY_HEX: Record<SourceReliability, string> = {
  HIGH: '#10b981',
  MEDIUM: '#f59e0b',
  LOW: '#ef4444',
  UNVERIFIED: '#71717a',
}

export const INCIDENT_TYPE_HEX: Record<IncidentType, string> = {
  SHOOTING: '#f97316',
  MURDER: '#ef4444',
  FIGHT: '#8b5cf6',
}

export const RELIABILITY_DESCRIPTION: Record<SourceReliability, string> = {
  HIGH: 'Primary reporting; multiple independent confirmations.',
  MEDIUM: 'Single credible source or partial corroboration.',
  LOW: 'Unconfirmed or anecdotal; treat with caution.',
  UNVERIFIED: 'No verification attempted yet.',
}

export const MEMBER_STATUS_DESCRIPTION: Record<MemberStatus, string> = {
  FREE: 'Currently at liberty.',
  LOCKED: 'Currently incarcerated.',
  DEAD: 'Deceased.',
  UNKNOWN: 'Status not established.',
  ESCAPEE: 'At large following an escape.',
  ABSCONDER: 'Failed to return to custody / on the run.',
}

export const MEMBER_STATUS_ORDER: MemberStatus[] = [
  'FREE', 'LOCKED', 'ESCAPEE', 'ABSCONDER', 'DEAD', 'UNKNOWN',
]
