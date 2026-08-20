import type { IncidentType, ParticipantOutcome, ParticipantRole } from './types'

export const INCIDENT_TYPE_CHIP: Record<IncidentType, string> = {
  SHOOTING: 'border-amber-800/70 text-amber-400 bg-amber-950/30',
  MURDER: 'border-rose-800/70 text-rose-400 bg-rose-950/30',
  FIGHT: 'border-violet-800/70 text-violet-400 bg-violet-950/30',
  BOMBING: 'border-yellow-800/70 text-yellow-400 bg-yellow-950/30',
  ARSON: 'border-pink-800/70 text-pink-400 bg-pink-950/30',
  EXTORTION: 'border-teal-800/70 text-teal-400 bg-teal-950/30',
  KIDNAPPING: 'border-blue-800/70 text-blue-400 bg-blue-950/30',
}

/** Foreground-only variant, for glyphs and text that carry no chip background. */
export const INCIDENT_TYPE_TEXT: Record<IncidentType, string> = {
  SHOOTING: 'text-amber-400',
  MURDER: 'text-rose-400',
  FIGHT: 'text-violet-400',
  BOMBING: 'text-yellow-400',
  ARSON: 'text-pink-400',
  EXTORTION: 'text-teal-400',
  KIDNAPPING: 'text-blue-400',
}

export const INCIDENT_TYPE_LABEL: Record<IncidentType, string> = {
  SHOOTING: 'Shooting',
  MURDER: 'Murder',
  FIGHT: 'Fight',
  BOMBING: 'Bombing',
  ARSON: 'Arson',
  EXTORTION: 'Extortion',
  KIDNAPPING: 'Kidnapping',
}

/**
 * Wording used to narrate an incident ("<shooters> shot <victims>").
 * `aggressor` labels the SHOOTER-role participants for that type.
 */
export const INCIDENT_VERB: Record<IncidentType, { verb: string; aggressor: string }> = {
  SHOOTING: { verb: 'shot', aggressor: 'Shooter' },
  MURDER: { verb: 'killed', aggressor: 'Shooter' },
  FIGHT: { verb: 'fought', aggressor: 'Aggressor' },
  BOMBING: { verb: 'bombed', aggressor: 'Bomber' },
  ARSON: { verb: 'torched', aggressor: 'Arsonist' },
  EXTORTION: { verb: 'extorted', aggressor: 'Extortionist' },
  KIDNAPPING: { verb: 'abducted', aggressor: 'Abductor' },
}

export const ROLE_CHIP: Record<ParticipantRole, string> = {
  SHOOTER: 'border-red-800/70 text-red-300 bg-red-950/40',
  ASSISTED: 'border-orange-800/70 text-orange-300 bg-orange-950/40',
  BYSTANDER: 'border-zinc-700 text-zinc-400 bg-zinc-900/40',
  VICTIM: 'border-rose-800/70 text-rose-300 bg-rose-950/40',
}

export const OUTCOME_CHIP: Record<ParticipantOutcome, string> = {
  KILLED: 'border-zinc-700 text-zinc-400 bg-zinc-900/60',
  INJURED: 'border-orange-800/70 text-orange-300 bg-orange-950/40',
  UNHARMED: 'border-emerald-800/70 text-emerald-300 bg-emerald-950/40',
  UNKNOWN: 'border-zinc-700 text-zinc-500 bg-zinc-900/40',
}

export const OUTCOME_LABEL: Record<ParticipantOutcome, string> = {
  KILLED: 'Killed',
  INJURED: 'Injured',
  UNHARMED: 'Unharmed',
  UNKNOWN: 'Unknown',
}

export const ROLE_LABEL: Record<ParticipantRole, string> = {
  SHOOTER: 'Shooter',
  ASSISTED: 'Assisted',
  BYSTANDER: 'Bystander',
  VICTIM: 'Victim',
}

export function summarizeOutcomes(outcomes: ParticipantOutcome[]): string {
  const counts: Partial<Record<ParticipantOutcome, number>> = {}
  for (const o of outcomes) counts[o] = (counts[o] ?? 0) + 1
  const parts: string[] = []
  if (counts.KILLED) parts.push(`${counts.KILLED} killed`)
  if (counts.INJURED) parts.push(`${counts.INJURED} injured`)
  if (counts.UNHARMED) parts.push(`${counts.UNHARMED} unharmed`)
  return parts.join(', ') || '—'
}
