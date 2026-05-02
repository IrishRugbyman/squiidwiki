import { Link } from '@tanstack/react-router'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { FuzzyDate } from '@/components/FuzzyDate'
import { INCIDENT_TYPE_HEX } from '@/lib/statusColors'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { IncidentListItem } from '@/lib/types'

interface MemberTimelineProps {
  incidents: IncidentListItem[]
  dob?: FuzzyDateValue | null
  dateOfDeath?: FuzzyDateValue | null
}

function fuzzyToEpoch(v: FuzzyDateValue | null | undefined): number | null {
  if (!v || !v.year) return null
  return new Date(v.year, (v.month ?? 6) - 1, v.day ?? 15).getTime()
}

export function MemberTimeline({ incidents, dob, dateOfDeath }: MemberTimelineProps) {
  const datedIncidents = incidents
    .map((i) => ({ inc: i, t: fuzzyToEpoch(i.date) }))
    .filter((x): x is { inc: IncidentListItem; t: number } => x.t !== null)
    .sort((a, b) => a.t - b.t)

  const dobT = fuzzyToEpoch(dob ?? null)
  const dodT = fuzzyToEpoch(dateOfDeath ?? null)

  if (datedIncidents.length === 0) return null

  const min = Math.min(
    datedIncidents[0].t,
    dobT ?? Infinity,
  )
  const max = Math.max(
    datedIncidents[datedIncidents.length - 1].t,
    dodT ?? -Infinity,
  )
  const span = Math.max(max - min, 1)

  function pct(t: number) {
    return ((t - min) / span) * 100
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
        <div className="mb-6 flex items-center justify-between text-[10px] text-zinc-600">
          <span>{new Date(min).getFullYear()}</span>
          <span>{new Date(max).getFullYear()}</span>
        </div>
        <div className="relative h-16">
          {/* Axis */}
          <div className="absolute top-1/2 left-0 right-0 h-px -translate-y-1/2 bg-zinc-800" />

          {/* DOB marker */}
          {dobT !== null && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${pct(dobT)}%` }}
                >
                  <div className="h-3 w-3 rounded-full bg-sky-500 ring-2 ring-zinc-900" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="top">Born {dob ? <FuzzyDate value={dob} /> : '—'}</TooltipContent>
            </Tooltip>
          )}

          {/* Incidents */}
          {datedIncidents.map(({ inc, t }) => (
            <Tooltip key={inc.id}>
              <TooltipTrigger asChild>
                <Link
                  to="/incidents/$id"
                  params={{ id: inc.id }}
                  className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 rounded-full"
                  style={{ left: `${pct(t)}%` }}
                >
                  <div
                    className="h-3 w-3 rounded-full ring-2 ring-zinc-900 transition-transform hover:scale-125"
                    style={{ backgroundColor: INCIDENT_TYPE_HEX[inc.type] ?? '#a78bfa' }}
                  />
                </Link>
              </TooltipTrigger>
              <TooltipContent side="top">
                <div className="flex flex-col gap-0.5 text-xs">
                  <span className="font-semibold">{inc.type}</span>
                  <span className="text-zinc-400">{inc.date ? <FuzzyDate value={inc.date} /> : 'Unknown date'}</span>
                  {inc.victim_names.length > 0 && (
                    <span className="text-zinc-400">Victims: {inc.victim_names.join(', ')}</span>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          ))}

          {/* DOD marker */}
          {dodT !== null && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${pct(dodT)}%` }}
                >
                  <div className="flex h-4 w-4 items-center justify-center rounded-full bg-zinc-700 ring-2 ring-zinc-900">
                    <span className="text-[8px] font-bold text-zinc-300">†</span>
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top">Died {dateOfDeath ? <FuzzyDate value={dateOfDeath} /> : '—'}</TooltipContent>
            </Tooltip>
          )}
        </div>
        <div className="mt-3 flex justify-center gap-4 text-[10px] text-zinc-500">
          {dobT !== null && <span className="inline-flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-sky-500" /> Born</span>}
          <span className="inline-flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: INCIDENT_TYPE_HEX.SHOOTING }} /> Shooting</span>
          <span className="inline-flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: INCIDENT_TYPE_HEX.MURDER }} /> Murder</span>
          {dodT !== null && <span className="inline-flex items-center gap-1">† Died</span>}
        </div>
      </div>
    </TooltipProvider>
  )
}
