import { describe, expect, it } from 'vitest'
import { participantDrafts, participantPayload, setParticipantDrafts } from './incidentDraft'
import type { ParticipantRead, SetParticipantRead } from './types'

// The incident form PATCHes the whole participant list, and the backend writes
// exactly what it is sent. So an unchanged form must send back every row it
// loaded, with every stored field: a dropped row clears that member's death
// link, a dropped note is gone. The expected payloads are the input rows
// themselves, written out by hand, never the output of the code under test.

const home: ParticipantRead = {
  member_id: 'aaaaaaaa-0000-0000-0000-000000000001',
  member_name: 'Local',
  member_slug: 'local',
  member_universe_slug: 'ohio',
  role: 'VICTIM',
  outcome: 'INJURED',
  acquitted: false,
  notes: 'Shot in the leg',
}

const visitor: ParticipantRead = {
  member_id: 'aaaaaaaa-0000-0000-0000-000000000002',
  member_name: 'Visitor',
  member_slug: 'visitor',
  member_universe_slug: 'michigan',
  role: 'SHOOTER',
  outcome: 'UNHARMED',
  acquitted: true,
  notes: null,
}

const setRow: SetParticipantRead = {
  set_id: 'bbbbbbbb-0000-0000-0000-000000000001',
  set_name: 'Some Set',
  set_slug: 'some-set',
  role: 'VICTIM',
  outcome: 'KILLED',
  notes: 'Member unnamed in every source',
}

describe('incident participant drafts', () => {
  it('sends back every loaded row unchanged, including one from another universe', () => {
    // The member list of the universe on screen knows only the local member.
    const drafts = participantDrafts({ participants: [home, visitor] }, { [home.member_id]: 'Local' })
    const sets = setParticipantDrafts({ set_participants: [setRow] }, {})

    expect(participantPayload(drafts, sets)).toEqual({
      participants: [
        { member_id: home.member_id, role: 'VICTIM', outcome: 'INJURED', acquitted: false, notes: 'Shot in the leg' },
        { member_id: visitor.member_id, role: 'SHOOTER', outcome: 'UNHARMED', acquitted: true, notes: null },
      ],
      set_participants: [
        { set_id: setRow.set_id, role: 'VICTIM', outcome: 'KILLED', notes: 'Member unnamed in every source' },
      ],
    })
  })

  it('names a participant from another universe from the payload, not by his id', () => {
    const [draft] = participantDrafts({ participants: [visitor] }, {})
    expect(draft.member_name).toBe('Visitor')
    expect(draft.universe_slug).toBe('michigan')
  })

  it('prefers the local member list for a name, which can be fresher than the payload', () => {
    const [draft] = participantDrafts({ participants: [home] }, { [home.member_id]: 'Renamed' })
    expect(draft.member_name).toBe('Renamed')
  })

  it('sends a null note for a participant added in the form', () => {
    const payload = participantPayload(
      [{ member_id: home.member_id, member_name: 'Local', role: 'BYSTANDER', outcome: 'UNKNOWN', acquitted: false }],
      [],
    )
    expect(payload.participants[0].notes).toBeNull()
  })
})
