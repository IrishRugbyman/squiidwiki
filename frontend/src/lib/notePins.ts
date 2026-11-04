import { AlertTriangle, Network, Shield, Users, type LucideIcon } from 'lucide-react'
import type { PinKind } from '@/lib/types'

export const PIN_ICON: Record<PinKind, LucideIcon> = {
  member: Users,
  set: Shield,
  incident: AlertTriangle,
  alliance: Network,
}

export const PIN_KIND_LABEL: Record<PinKind, string> = {
  member: 'Member',
  set: 'Set',
  incident: 'Incident',
  alliance: 'Alliance',
}

/** First non-empty line of a note, trimmed for a one-line preview. */
export function firstLine(content: string): string {
  const line = content.split('\n').find((l) => l.trim() !== '')
  return line ? line.trim().slice(0, 140) : ''
}
