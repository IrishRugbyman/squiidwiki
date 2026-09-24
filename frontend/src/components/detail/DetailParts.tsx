import { Link } from '@tanstack/react-router'
import { FuzzyDate } from '@/components/FuzzyDate'
import { INCIDENT_TYPE_ICON, INCIDENT_TYPE_TILE } from '@/lib/incidentColors'
import type { IncidentListItem } from '@/lib/types'

// Building blocks shared by the detail pages (set, alliance, incident), so the
// three read as one design and a fix lands on all of them.

const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()
const RANK_LABEL: Record<string, string> = { CEO: 'CEO', CO_CEO: 'Co-CEO' }

export function PanelHeading({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="mb-2 flex items-center justify-between gap-2">
      <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-400">{children}</h2>
      {action}
    </div>
  )
}

/** Label over value on a grid, so a 320px column never squeezes either. */
export function DetailRow({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[6.5rem_minmax(0,1fr)] items-baseline gap-3 py-1.5">
      <dt className="text-xs text-zinc-400">{label}</dt>
      <dd className="min-w-0 text-sm text-zinc-200">{children}</dd>
    </div>
  )
}

export const None = () => <span className="text-zinc-500">-</span>

/**
 * One strip of counts. A zero renders dim so the eye lands on what exists, and
 * each cell opens the view behind it.
 */
export function StatStrip({ cells }: { cells: { label: string; value: number; accent: string; onClick?: () => void; title?: string }[] }) {
  return (
    <div className="grid grid-cols-3 divide-x divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30 sm:grid-cols-6 sm:divide-y-0">
      {cells.map((c) => {
        const body = (
          <>
            <span className={`text-lg font-semibold tabular-nums ${c.value > 0 ? c.accent : 'text-zinc-600'}`}>{c.value.toLocaleString()}</span>
            <span className={`text-[11px] ${c.value > 0 ? 'text-zinc-300' : 'text-zinc-500'}`}>{c.label}</span>
          </>
        )
        const cls = 'flex flex-col items-center gap-0.5 px-2 py-2'
        return c.onClick ? (
          <button key={c.label} type="button" onClick={c.onClick} title={c.title} className={`${cls} transition-colors hover:bg-zinc-800/40 focus-visible:bg-zinc-800/40 focus-visible:outline-none`}>
            {body}
          </button>
        ) : (
          <div key={c.label} title={c.title} className={cls}>{body}</div>
        )
      })}
    </div>
  )
}

export function RankBadge({ rank }: { rank: string | null }) {
  if (!rank) return null
  return (
    <span className="inline-flex items-center rounded-md border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-300">
      {RANK_LABEL[rank] ?? rank}
    </span>
  )
}

/** Who did it and to whom, in one muted line. */
export function IncidentPeople({ inc }: { inc: IncidentListItem }) {
  const list = (names: string[]) => names.slice(0, 3).join(', ') + (names.length > 3 ? ` +${names.length - 3}` : '')
  if (!inc.shooter_names.length && !inc.victim_names.length) return null
  return (
    <span className="block truncate text-xs text-zinc-400">
      {inc.victim_names.length > 0 && <span className="text-zinc-300">{list(inc.victim_names)}</span>}
      {inc.shooter_names.length > 0 && <span>{inc.victim_names.length > 0 ? ' · ' : ''}by {list(inc.shooter_names)}</span>}
    </span>
  )
}

export function IncidentRow({ inc }: { inc: IncidentListItem }) {
  const Icon = INCIDENT_TYPE_ICON[inc.type]
  return (
    <Link to="/incidents/$id" params={{ id: inc.id }} className="flex items-center gap-3 px-3 py-2.5 transition-colors hover:bg-zinc-900/60">
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${INCIDENT_TYPE_TILE[inc.type]}`} title={titleCase(inc.type)}>
        <Icon className="h-4 w-4" aria-hidden />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline gap-2 text-sm">
          <span className="font-medium text-zinc-100">{titleCase(inc.type)}</span>
          <span className="font-mono text-xs tabular-nums text-zinc-400">{inc.date ? <FuzzyDate value={inc.date} /> : 'Date unknown'}</span>
          {inc.municipality_name && <span className="hidden truncate text-xs text-zinc-500 sm:inline">{inc.municipality_name}</span>}
        </span>
        <IncidentPeople inc={inc} />
      </span>
    </Link>
  )
}
