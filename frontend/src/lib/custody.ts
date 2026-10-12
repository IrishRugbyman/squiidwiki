import type { MemberCustodyIdRead, MemberRead } from './types'

// Custody systems beyond the two that still have their own member columns.
// MDOC and BOP keep their dedicated badges (with their lookup links), so rows
// mirrored from those columns are not shown a second time beside them.
const CUSTODY_SYSTEMS: Record<string, { short: string; label: string }> = {
  GDC: { short: 'GDC', label: 'Georgia Department of Corrections ID' },
  GA_OTN: { short: 'OTN', label: 'Georgia Offender Tracking Number (per arrest)' },
  TDOC: { short: 'TDOC', label: 'Tennessee Department of Correction number' },
  IDOC: { short: 'IDOC', label: 'Illinois Department of Corrections number' },
  COOK_COUNTY_JAIL: { short: 'Cook Co. jail', label: 'Cook County jail booking number' },
  RICHMOND_COUNTY_JAIL: { short: 'Richmond Co. jail', label: 'Richmond County jail booking number' },
}

export function custodyShort(system: string): string {
  return CUSTODY_SYSTEMS[system]?.short ?? system
}

export function custodyLabel(system: string): string {
  return CUSTODY_SYSTEMS[system]?.label ?? system
}

export function otherCustodyIds(member: MemberRead & { custody_ids?: MemberCustodyIdRead[] }): MemberCustodyIdRead[] {
  return (member.custody_ids ?? []).filter((c) => c.system !== 'MDOC' && c.system !== 'BOP')
}
