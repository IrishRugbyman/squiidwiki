import { createFileRoute, Link } from '@tanstack/react-router'
import { ShieldAlert, Skull, Swords, Unlock } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useMemo } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { useAllIncidents, useAllMembers } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { UUID } from '@/lib/types'

export const Route = createFileRoute('/_app/timeline')({
  component: TimelinePage,
})

type EventKind = 'SHOOTING' | 'MURDER' | 'FIGHT' | 'DEATH' | 'RELEASE'

interface TimelineEvent {
  kind: EventKind
  date: FuzzyDateValue
  /** id of the entity to deep-link into */
  id: UUID
  /** url-safe slug if available, else id */
  slug: string
  /** primary label */
  primary: string
  /** secondary descriptive text (optional) */
  secondary?: string
}

function sortableKey(d: FuzzyDateValue | null | undefined): number {
  if (!d?.year) return -Infinity
  const m = d.month ?? 6
  const day = d.day ?? 15
  return d.year * 10000 + m * 100 + day
}

const KIND_CONFIG: Record<EventKind, { icon: LucideIcon; tint: string; label: string; route: string }> = {
  SHOOTING: { icon: Swords, tint: 'text-amber-400 bg-amber-950/40 border-amber-800/60', label: 'Shooting', route: '/incidents/$id' },
  MURDER: { icon: Skull, tint: 'text-rose-400 bg-rose-950/40 border-rose-800/60', label: 'Murder', route: '/incidents/$id' },
  FIGHT: { icon: ShieldAlert, tint: 'text-violet-400 bg-violet-950/40 border-violet-800/60', label: 'Fight', route: '/incidents/$id' },
  DEATH: { icon: Skull, tint: 'text-rose-300 bg-rose-950/30 border-rose-900/60', label: 'Member died', route: '/members/$id' },
  RELEASE: { icon: Unlock, tint: 'text-emerald-400 bg-emerald-950/30 border-emerald-800/60', label: 'Released', route: '/members/$id' },
}

function TimelinePage() {
  const universeId = useUniverseStore((s) => s.activeUniverse?.id ?? null)
  const { data: incidentsData, isLoading: incidentsLoading } = useAllIncidents(universeId)
  const { data: membersData, isLoading: membersLoading } = useAllMembers(universeId)

  const events = useMemo<TimelineEvent[]>(() => {
    const out: TimelineEvent[] = []

    // Map of "name|year-month-day" → true for every victim already described in an incident row.
    // Used below to suppress redundant "Member died" entries.
    const incidentVictimKeys = new Set<string>()

    for (const inc of incidentsData?.items ?? []) {
      if (!inc.date?.year) continue
      const shooters = inc.shooter_names ?? []
      const victims = inc.victim_names ?? []
      const kind: EventKind =
        inc.type === 'MURDER' ? 'MURDER'
        : inc.type === 'FIGHT' ? 'FIGHT'
        : 'SHOOTING'
      const verb = kind === 'MURDER' ? 'killed' : kind === 'FIGHT' ? 'fought' : 'shot'
      const aggressorLabel = kind === 'FIGHT' ? 'Aggressor' : 'Shooter'
      const fmt = (names: string[], max = 3) =>
        names.slice(0, max).join(', ') + (names.length > max ? ` +${names.length - max}` : '')
      const secondary =
        shooters.length > 0 && victims.length > 0 ? `${fmt(shooters)} ${verb} ${fmt(victims)}`
        : victims.length > 0 ? `Victim${victims.length === 1 ? '' : 's'}: ${fmt(victims)}`
        : shooters.length > 0 ? `${aggressorLabel}${shooters.length === 1 ? '' : 's'}: ${fmt(shooters)}`
        : undefined
      out.push({
        kind,
        date: inc.date,
        id: inc.id,
        slug: inc.id,
        primary: KIND_CONFIG[kind].label,
        secondary,
      })
      const dateKey = `${inc.date.year}-${inc.date.month ?? 0}-${inc.date.day ?? 0}`
      for (const name of victims) incidentVictimKeys.add(`${name}|${dateKey}`)
    }

    for (const m of membersData?.items ?? []) {
      if (!m.date_of_death?.year) continue
      const dateKey = `${m.date_of_death.year}-${m.date_of_death.month ?? 0}-${m.date_of_death.day ?? 0}`
      // Skip if this death is already described by an incident victim row on the same date.
      if (incidentVictimKeys.has(`${m.display_name}|${dateKey}`)) continue
      out.push({
        kind: 'DEATH',
        date: m.date_of_death,
        id: m.id,
        slug: m.slug ?? m.id,
        primary: m.display_name,
        secondary: 'died',
      })
    }

    out.sort((x, y) => sortableKey(y.date) - sortableKey(x.date))
    return out
  }, [incidentsData, membersData])

  const grouped = useMemo(() => {
    const map = new Map<number, TimelineEvent[]>()
    for (const e of events) {
      const y = e.date.year ?? 0
      if (!map.has(y)) map.set(y, [])
      map.get(y)!.push(e)
    }
    return Array.from(map.entries()).sort((a, b) => b[0] - a[0])
  }, [events])

  if (!universeId) return <NoUniverse />

  const isLoading = incidentsLoading || membersLoading
  const eventCount = events.length

  return (
    <div>
      <PageHeader
        title="Timeline"
        description={
          isLoading
            ? undefined
            : `${eventCount} dated event${eventCount === 1 ? '' : 's'} across ${grouped.length} year${grouped.length === 1 ? '' : 's'}`
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
      ) : eventCount === 0 ? (
        <p className="py-12 text-center text-sm text-zinc-400">
          Nothing dated to show yet. Record incidents or set member dates of death to populate the feed.
        </p>
      ) : (
        <div className="space-y-8">
          {grouped.map(([year, items]) => (
            <section key={year}>
              <div className="sticky top-0 z-10 -mx-4 mb-3 flex items-center gap-3 bg-zinc-950/95 px-4 py-1 backdrop-blur">
                <h2 className="font-mono text-2xl font-bold tabular-nums text-white">{year}</h2>
                <span className="text-xs text-zinc-400">
                  {items.length} event{items.length === 1 ? '' : 's'}
                </span>
              </div>
              <ol className="relative space-y-2 border-l border-zinc-800 pl-5">
                {items.map((e, idx) => {
                  const cfg = KIND_CONFIG[e.kind]
                  const Icon = cfg.icon
                  return (
                    <li key={`${e.kind}-${e.id}-${idx}`} className="relative">
                      <span
                        className={`absolute -left-[27px] top-2 inline-flex h-4 w-4 items-center justify-center rounded-full border ${cfg.tint}`}
                        aria-hidden="true"
                      >
                        <Icon className="h-2.5 w-2.5" />
                      </span>
                      <Link
                        to={cfg.route as '/incidents/$id' | '/members/$id'}
                        params={{ id: e.slug }}
                        className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-zinc-800 bg-zinc-900/30 px-3 py-2 text-sm transition-colors hover:border-zinc-700 hover:bg-zinc-900/60"
                      >
                        <span className="font-mono text-xs tabular-nums text-zinc-400">
                          <FuzzyDate value={e.date} />
                        </span>
                        <span className="text-zinc-200">{e.primary}</span>
                        {e.secondary && <span className="text-xs text-zinc-400">{e.secondary}</span>}
                        <span className="ml-auto rounded-md border border-zinc-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-zinc-400">
                          {cfg.label}
                        </span>
                      </Link>
                    </li>
                  )
                })}
              </ol>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
