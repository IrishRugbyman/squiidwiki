import { useEffect } from 'react'
import { MapPin } from 'lucide-react'
import { formatFuzzyDate } from '@/components/FuzzyDate'
import {
  useCourtCasesFor, useMedia, useSetAllianceRelationships, useSetDetail, useSetIncidents, useSetMembers,
} from '@/lib/queries'
import type { AllianceRelationshipItem, MemberListItem, MemberStatus, SetLineageItem } from '@/lib/types'
import { MEMBER_STATUS_DOT, MEMBER_STATUS_ORDER } from '@/lib/statusColors'
import { variantDisplay, variantExtras } from '@/lib/setDisplay'
import { allianceRefsOf, gangRefsOf } from '@/lib/setGangs'
import { currentAffiliations, fuzzyDateSortKey } from '@/lib/utils'
import { CardShell, Chip, Facts, Panel, PhotoGrid, Prose, Section, ShareImg, StatGrid } from './ShareCardParts'
import { CourtCasesTable, IncidentsTable } from './ShareTables'
import type { ShareCardProps } from './MemberShareCard'

const RANK_LABEL: Record<string, string> = { CEO: 'CEO', CO_CEO: 'Co-CEO' }
const RANK_ORDER: Record<string, number> = { CEO: 0, CO_CEO: 1 }
const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

const SET_STATUS_CHIP = {
  ACTIVE: 'bg-emerald-900 text-emerald-300',
  EXTINCT: 'bg-zinc-800 text-zinc-400',
} as const

function lineageSentence(row: SetLineageItem, self: string): string {
  const [child, parent] = row.direction === 'parent' ? [self, row.other_name] : [row.other_name, self]
  switch (row.kind) {
    case 'SPLINTERED_FROM': return `${child} splintered from ${parent}`
    case 'RENAMED_FROM': return `${parent} was renamed ${child}`
    case 'MERGED_FROM': return `${parent} merged into ${child}`
    case 'YOUNGER_GENERATION_OF': return `${child} is the younger generation of ${parent}`
  }
}

function Names({ title, names, tone }: { title: string; names: string[]; tone: string }) {
  if (names.length === 0) return null
  return (
    <div>
      <p className={`text-xs font-semibold uppercase tracking-wider ${tone}`}>{title} <span className="text-zinc-500">{names.length}</span></p>
      <p className="mt-1 text-[15px] leading-relaxed text-zinc-100">{names.join(' · ')}</p>
    </div>
  )
}

function viaAlliance(rels: AllianceRelationshipItem[], type: 'FRIEND' | 'ENEMY'): string[] {
  return rels
    .filter((r) => r.type === type && r.is_current)
    .map((r) => (r.via_alliance_name ? `${r.other_name} (via ${r.via_alliance_name})` : r.other_name))
}

function RosterCard({ m, setId }: { m: MemberListItem; setId: string }) {
  const rank = currentAffiliations(m.affiliations).find((a) => a.set_id === setId)?.rank ?? null
  return (
    <div className="flex min-w-0 items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2">
      <ShareImg src={m.primary_photo_thumb_url ?? m.primary_photo_url} fallback={m.display_name} className="h-11 w-11 shrink-0 rounded-md text-sm" />
      <div className="min-w-0">
        <p className="flex items-center gap-1.5 text-[15px] font-medium leading-tight text-zinc-100">
          <span className="truncate">{m.display_name}</span>
          {rank && <span className="shrink-0 rounded bg-amber-900/60 px-1.5 text-[11px] font-semibold text-amber-300">{RANK_LABEL[rank] ?? rank}</span>}
        </p>
        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-zinc-400">
          <span className={`h-1.5 w-1.5 rounded-full ${MEMBER_STATUS_DOT[m.status]}`} />
          {titleCase(m.status)}
        </p>
      </div>
    </div>
  )
}

/** Everything the set page holds across its tabs, laid out as one image. */
export default function SetShareCard({ id, universeId, universeName, onReady }: ShareCardProps) {
  const setQ = useSetDetail(id, universeId)
  const membersQ = useSetMembers(id, universeId, false)
  const incidentsQ = useSetIncidents(id, universeId)
  const relsQ = useSetAllianceRelationships(id, universeId)
  const casesQ = useCourtCasesFor('set_id', id, universeId)
  const mediaQ = useMedia('set', id, universeId)
  const set = setQ.data

  const settled = !!set && [membersQ, incidentsQ, relsQ, casesQ, mediaQ].every((q) => !q.isLoading)
  useEffect(() => {
    if (settled) onReady()
  }, [settled, onReady])

  if (!set) return null

  const members = membersQ.data?.items ?? []
  const roster = [...members].sort((a, b) => {
    const ra = RANK_ORDER[currentAffiliations(a.affiliations).find((x) => x.set_id === set.id)?.rank ?? ''] ?? 9
    const rb = RANK_ORDER[currentAffiliations(b.affiliations).find((x) => x.set_id === set.id)?.rank ?? ''] ?? 9
    return ra - rb
      || MEMBER_STATUS_ORDER.indexOf(a.status) - MEMBER_STATUS_ORDER.indexOf(b.status)
      || a.display_name.localeCompare(b.display_name, undefined, { sensitivity: 'base', numeric: true })
  })
  const counts: Partial<Record<MemberStatus, number>> = {}
  for (const m of members) counts[m.status] = (counts[m.status] ?? 0) + 1
  const incidents = [...(incidentsQ.data?.items ?? [])].sort((a, b) => fuzzyDateSortKey(b.date).localeCompare(fuzzyDateSortKey(a.date)))
  const cases = casesQ.data ?? []
  const rels = relsQ.data ?? []
  const photos = [...(mediaQ.data ?? [])]
    .sort((a, b) => Number(b.is_primary) - Number(a.is_primary))
    .flatMap((m) => (m.thumb_url ?? m.url ? [m.thumb_url ?? m.url!] : []))
  const headPhoto = (mediaQ.data ?? []).find((m) => m.is_primary)?.url ?? set.primary_photo_url

  const variants = set.name_variants ?? []
  const primary = variants.find((v) => v.is_primary)
  const primaryExtras = primary ? variantExtras(primary) : []
  const others = variants.filter((v) => !v.is_primary)
  const gangs = gangRefsOf(set)
  const alliances = allianceRefsOf(set)
  const stats = set.stats
  const territories = (set.territories ?? []).map((t) => t.name).sort((a, b) => a.localeCompare(b))
  const activeYears = stats?.first_incident_year
    ? stats.first_incident_year === stats.last_incident_year ? String(stats.first_incident_year) : `${stats.first_incident_year} to ${stats.last_incident_year}`
    : null

  const facts: [string, React.ReactNode][] = [['Status', titleCase(set.status)]]
  if (set.founder_display_name) facts.push(['Founder', set.founder_display_name])
  if (gangs.length) facts.push([gangs.length > 1 ? 'Gangs' : 'Gang', gangs.map((g) => g.name).join(', ')])
  if (alliances.length) facts.push([alliances.length > 1 ? 'Alliances' : 'Alliance', alliances.map((a) => a.name).join(', ')])
  if (set.municipality_name) facts.push(['Municipality', set.municipality_name])
  if (territories.length) facts.push(['Territory', territories.join(', ')])
  if (activeYears) facts.push(['Active years', activeYears])

  const allies = (set.allies ?? []).map((s) => s.name)
  const enemies = (set.enemies ?? []).map((s) => s.name)
  const alliedVia = viaAlliance(rels, 'FRIEND')
  const enemiesVia = viaAlliance(rels, 'ENEMY')
  const lineage = (set.lineage ?? []).map((r) => ({
    text: lineageSentence(r, set.name),
    when: [formatFuzzyDate(r.from_date), r.until_date && `until ${formatFuzzyDate(r.until_date)}`].filter(Boolean).join(' '),
  }))
  const hasTies = allies.length + enemies.length + alliedVia.length + enemiesVia.length + lineage.length > 0

  return (
    <CardShell universeName={universeName}>
      <header className="flex items-start gap-8">
        <ShareImg src={headPhoto} fallback={set.name} className="h-56 w-56 shrink-0 rounded-2xl text-5xl ring-1 ring-zinc-700" />
        <div className="min-w-0 flex-1 pt-1">
          <h1 className="flex flex-wrap items-baseline gap-x-3 text-6xl font-bold leading-[1.05] tracking-tight text-white">
            {set.emojis?.length ? <span className="text-5xl">{set.emojis.join('')}</span> : null}
            {set.name}
          </h1>
          {(primaryExtras.length > 0 || others.length > 0) && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-base">
              {primaryExtras.map(({ slot, value }) => (
                <span key={slot} className="inline-flex items-center gap-1.5 rounded-full bg-zinc-800 px-3 py-1 text-zinc-200">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">{slot}</span>{value}
                </span>
              ))}
              {others.length > 0 && <span className="ml-1 text-xs font-semibold uppercase tracking-wider text-zinc-500">a/k/a</span>}
              {others.map((v, i) => {
                const shown = variantDisplay(v)
                if (!shown) return null
                const extras = variantExtras(v).map((e) => e.value)
                return (
                  <span key={i} className="rounded-full border border-zinc-700 px-3 py-1 text-zinc-300">
                    <span className="text-zinc-100">{shown}</span>{extras.length > 0 && <span className="text-zinc-400"> · {extras.join(' · ')}</span>}
                  </span>
                )
              })}
            </div>
          )}
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <Chip className={SET_STATUS_CHIP[set.status]}>{titleCase(set.status)}</Chip>
            {gangs.map((g) => (
              <Chip key={g.name} className="bg-zinc-800 text-zinc-100 ring-1 ring-zinc-700">
                {g.color && <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: g.color }} />}{g.name}
              </Chip>
            ))}
            {alliances.map((a) => <Chip key={a.id} className="bg-blue-950/70 text-blue-200 ring-1 ring-blue-800/50">{a.name}</Chip>)}
            {set.municipality_name && <Chip><MapPin className="h-4 w-4 text-zinc-400" />{set.municipality_name}</Chip>}
          </div>
        </div>
      </header>

      <StatGrid cells={[
        { label: 'Members', value: members.length, accent: 'text-violet-400' },
        { label: 'Free', value: counts.FREE ?? 0, accent: 'text-emerald-400' },
        { label: 'Locked', value: counts.LOCKED ?? 0, accent: 'text-orange-400' },
        { label: 'Dead', value: counts.DEAD ?? 0, accent: 'text-zinc-200' },
        { label: 'Incidents', value: incidents.length, accent: 'text-sky-400' },
        { label: 'Shootings', value: stats?.total_shootings ?? 0, accent: 'text-amber-400' },
        { label: 'Kills', value: stats?.total_kills ?? 0, accent: 'text-rose-400' },
        { label: 'Cases', value: cases.length, accent: 'text-indigo-400' },
      ]} />

      {set.bio && <Prose text={set.bio} />}

      <div className={`grid items-start gap-6 ${hasTies ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <Section title="Details"><Facts rows={facts} /></Section>
        {hasTies && (
          <Section title="Ties">
            <Panel className="space-y-4 px-5 py-4">
              <Names title="Allies" names={allies} tone="text-emerald-400" />
              <Names title="Enemies" names={enemies} tone="text-rose-400" />
              <Names title="Allies through alliances" names={alliedVia} tone="text-emerald-400/80" />
              <Names title="Enemies through alliances" names={enemiesVia} tone="text-rose-400/80" />
              {lineage.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-violet-400">Lineage</p>
                  {lineage.map((l) => (
                    <p key={l.text} className="mt-1 text-[15px] text-zinc-100">{l.text}{l.when && <span className="text-zinc-400"> · {l.when}</span>}</p>
                  ))}
                </div>
              )}
            </Panel>
          </Section>
        )}
      </div>

      {roster.length > 0 && (
        <Section title="Members" count={roster.length}>
          <div className="grid grid-cols-4 gap-2">
            {roster.map((m) => <RosterCard key={m.id} m={m} setId={set.id} />)}
          </div>
        </Section>
      )}

      {incidents.length > 0 && (
        <Section title="Incidents" count={incidents.length}><IncidentsTable incidents={incidents} /></Section>
      )}

      {cases.length > 0 && (
        <Section title="Court cases" count={cases.length}><CourtCasesTable cases={cases} /></Section>
      )}

      <PhotoGrid urls={photos} label={set.name} />
    </CardShell>
  )
}
