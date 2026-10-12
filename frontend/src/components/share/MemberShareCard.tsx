import { useEffect, useMemo } from 'react'
import { useQueries } from '@tanstack/react-query'
import { Mic, Rat, Skull } from 'lucide-react'
import { api } from '@/lib/api'
import { formatFuzzyDate } from '@/components/FuzzyDate'
import { useCourtCasesFor, useMedia, useMember, useMemberIncidents } from '@/lib/queries'
import type { MemberRead, UUID } from '@/lib/types'
import { MEMBER_STATUS_CHIP } from '@/lib/statusColors'
import { INCIDENT_TYPE_LABEL, OUTCOME_LABEL, ROLE_CHIP, ROLE_LABEL } from '@/lib/incidentColors'
import {
  controllingSpell, formatTermRange, groupIncarcerations, incarcerationStatus, parseSentenceNotes,
} from '@/lib/incarceration'
import { custodyShort, otherCustodyIds } from '@/lib/custody'
import { socialEntries, socialHandle } from '@/lib/social'
import { ageFromFuzzyDates, currentAffiliations, fuzzyDateSortKey, primaryAffiliation } from '@/lib/utils'
import { familyDictToEntries, ROLE_LABEL_PLURAL, type FamilyRole } from '@/components/members/MemberFormSheet'
import { CardShell, Chip, Dash, Facts, Panel, PhotoGrid, Prose, Section, ShareImg, StatGrid } from './ShareCardParts'
import { CourtCasesTable, IncidentsTable } from './ShareTables'

const RANK_LABEL: Record<string, string> = { CEO: 'CEO', CO_CEO: 'Co-CEO' }
const FAMILY_ORDER: FamilyRole[] = ['spouse', 'parent', 'child', 'sibling', 'cousin', 'uncle', 'nephew']
const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

export interface ShareCardProps {
  id: UUID
  universeId: UUID
  universeName: string | null
  onReady: () => void
}

/** Everything the member page holds, laid out as one image. Sources are left
 *  off on purpose: they are research provenance, not part of what is sent. */
export default function MemberShareCard({ id, universeId, universeName, onReady }: ShareCardProps) {
  const memberQ = useMember(id, universeId)
  const incidentsQ = useMemberIncidents(id, universeId)
  const casesQ = useCourtCasesFor('member_id', id, universeId)
  const mediaQ = useMedia('member', id, universeId)
  const member = memberQ.data

  const family = useMemo(() => familyDictToEntries((member?.family as Record<string, unknown> | null) ?? null), [member?.family])
  const relativesQ = useQueries({
    queries: Array.from(new Set(family.map((e) => e.memberId))).map((rid) => ({
      queryKey: ['members', rid],
      queryFn: () => api.get<MemberRead>(`/members/${rid}?universe_id=${universeId}`),
      staleTime: 30_000,
    })),
    combine: (results) => ({
      byId: Object.fromEntries(results.flatMap((r) => (r.data ? [[r.data.id, r.data]] : []))) as Record<UUID, MemberRead>,
      pending: results.some((r) => r.isLoading),
    }),
  })

  const settled = !!member && !incidentsQ.isLoading && !casesQ.isLoading && !mediaQ.isLoading && !relativesQ.pending
  useEffect(() => {
    if (settled) onReady()
  }, [settled, onReady])

  if (!member) return null

  const incidents = [...(incidentsQ.data?.items ?? [])].sort((a, b) => fuzzyDateSortKey(b.date).localeCompare(fuzzyDateSortKey(a.date)))
  const cases = casesQ.data ?? []
  const photos = [...(mediaQ.data ?? [])]
    .sort((a, b) => Number(b.is_primary) - Number(a.is_primary))
    .flatMap((m) => (m.thumb_url ?? m.url ? [m.thumb_url ?? m.url!] : []))
  const headPhoto = (mediaQ.data ?? []).find((m) => m.is_primary)?.url ?? member.primary_photo_url

  const primaryAff = primaryAffiliation(member.affiliations)
  const otherCurrent = currentAffiliations(member.affiliations).filter((a) => a.set_id !== primaryAff?.set_id)
  const past = member.affiliations.filter((a) => !currentAffiliations([a]).length)
  const aliasNames = [...(member.aliases ?? []), ...member.aliases_detail.map((a) => a.alias)]
    .filter((v, i, arr) => v && arr.indexOf(v) === i)
  const showLegal = !member.nickname_unknown && member.nickname && member.legal_name && member.legal_name !== member.display_name
  const stats = member.stats
  const age = member.dob?.year ? ageFromFuzzyDates(member.dob, member.status === 'DEAD' ? member.date_of_death : null) : null
  const groups = groupIncarcerations(member.incarcerations)
  const socials = socialEntries(member.social_media)
  const custody = [
    member.mdoc_number && `MDOC ${member.mdoc_number}`,
    member.bop_register_number && `BOP ${member.bop_register_number}`,
    ...otherCustodyIds(member).map((c) => `${custodyShort(c.system)} ${c.number}`),
  ].filter(Boolean) as string[]

  const facts: [string, React.ReactNode][] = []
  facts.push(['Status', titleCase(member.status)])
  if (primaryAff) facts.push(['Set', <>{primaryAff.set_name}{primaryAff.rank && <span className="ml-2 text-zinc-400">{RANK_LABEL[primaryAff.rank] ?? primaryAff.rank}</span>}</>])
  if (otherCurrent.length) facts.push(['Also in', otherCurrent.map((a) => a.set_name).join(', ')])
  if (past.length) {
    facts.push(['Formerly', (
      <span className="flex flex-col">
        {past.map((a) => (
          <span key={a.id ?? a.set_id}>
            {a.set_name}
            {(a.from_date?.year || a.until_date?.year) && (
              <span className="ml-2 tabular-nums text-zinc-400">{a.from_date?.year ?? '?'} to {a.until_date?.year ?? '?'}</span>
            )}
          </span>
        ))}
      </span>
    )])
  }
  if (member.alliance_name) facts.push(['Alliance', member.alliance_name])
  if (member.dob) facts.push(['Born', <>{formatFuzzyDate(member.dob) ?? 'Unknown'}{age !== null && <span className="ml-2 text-zinc-400">{member.status === 'DEAD' ? `died aged ${age}` : `age ${age}`}</span>}</>])
  if (member.status === 'DEAD') facts.push(['Died', formatFuzzyDate(member.date_of_death) ?? 'Unknown'])
  if (custody.length) facts.push(['Custody no.', <span className="flex flex-col font-mono text-sm">{custody.map((c) => <span key={c}>{c}</span>)}</span>])
  if (socials.length) {
    facts.push(['Social', (
      <span className="flex flex-col">
        {socials.map((s) => <span key={s.key}><span className="text-zinc-400">{s.platform.charAt(0).toUpperCase() + s.platform.slice(1)}</span> {socialHandle(s.raw)}</span>)}
      </span>
    )])
  }

  const familyGroups = FAMILY_ORDER
    .map((role) => ({ role, names: family.filter((e) => e.role === role).map((e) => relativesQ.byId[e.memberId]?.display_name).filter(Boolean) as string[] }))
    .filter((g) => g.names.length > 0)

  return (
    <CardShell universeName={universeName}>
      {/* Who */}
      <header className="flex items-start gap-8">
        <ShareImg src={headPhoto} fallback={member.display_name} className="h-64 w-64 shrink-0 rounded-2xl text-6xl ring-1 ring-zinc-700" />
        <div className="min-w-0 flex-1 pt-1">
          <h1 className="text-6xl font-bold leading-[1.05] tracking-tight text-white">{member.display_name}</h1>
          {showLegal && <p className="mt-2 text-2xl text-zinc-300">{member.legal_name}</p>}
          {aliasNames.length > 0 && <p className="mt-1.5 text-lg text-zinc-400">a/k/a {aliasNames.join(' · ')}</p>}
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <Chip className={MEMBER_STATUS_CHIP[member.status]}>{titleCase(member.status)}</Chip>
            {primaryAff && (
              <Chip className="bg-violet-950/70 text-violet-200 ring-1 ring-violet-700/50">
                {primaryAff.set_name}{primaryAff.rank && <span className="text-violet-300/80">· {RANK_LABEL[primaryAff.rank] ?? primaryAff.rank}</span>}
              </Chip>
            )}
            {member.alliance_name && <Chip className="bg-blue-950/70 text-blue-200 ring-1 ring-blue-800/50">{member.alliance_name}</Chip>}
            {member.is_rapper && <Chip className="bg-fuchsia-950/60 text-fuchsia-300 ring-1 ring-fuchsia-800/60"><Mic className="h-4 w-4" />Rapper</Chip>}
            {member.is_snitch && <Chip className="bg-amber-950/60 text-amber-300 ring-1 ring-amber-800/60"><Rat className="h-4 w-4" />Snitch</Chip>}
          </div>
        </div>
      </header>

      {member.status === 'DEAD' && member.killed_in && (
        <div className="flex items-center gap-4 rounded-xl border border-rose-900/70 bg-rose-950/40 px-6 py-4">
          <Skull className="h-7 w-7 shrink-0 text-rose-400" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-rose-400">Killed</p>
            <p className="mt-0.5 text-lg text-zinc-100">
              {INCIDENT_TYPE_LABEL[member.killed_in.type]}
              {formatFuzzyDate(member.killed_in.date) && <span className="text-zinc-300"> · {formatFuzzyDate(member.killed_in.date)}</span>}
              {member.killed_in.municipality_name && <span className="text-zinc-300"> · {member.killed_in.municipality_name}</span>}
            </p>
          </div>
        </div>
      )}

      {stats && stats.shootings + stats.assists + stats.kills + stats.times_shot_survived > 0 && (
        <StatGrid cells={[
          { label: 'Shootings', value: stats.shootings, accent: 'text-amber-400' },
          { label: 'Assists', value: stats.assists, accent: 'text-violet-400' },
          { label: 'Kills', value: stats.kills, accent: 'text-rose-400' },
          { label: 'Shot, survived', value: stats.times_shot_survived, accent: 'text-emerald-400' },
        ]} />
      )}

      {member.biography && <Prose text={member.biography} />}

      <div className={`grid items-start gap-6 ${familyGroups.length > 0 ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <Section title="Details"><Facts rows={facts} /></Section>
        {familyGroups.length > 0 && (
          <Section title="Family">
            <Panel className="space-y-3 px-5 py-4">
              {familyGroups.map((g) => (
                <div key={g.role}>
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{ROLE_LABEL_PLURAL[g.role]}</p>
                  <p className="mt-0.5 text-[15px] text-zinc-100">{g.names.join(', ')}</p>
                </div>
              ))}
            </Panel>
          </Section>
        )}
      </div>

      {incidents.length > 0 && (
        <Section title="Incidents" count={incidents.length}>
          <IncidentsTable
            incidents={incidents}
            role={(inc) => inc.viewer_role ? (
              <span className="inline-flex flex-wrap items-center gap-1.5">
                <span className={`rounded-md border px-2 py-0.5 text-xs font-medium ${ROLE_CHIP[inc.viewer_role]}`}>{ROLE_LABEL[inc.viewer_role]}</span>
                {inc.viewer_outcome && inc.viewer_outcome !== 'UNKNOWN' && <span className="text-xs text-zinc-400">{OUTCOME_LABEL[inc.viewer_outcome]}</span>}
              </span>
            ) : <Dash />}
          />
        </Section>
      )}

      {groups.length > 0 && (
        <Section title="Incarceration" count={groups.length}>
          <Panel className="overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 bg-zinc-900 text-xs uppercase tracking-wider text-zinc-400">
                  <th className="px-4 py-2.5 font-medium">Offense</th>
                  <th className="px-4 py-2.5 font-medium">Sentenced</th>
                  <th className="px-4 py-2.5 font-medium">Term</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="px-4 py-2.5 font-medium">Facility</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {groups.map((g) => {
                  const head = parseSentenceNotes(controllingSpell(g).notes)
                  const term = formatTermRange(head.minimum, head.maximum)
                  const status = incarcerationStatus(g)
                  return (
                    <tr key={g.key} className="align-top">
                      <td className="px-4 py-2.5 text-zinc-100">
                        {head.offense ?? g.caseId ?? 'Sentence'}
                        {(head.county || (head.offense && g.caseId) || g.spells.length > 1) && (
                          <span className="block text-xs text-zinc-400">
                            {[head.county && `${head.county} County`, head.offense && g.caseId && `#${g.caseId}`, g.spells.length > 1 && `${g.spells.length} counts`].filter(Boolean).join(' · ')}
                          </span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-2.5 tabular-nums text-zinc-300">{formatFuzzyDate(g.from) ?? <Dash />}</td>
                      <td className="whitespace-nowrap px-4 py-2.5 font-mono text-xs text-zinc-300">{g.lifeSentence ? 'Life' : term ?? <Dash />}</td>
                      <td className="whitespace-nowrap px-4 py-2.5">
                        {status === 'discharged' ? <span className="text-zinc-400">Out {formatFuzzyDate(g.to) ?? ''}</span>
                          : status === 'life' ? <span className="font-medium text-rose-400">Life</span>
                          : status === 'projected' ? <span className="text-amber-300">Serving{g.earliestRelease && <span className="block text-xs text-zinc-400">earliest out {formatFuzzyDate(g.earliestRelease)}</span>}{g.maxDischarge && <span className="block text-xs text-zinc-400">max {formatFuzzyDate(g.maxDischarge)}</span>}</span>
                          : <span className="italic text-zinc-400">No discharge recorded</span>}
                      </td>
                      <td className="px-4 py-2.5 text-zinc-300">{g.facility ?? <Dash />}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Panel>
        </Section>
      )}

      {cases.length > 0 && (
        <Section title="Court cases" count={cases.length}><CourtCasesTable cases={cases} /></Section>
      )}

      <PhotoGrid urls={photos} label={member.display_name} />
    </CardShell>
  )
}
