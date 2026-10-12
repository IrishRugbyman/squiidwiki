import { useEffect } from 'react'
import { MapPin } from 'lucide-react'
import { formatFuzzyDate } from '@/components/FuzzyDate'
import {
  useAlliance, useAllianceIncidents, useAllianceMembers, useAllianceRelationships, useAllSets, useCourtCasesFor, useMedia,
} from '@/lib/queries'
import type { AllianceRelationshipItem, MemberListItem } from '@/lib/types'
import { MEMBER_STATUS_DOT, MEMBER_STATUS_ORDER } from '@/lib/statusColors'
import { nonPrimaryVariantsText, variantDisplay, variantExtras } from '@/lib/setDisplay'
import { currentAffiliations, fuzzyDateSortKey } from '@/lib/utils'
import { CardShell, Chip, Facts, Panel, PhotoGrid, Prose, Section, ShareImg, StatGrid } from './ShareCardParts'
import { CourtCasesTable, IncidentsTable } from './ShareTables'
import type { ShareCardProps } from './MemberShareCard'

const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

const ALLIANCE_STATUS_CHIP = {
  ACTIVE: 'bg-emerald-900 text-emerald-300',
  DORMANT: 'bg-amber-900 text-amber-300',
  EXTINCT: 'bg-zinc-800 text-zinc-400',
} as const

const LINEAGE_VERB = {
  SPLINTERED_FROM: ['splintered from', 'splintered from it'],
  RENAMED_FROM: ['renamed from', 'renamed to'],
  MERGED_FROM: ['merged from', 'merged into it'],
  YOUNGER_GENERATION_OF: ['younger generation of', 'its younger generation'],
} as const

function names(rels: AllianceRelationshipItem[], type: 'FRIEND' | 'ENEMY'): string[] {
  return rels.filter((r) => r.type === type && r.is_current).map((r) => r.other_name)
}

function MemberChip({ m, setNames }: { m: MemberListItem; setNames: string }) {
  return (
    <div className="flex min-w-0 items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2">
      <ShareImg src={m.primary_photo_thumb_url ?? m.primary_photo_url} fallback={m.display_name} className="h-11 w-11 shrink-0 rounded-md text-sm" />
      <div className="min-w-0">
        <p className="truncate text-[15px] font-medium leading-tight text-zinc-100">{m.display_name}</p>
        <p className="mt-0.5 flex items-center gap-1.5 truncate text-xs text-zinc-400">
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${MEMBER_STATUS_DOT[m.status]}`} />
          {titleCase(m.status)}{setNames && <span className="truncate text-zinc-500">· {setNames}</span>}
        </p>
      </div>
    </div>
  )
}

/** Everything the alliance page holds across its tabs, laid out as one image. */
export default function AllianceShareCard({ id, universeId, universeName, onReady }: ShareCardProps) {
  const allianceQ = useAlliance(id, universeId)
  const setsQ = useAllSets(universeId)
  const membersQ = useAllianceMembers(id, universeId)
  const incidentsQ = useAllianceIncidents(id, universeId)
  const relsQ = useAllianceRelationships(id, universeId)
  const casesQ = useCourtCasesFor('alliance_id', id, universeId)
  const mediaQ = useMedia('alliance', id, universeId)
  const alliance = allianceQ.data

  const settled = !!alliance && [setsQ, membersQ, incidentsQ, relsQ, casesQ, mediaQ].every((q) => !q.isLoading)
  useEffect(() => {
    if (settled) onReady()
  }, [settled, onReady])

  if (!alliance) return null

  const setIds = new Set(alliance.set_ids)
  const sets = (setsQ.data?.items ?? []).filter((s) => setIds.has(s.id)).sort((a, b) => b.member_count - a.member_count || a.name.localeCompare(b.name))
  const members = [...(membersQ.data?.items ?? [])].sort((a, b) =>
    MEMBER_STATUS_ORDER.indexOf(a.status) - MEMBER_STATUS_ORDER.indexOf(b.status)
    || a.display_name.localeCompare(b.display_name, undefined, { sensitivity: 'base', numeric: true }))
  const incidents = [...(incidentsQ.data?.items ?? [])].sort((a, b) => fuzzyDateSortKey(b.date).localeCompare(fuzzyDateSortKey(a.date)))
  const cases = casesQ.data ?? []
  const rels = relsQ.data ?? []
  const photos = [...(mediaQ.data ?? [])]
    .sort((a, b) => Number(b.is_primary) - Number(a.is_primary))
    .flatMap((m) => (m.thumb_url ?? m.url ? [m.thumb_url ?? m.url!] : []))
  const headPhoto = (mediaQ.data ?? []).find((m) => m.is_primary)?.url ?? alliance.primary_photo_url

  const variants = alliance.name_variants ?? []
  const primary = variants.find((v) => v.is_primary)
  const primaryExtras = primary ? variantExtras(primary) : []
  const others = variants.filter((v) => !v.is_primary)
  const stats = alliance.stats
  const activeYears = stats.first_incident_year
    ? stats.first_incident_year === stats.last_incident_year ? String(stats.first_incident_year) : `${stats.first_incident_year} to ${stats.last_incident_year}`
    : null

  const facts: [string, React.ReactNode][] = [['Status', titleCase(alliance.status)]]
  if (alliance.founder_display_name) facts.push(['Founder', alliance.founder_display_name])
  if (alliance.founded_at) facts.push(['Founded', formatFuzzyDate(alliance.founded_at) ?? 'Unknown'])
  if (alliance.gangs.length) facts.push([alliance.gangs.length > 1 ? 'Gangs' : 'Gang', alliance.gangs.map((g) => g.name).join(', ')])
  if (alliance.territories.length) facts.push(['Cities', alliance.territories.map((t) => t.name).join(', ')])
  if (activeYears) facts.push(['Active years', activeYears])

  const allies = names(rels, 'FRIEND')
  const enemies = names(rels, 'ENEMY')
  const lineage = alliance.lineage.map((l) => {
    const verb = LINEAGE_VERB[l.kind][l.direction === 'parent' ? 0 : 1]
    return l.direction === 'parent' ? `${alliance.name} ${verb} ${l.other_name}` : `${l.other_name}: ${verb}`
  })
  const hasTies = allies.length + enemies.length + lineage.length > 0

  return (
    <CardShell universeName={universeName}>
      <header className="flex items-start gap-8">
        <ShareImg src={headPhoto} fallback={alliance.name} className="h-56 w-56 shrink-0 rounded-2xl text-5xl ring-1 ring-zinc-700" />
        <div className="min-w-0 flex-1 pt-1">
          <h1 className="flex flex-wrap items-baseline gap-x-3 text-6xl font-bold leading-[1.05] tracking-tight text-white">
            {alliance.emojis?.length ? <span className="text-5xl">{alliance.emojis.join('')}</span> : null}
            {alliance.name}
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
            <Chip className={ALLIANCE_STATUS_CHIP[alliance.status]}>{titleCase(alliance.status)}</Chip>
            {alliance.gangs.map((g) => (
              <Chip key={g.id} className="bg-zinc-800 text-zinc-100 ring-1 ring-zinc-700">
                {g.color && <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: g.color }} />}{g.name}
              </Chip>
            ))}
            {alliance.territories.map((t) => <Chip key={t.id}><MapPin className="h-4 w-4 text-zinc-400" />{t.name}</Chip>)}
          </div>
        </div>
      </header>

      <StatGrid cells={[
        { label: 'Sets', value: alliance.set_ids.length, accent: 'text-violet-400' },
        { label: 'Members', value: stats.member_count, accent: 'text-sky-400' },
        { label: 'Locked', value: stats.locked_members, accent: 'text-orange-400' },
        { label: 'Dead', value: stats.dead_members, accent: 'text-zinc-200' },
        { label: 'Incidents', value: incidents.length, accent: 'text-amber-300' },
        { label: 'Shootings', value: stats.total_shootings, accent: 'text-amber-400' },
        { label: 'Kills', value: stats.total_kills, accent: 'text-rose-400' },
        { label: 'Cases', value: cases.length, accent: 'text-indigo-400' },
      ]} />

      {alliance.description && <Prose text={alliance.description} />}

      <div className={`grid items-start gap-6 ${hasTies ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <Section title="Details"><Facts rows={facts} /></Section>
        {hasTies && (
          <Section title="Ties">
            <Panel className="space-y-4 px-5 py-4">
              {allies.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Allies <span className="text-zinc-500">{allies.length}</span></p>
                  <p className="mt-1 text-[15px] leading-relaxed text-zinc-100">{allies.join(' · ')}</p>
                </div>
              )}
              {enemies.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-rose-400">Enemies <span className="text-zinc-500">{enemies.length}</span></p>
                  <p className="mt-1 text-[15px] leading-relaxed text-zinc-100">{enemies.join(' · ')}</p>
                </div>
              )}
              {lineage.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-violet-400">Lineage</p>
                  {lineage.map((l) => <p key={l} className="mt-1 text-[15px] text-zinc-100">{l}</p>)}
                </div>
              )}
            </Panel>
          </Section>
        )}
      </div>

      {sets.length > 0 && (
        <Section title="Sets" count={sets.length}>
          <div className="grid grid-cols-3 gap-2">
            {sets.map((s) => {
              const aka = nonPrimaryVariantsText(s.name_variants)
              return (
                <div key={s.id} className="flex min-w-0 items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2">
                  <ShareImg src={s.primary_photo_thumb_url} fallback={s.name} className="h-11 w-11 shrink-0 rounded-md text-sm" />
                  <div className="min-w-0">
                    <p className="truncate text-[15px] font-medium leading-tight text-zinc-100">{s.emojis?.[0] ? `${s.emojis[0]} ` : ''}{s.name}</p>
                    <p className="mt-0.5 truncate text-xs text-zinc-400">{s.member_count} members{aka && ` · ${aka}`}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </Section>
      )}

      {members.length > 0 && (
        <Section title="Members" count={members.length}>
          <div className="grid grid-cols-4 gap-2">
            {members.map((m) => (
              <MemberChip key={m.id} m={m} setNames={currentAffiliations(m.affiliations).filter((a) => setIds.has(a.set_id)).map((a) => a.set_name).join(', ')} />
            ))}
          </div>
        </Section>
      )}

      {incidents.length > 0 && (
        <Section title="Incidents" count={incidents.length}><IncidentsTable incidents={incidents} /></Section>
      )}

      {cases.length > 0 && (
        <Section title="Court cases" count={cases.length}><CourtCasesTable cases={cases} /></Section>
      )}

      <PhotoGrid urls={photos} label={alliance.name} />
    </CardShell>
  )
}
