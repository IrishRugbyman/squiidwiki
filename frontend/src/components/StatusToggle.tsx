import { Check, ChevronDown, Loader2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { AllianceStatus, MemberStatus, SetStatus } from '@/lib/types'

const MEMBER_STATUS_STYLE: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-900 text-emerald-300',
  LOCKED: 'bg-orange-900 text-orange-300',
  DEAD: 'bg-zinc-800 text-zinc-400',
  UNKNOWN: 'bg-zinc-800 text-zinc-400',
  ESCAPEE: 'bg-amber-900 text-amber-300',
  ABSCONDER: 'bg-yellow-900 text-yellow-300',
}

const SET_STATUS_STYLE: Record<SetStatus, string> = {
  ACTIVE: 'bg-emerald-900 text-emerald-300',
  EXTINCT: 'bg-zinc-800 text-zinc-500',
}

const ALLIANCE_STATUS_STYLE: Record<AllianceStatus, string> = {
  ACTIVE: 'bg-emerald-900 text-emerald-300',
  DORMANT: 'bg-amber-900 text-amber-300',
  EXTINCT: 'bg-zinc-800 text-zinc-500',
}

const MEMBER_OPTIONS: MemberStatus[] = ['FREE', 'LOCKED', 'DEAD', 'UNKNOWN', 'ESCAPEE', 'ABSCONDER']
const SET_OPTIONS: SetStatus[] = ['ACTIVE', 'EXTINCT']
const ALLIANCE_OPTIONS: AllianceStatus[] = ['ACTIVE', 'DORMANT', 'EXTINCT']

interface BaseProps<T extends string> {
  value: T
  options: readonly T[]
  styles: Record<T, string>
  onChange: (next: T) => void
  pending?: boolean
}

function StatusToggle<T extends string>({ value, options, styles, onChange, pending }: BaseProps<T>) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        disabled={pending}
        onClick={(e) => e.stopPropagation()}
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition-opacity hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 disabled:opacity-50 ${styles[value]}`}
        aria-label={`Change status (current: ${value})`}
      >
        {value}
        {pending
          ? <Loader2 className="h-3 w-3 animate-spin opacity-70" />
          : <ChevronDown className="h-3 w-3 opacity-50" />}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" onClick={(e) => e.stopPropagation()}>
        {options.map((opt) => (
          <DropdownMenuItem
            key={opt}
            onSelect={() => { if (opt !== value) onChange(opt) }}
            className="flex items-center justify-between gap-3"
          >
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${styles[opt]}`}>
              {opt}
            </span>
            {opt === value && <Check className="h-3.5 w-3.5 text-violet-400" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function MemberStatusToggle(props: { value: MemberStatus; onChange: (s: MemberStatus) => void; pending?: boolean }) {
  return <StatusToggle value={props.value} options={MEMBER_OPTIONS} styles={MEMBER_STATUS_STYLE} onChange={props.onChange} pending={props.pending} />
}

export function SetStatusToggle(props: { value: SetStatus; onChange: (s: SetStatus) => void; pending?: boolean }) {
  return <StatusToggle value={props.value} options={SET_OPTIONS} styles={SET_STATUS_STYLE} onChange={props.onChange} pending={props.pending} />
}

export function AllianceStatusToggle(props: { value: AllianceStatus; onChange: (s: AllianceStatus) => void; pending?: boolean }) {
  return <StatusToggle value={props.value} options={ALLIANCE_OPTIONS} styles={ALLIANCE_STATUS_STYLE} onChange={props.onChange} pending={props.pending} />
}
