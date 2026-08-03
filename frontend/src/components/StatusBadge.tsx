import { Badge } from './ui/badge'
import type { AllianceStatus, MemberStatus, SetStatus, SourceReliability } from '@/lib/types'

const MEMBER_STATUS_STYLE: Record<MemberStatus, string> = {
  FREE: 'border-transparent bg-emerald-900 text-emerald-300',
  LOCKED: 'border-transparent bg-orange-900 text-orange-300',
  DEAD: 'border-transparent bg-zinc-800 text-zinc-400 line-through',
  // bg-transparent is load-bearing, not decorative. Every other entry sets a
  // bg-*, which tailwind-merge uses to displace the Badge default variant's
  // `bg-violet-600`. Omit it and the badge silently inherits the accent fill,
  // so "we do not know this member's status" renders as a solid highlighted
  // pill. Same for UNVERIFIED below.
  UNKNOWN: 'border-zinc-700 bg-transparent text-zinc-400',
  ESCAPEE: 'border-transparent bg-amber-900 text-amber-300',
  ABSCONDER: 'border-transparent bg-yellow-900 text-yellow-300',
}

const SET_STATUS_STYLE: Record<SetStatus, string> = {
  ACTIVE: 'border-transparent bg-emerald-900 text-emerald-300',
  EXTINCT: 'border-transparent bg-zinc-800 text-zinc-400',
}

const ALLIANCE_STATUS_STYLE: Record<AllianceStatus, string> = {
  ACTIVE: 'border-transparent bg-emerald-900 text-emerald-300',
  DORMANT: 'border-transparent bg-amber-900 text-amber-300',
  EXTINCT: 'border-transparent bg-zinc-800 text-zinc-400',
}

const RELIABILITY_STYLE: Record<SourceReliability, string> = {
  HIGH: 'border-transparent bg-emerald-900 text-emerald-300',
  MEDIUM: 'border-transparent bg-amber-900 text-amber-300',
  LOW: 'border-transparent bg-red-900 text-red-300',
  UNVERIFIED: 'border-zinc-700 bg-transparent text-zinc-400',
}

export function MemberStatusBadge({ status }: { status: MemberStatus }) {
  return <Badge className={MEMBER_STATUS_STYLE[status]}>{status}</Badge>
}

export function SetStatusBadge({ status }: { status: SetStatus }) {
  return <Badge className={SET_STATUS_STYLE[status]}>{status}</Badge>
}

export function AllianceStatusBadge({ status }: { status: AllianceStatus }) {
  return <Badge className={ALLIANCE_STATUS_STYLE[status]}>{status}</Badge>
}

export function ReliabilityBadge({ reliability }: { reliability: SourceReliability }) {
  return <Badge className={RELIABILITY_STYLE[reliability]}>{reliability}</Badge>
}
