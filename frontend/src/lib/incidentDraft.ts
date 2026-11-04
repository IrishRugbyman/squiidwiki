// The incident form holds its participants as drafts and sends them back as the
// whole list: a PATCH replaces every participant row, so anything a draft does
// not carry is erased on save. These functions are the round trip, kept out of
// the form so it can be tested on its own.

import type {
  IncidentReadDetail,
  ParticipantOutcome,
  ParticipantRole,
  UUID,
} from './types'

export interface ParticipantDraft {
  member_id: UUID
  member_name: string
  role: ParticipantRole
  outcome: ParticipantOutcome
  /** A court cleared them of this role. Excluded from kill/shooting counts. */
  acquitted: boolean
  notes?: string | null
  /** Set when the member is from another universe than the incident. The picker
   *  only searches this universe, so such a row can only have come in on load,
   *  and it has to go back out unchanged. */
  universe_slug?: string | null
}

export interface SetParticipantDraft {
  set_id: UUID
  set_name: string
  role: ParticipantRole
  outcome: ParticipantOutcome
  notes?: string | null
}

/** Drafts for an incident being edited. The detail payload names every
 *  participant, including one from another universe that this universe's member
 *  list will never contain, so its name is the fallback before the raw id. */
export function participantDrafts(
  incident: Pick<IncidentReadDetail, 'participants'>,
  memberNameById: Record<string, string>,
): ParticipantDraft[] {
  return incident.participants.map((p) => ({
    member_id: p.member_id,
    member_name: memberNameById[p.member_id] ?? p.member_name ?? p.member_id,
    role: p.role,
    outcome: p.outcome,
    acquitted: p.acquitted,
    notes: p.notes,
    universe_slug: p.member_universe_slug,
  }))
}

export function setParticipantDrafts(
  incident: Pick<IncidentReadDetail, 'set_participants'>,
  setNameById: Record<string, string>,
): SetParticipantDraft[] {
  return incident.set_participants.map((p) => ({
    set_id: p.set_id,
    set_name: setNameById[p.set_id] ?? p.set_name ?? p.set_id,
    role: p.role,
    outcome: p.outcome,
    notes: p.notes,
  }))
}

/** The participant lists as the API takes them. */
export function participantPayload(participants: ParticipantDraft[], setParticipants: SetParticipantDraft[]) {
  return {
    participants: participants.map(({ member_id, role, outcome, acquitted, notes }) => ({
      member_id, role, outcome, acquitted, notes: notes ?? null,
    })),
    set_participants: setParticipants.map(({ set_id, role, outcome, notes }) => ({
      set_id, role, outcome, notes: notes ?? null,
    })),
  }
}
