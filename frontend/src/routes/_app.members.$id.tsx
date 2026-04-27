import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import {
  AlertTriangle, CheckCircle2, Copy, Download, ExternalLink, Heart,
  Pencil, Plus, Skull, Trash2,
} from 'lucide-react'
import { FacebookIcon, InstagramIcon, TwitterIcon } from '@/components/icons/SocialIcons'
import { lazy, Suspense, useState } from 'react'
import { toast } from 'sonner'
import { FuzzyDate } from '@/components/FuzzyDate'
import { MemberIdentity } from '@/components/MemberIdentity'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  useMember, useMemberStats, useSets, useAlliances,
  useDeleteMember, useMemberIncidents, useAllMembers,
} from '@/lib/queries'
import type { IncidentListItem, MemberListItem, MemberRead } from '@/lib/types'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { downloadText } from '@/lib/download'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { MemberFormSheet, familyDictToEntries, ROLE_LABEL } from './_app.members.index'
import type { FamilyRole } from './_app.members.index'
import { AddFamilyRelativeDialog } from '@/components/AddFamilyRelativeDialog'

const MemberFamilyGraph = lazy(() =>
  import('@/components/graphs/MemberFamilyGraph').then((m) => ({ default: m.MemberFamilyGraph })),
)
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'
import { IncidentFormSheet } from './_app.incidents.index'

const MemberTimeline = lazy(() =>
  import('@/components/graphs/MemberTimeline').then((m) => ({ default: m.MemberTimeline })),
)

export const Route = createFileRoute('/_app/members/$id')({
  component: MemberDetailPage,
})

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatPill({ label, value, accent = 'text-white' }: { label: string; value: number; accent?: string }) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <span className={`text-2xl font-bold tabular-nums ${accent}`}>{value}</span>
      <span className="mt-0.5 text-[11px] text-zinc-500">{label}</span>
    </div>
  )
}

function DetailRow({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-4 border-b border-zinc-800/70 py-2.5 last:border-0">
      <span className="w-32 shrink-0 text-xs text-zinc-500">{label}</span>
      <span className="text-sm text-zinc-200">{children}</span>
    </div>
  )
}

const SOCIAL_HOST_REGEX = /^https?:\/\/([^/]+)/i

function extractHost(url: string): string | null {
  const match = url.match(SOCIAL_HOST_REGEX)
  return match?.[1] ?? null
}

function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

const SOCIAL_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  facebook: FacebookIcon,
  instagram: InstagramIcon,
  twitter: TwitterIcon,
  x: TwitterIcon,
}

function socialUrl(platform: string, value: string): string | null {
  if (value.startsWith('http')) return isValidUrl(value) ? value : null
  const handle = value.replace(/^@/, '').trim()
  if (!handle) return null
  switch (platform.toLowerCase()) {
    case 'facebook': return `https://facebook.com/${handle}`
    case 'instagram': return `https://instagram.com/${handle}`
    case 'twitter':
    case 'x': return `https://x.com/${handle}`
    default: return null
  }
}

// ─── Family member inline link ─────────────────────────────────────────────────

function FamilyMemberLink({ memberId, member }: { memberId: string; member: MemberListItem | undefined }) {
  if (!member) {
    return <span className="text-xs text-zinc-600 font-mono">{memberId.slice(0, 8)}…</span>
  }
  return (
    <Link
      to="/members/$id"
      params={{ id: member.slug ?? member.id }}
      className="group inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2 transition-colors hover:border-zinc-700 hover:bg-zinc-900"
    >
      {member.photo_url ? (
        <img src={member.photo_url} alt={member.display_name} loading="lazy" decoding="async" className="h-6 w-6 rounded-full object-cover ring-1 ring-zinc-700" />
      ) : (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-800 text-[9px] font-bold text-zinc-400">
          {member.display_name.slice(0, 2).toUpperCase()}
        </div>
      )}
      <span className="text-sm text-zinc-300 group-hover:text-white">{member.display_name}</span>
      <MemberStatusBadge status={member.status} />
    </Link>
  )
}

// ─── Family tab content ────────────────────────────────────────────────────────

const ROLE_COLOR: Record<FamilyRole, string> = {
  father: 'text-amber-400',
  son: 'text-sky-400',
  brother: 'text-violet-400',
  cousin: 'text-emerald-400',
  uncle: 'text-orange-400',
  nephew: 'text-pink-400',
}

const ROLE_TOOLTIP: Record<FamilyRole, string> = {
  father: 'Biological or adoptive father',
  son: 'Male child of this member',
  brother: 'Brother (shared parent)',
  cousin: 'Shares a grandparent',
  uncle: "Sibling of this member's parent",
  nephew: "Child of this member's sibling",
}

function FamilyTab({ family, universeId }: { family: Record<string, unknown> | null; universeId: string }) {
  const { data: allMembers } = useAllMembers(universeId)
  const memberMap: Record<string, MemberListItem> = Object.fromEntries(
    (allMembers?.items ?? []).map((m) => [m.id, m])
  )

  const entries = familyDictToEntries(family)
  const grouped = (['father', 'son', 'brother', 'cousin', 'uncle', 'nephew'] as FamilyRole[])
    .map((role) => ({ role, ids: entries.filter((e) => e.role === role).map((e) => e.memberId) }))
    .filter((g) => g.ids.length > 0)

  if (grouped.length === 0) {
    return <p className="py-6 text-sm text-zinc-600">No family links recorded.</p>
  }

  return (
    <div className="space-y-5">
      {grouped.map(({ role, ids }) => (
        <div key={role}>
          <div className="mb-2 flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <span className={`inline-flex items-center gap-2 ${ROLE_COLOR[role]}`}>
                  <Heart className="h-3 w-3" />
                  <span className="text-xs font-semibold uppercase tracking-wider">
                    {ROLE_LABEL[role]}{ids.length > 1 ? 's' : ''}
                  </span>
                </span>
              </TooltipTrigger>
              <TooltipContent side="right">{ROLE_TOOLTIP[role]}</TooltipContent>
            </Tooltip>
          </div>
          <div className="flex flex-wrap gap-2">
            {ids.map((id) => (
              <FamilyMemberLink key={id} memberId={id} member={memberMap[id]} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Markdown export ──────────────────────────────────────────────────────────

const MD_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatFuzzyDateText(value: FuzzyDateValue | null | undefined, fallback = 'Unknown'): string {
  if (!value || value.precision === 'UNKNOWN') return fallback
  const prefix = value.approx ? 'c. ' : ''
  if (value.precision === 'YMD' && value.year && value.month && value.day)
    return `${prefix}${MD_MONTHS[value.month - 1]} ${value.day}, ${value.year}`
  if (value.precision === 'YM' && value.year && value.month)
    return `${prefix}${MD_MONTHS[value.month - 1]} ${value.year}`
  if (value.precision === 'Y' && value.year)
    return `${prefix}${value.year}`
  return fallback
}

function buildMemberMarkdown({
  member, setName, allianceName, family, incidents,
}: {
  member: MemberRead
  setName: string | null
  allianceName: string | null
  family: { role: FamilyRole; name: string }[]
  incidents: IncidentListItem[]
}): string {
  const lines: string[] = []
  lines.push(`# ${member.display_name}`)
  if (member.legal_name && member.legal_name !== member.display_name) {
    lines.push('')
    lines.push(`*Legal name: ${member.legal_name}*`)
  }
  lines.push('')

  lines.push('## Identity')
  lines.push('')
  lines.push(`- **Status:** ${member.status}`)
  if (member.dob) lines.push(`- **Date of birth:** ${formatFuzzyDateText(member.dob)}`)
  if (member.date_of_death) lines.push(`- **Date of death:** ${formatFuzzyDateText(member.date_of_death)}`)
  if (setName) lines.push(`- **Set:** ${setName}`)
  if (allianceName) lines.push(`- **Alliance:** ${allianceName}`)
  if (member.aliases && member.aliases.length > 0) {
    lines.push(`- **Aliases:** ${member.aliases.join(', ')}`)
  }
  lines.push('')

  if (member.biography) {
    lines.push('## Biography')
    lines.push('')
    lines.push(member.biography)
    lines.push('')
  }

  if (family.length > 0) {
    lines.push('## Family')
    lines.push('')
    const grouped: Record<string, string[]> = {}
    for (const { role, name } of family) {
      (grouped[role] ??= []).push(name)
    }
    for (const role of (['father', 'son', 'brother', 'cousin', 'uncle', 'nephew'] as FamilyRole[])) {
      const names = grouped[role]
      if (!names) continue
      const label = ROLE_LABEL[role] + (names.length > 1 ? 's' : '')
      lines.push(`- **${label}:** ${names.join(', ')}`)
    }
    lines.push('')
  }

  if (incidents.length > 0) {
    lines.push(`## Incidents (${incidents.length})`)
    lines.push('')
    for (const inc of incidents) {
      const dateStr = formatFuzzyDateText(inc.date, 'Date unknown')
      const victims = inc.victim_names.length > 0 ? ` — Victims: ${inc.victim_names.join(', ')}` : ''
      const verified = inc.verified ? ' [verified]' : ''
      lines.push(`- ${dateStr} — ${inc.type}${victims}${verified}`)
    }
    lines.push('')
  }

  const social = member.social_media as Record<string, string> | null | undefined
  if (social && Object.values(social).some((v) => v)) {
    lines.push('## Social')
    lines.push('')
    for (const [k, v] of Object.entries(social)) {
      if (v) lines.push(`- **${k.charAt(0).toUpperCase() + k.slice(1)}:** ${v}`)
    }
    lines.push('')
  }

  return lines.join('\n').trimEnd() + '\n'
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function MemberDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: member, isLoading, isError, refetch } = useMember(id, universe?.id ?? null)
  const { data: stats } = useMemberStats(id, universe?.id ?? null)
  const { data: allSets } = useSets(universe?.id ?? null)
  const { data: allAlliances } = useAlliances(universe?.id ?? null)
  const { data: incidents } = useMemberIncidents(id, universe?.id ?? null)

  useRecordRecent(member ? { type: 'member', id: member.id, slug: member.slug, label: member.display_name } : null)

  const deleteMember = useDeleteMember(universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [duplicating, setDuplicating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [creatingIncident, setCreatingIncident] = useState(false)
  const [addingFamily, setAddingFamily] = useState(false)
  const [familyView, setFamilyView] = useState<'list' | 'graph'>('list')

  useEditShortcut(() => member && setEditing(true))

  const setName = (sid: string) => (allSets?.items ?? []).find((s) => s.id === sid)?.name ?? sid
  const setSlug = (sid: string) => (allSets?.items ?? []).find((s) => s.id === sid)?.slug ?? sid
  const allianceName = (aid: string) => (allAlliances?.items ?? []).find((a) => a.id === aid)?.name ?? aid

  async function handleDelete() {
    if (!member) return
    try {
      await deleteMember.mutateAsync(member.id)
      navigate({ to: '/members' })
    } catch (err) {
      setDeleting(false)
      toast.error(err instanceof Error ? err.message : 'Failed to delete member')
    }
  }

  const familyCount = member?.family ? familyDictToEntries(member.family as Record<string, unknown>).length : 0

  const { data: allMembers } = useAllMembers(universe?.id ?? null)

  function handleExport() {
    if (!member) return
    const memberMap: Record<string, string> = Object.fromEntries(
      (allMembers?.items ?? []).map((m) => [m.id, m.display_name]),
    )
    const familyEntries = familyDictToEntries(member.family as Record<string, unknown> | null)
      .map((e) => ({ role: e.role, name: memberMap[e.memberId] ?? e.memberId.slice(0, 8) + '…' }))
    const md = buildMemberMarkdown({
      member,
      setName: member.set_id ? setName(member.set_id) : null,
      allianceName: member.alliance_id ? allianceName(member.alliance_id) : null,
      family: familyEntries,
      incidents: incidents?.items ?? [],
    })
    const safeName = member.display_name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'member'
    downloadText(md, `${safeName}.md`, 'text/markdown;charset=utf-8')
  }

  if (isError) return <ErrorState title="Member not found" onRetry={() => refetch()} />

  return (
    <TooltipProvider delayDuration={200}>
    <div className="space-y-5">
      <Breadcrumbs
        items={[
          (() => {
            const memberSet = member?.set_id ? (allSets?.items ?? []).find((s) => s.id === member.set_id) : null
            return memberSet
              ? { label: memberSet.name, to: `/sets/${memberSet.slug ?? memberSet.id}` }
              : { label: 'Members', to: '/members' }
          })(),
          { label: member?.display_name ?? 'Member' },
        ]}
      />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : member ? (
        <>
          {/* Hero header */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="shrink-0">
                {member.photo_url ? (
                  <img
                    src={member.photo_url}
                    alt={`Photo of ${member.display_name}`}
                    loading="lazy"
                    decoding="async"
                    className="h-20 w-20 rounded-xl object-cover ring-1 ring-zinc-600/80 shadow-lg shadow-black/30"
                  />
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-zinc-800 text-2xl font-bold text-zinc-400 ring-1 ring-zinc-700">
                    {member.display_name.slice(0, 2).toUpperCase()}
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1">
                  <MemberIdentity member={member} showLegalName className="text-2xl font-bold" secondaryClassName="text-base mt-0.5" />
                  <CopyButton value={window.location.href} label="Copy link to this member" className="ml-1 opacity-60 hover:opacity-100" />
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <MemberStatusBadge status={member.status} />
                  {member.aliases && member.aliases.length > 0 && (
                    <span className="text-xs text-zinc-500">a.k.a. {member.aliases.join(', ')}</span>
                  )}
                </div>
                {(member.set_id || member.alliance_id) && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {member.set_id && (
                      <Link
                        to="/sets/$id"
                        params={{ id: setSlug(member.set_id) }}
                        className="rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors"
                      >
                        {setName(member.set_id)}
                      </Link>
                    )}
                    {member.alliance_id && (
                      <Link
                        to="/alliances/$id"
                        params={{ id: member.alliance_id }}
                        className="rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-blue-400 transition-colors"
                      >
                        {allianceName(member.alliance_id)}
                      </Link>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
              </Button>
              <Button size="sm" variant="outline" onClick={() => setDuplicating(true)}>
                <Copy className="mr-1.5 h-3.5 w-3.5" />Duplicate
              </Button>
              <Button size="sm" variant="outline" onClick={handleExport}>
                <Download className="mr-1.5 h-3.5 w-3.5" />Export
              </Button>
              {user?.global_role === 'ADMIN' && (
                <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
                </Button>
              )}
            </div>
          </div>

          {/* Stats row */}
          {stats && (() => {
            const hasAny = stats.shootings || stats.assists || stats.kills || stats.times_shot_survived
            return (
              <div>
                <div className="grid grid-cols-4 gap-2">
                  <StatPill label="Shootings" value={stats.shootings} accent="text-amber-400" />
                  <StatPill label="Assists" value={stats.assists} accent="text-violet-400" />
                  <StatPill label="Kills" value={stats.kills} accent="text-rose-400" />
                  <StatPill label="Survived" value={stats.times_shot_survived} accent="text-emerald-400" />
                </div>
                {!hasAny && (
                  <p className="mt-2 text-center text-xs text-zinc-600">No recorded incidents yet.</p>
                )}
              </div>
            )
          })()}

          {/* Tabs */}
          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="biography">Bio</TabsTrigger>
              <TabsTrigger value="family">
                Family
                {familyCount > 0 && (
                  <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-xs">{familyCount}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="incidents">
                Incidents
                {incidents && incidents.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-xs">{incidents.items.length}</Badge>
                )}
              </TabsTrigger>
              {incidents && incidents.items.length > 0 && (
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
              )}
            </TabsList>

            {/* Overview */}
            <TabsContent value="overview" className="mt-4 space-y-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-1">
                <DetailRow label="Date of Birth">
                  {member.dob ? <FuzzyDate value={member.dob} /> : <span className="text-zinc-600">Unknown</span>}
                </DetailRow>
                {member.status === 'DEAD' && (
                  <DetailRow label="Date of Death">
                    <span className="flex items-center gap-2">
                      <Skull className="h-3 w-3 text-zinc-500" />
                      {member.date_of_death ? <FuzzyDate value={member.date_of_death} /> : <span className="text-zinc-600">Unknown</span>}
                    </span>
                  </DetailRow>
                )}
                {member.status === 'LOCKED' && (member.life_sentence || member.release_date) && (
                  <DetailRow label="Release Date">
                    {member.life_sentence
                      ? <span className="font-medium text-rose-400">Life</span>
                      : <FuzzyDate value={member.release_date} />}
                  </DetailRow>
                )}
                <DetailRow label="Set">
                  {member.set_id ? (
                    <Link to="/sets/$id" params={{ id: setSlug(member.set_id) }} className="text-violet-400 hover:underline">
                      {setName(member.set_id)}
                    </Link>
                  ) : <span className="text-zinc-600">—</span>}
                </DetailRow>
                <DetailRow label="Alliance">
                  {member.alliance_id ? (
                    <Link to="/alliances/$id" params={{ id: member.alliance_id }} className="text-blue-400 hover:underline">
                      {allianceName(member.alliance_id)}
                    </Link>
                  ) : <span className="text-zinc-600">—</span>}
                </DetailRow>
              </div>

              {/* Social media */}
              {member.social_media && Object.keys(member.social_media).length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                  {Object.entries(member.social_media).map(([platform, handle]) => {
                    const raw = String(handle)
                    const url = socialUrl(platform, raw)
                    const display = raw.startsWith('http') ? (extractHost(raw) ?? raw) : `@${raw.replace(/^@/, '')}`
                    const Icon = SOCIAL_ICON[platform.toLowerCase()] ?? null
                    return (
                      <DetailRow
                        key={platform}
                        label={
                          <span className="inline-flex items-center gap-1.5 capitalize">
                            {Icon ? <Icon className="h-3.5 w-3.5 text-zinc-500" /> : null}
                            {platform}
                          </span>
                        }
                      >
                        {url ? (
                          <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sky-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500/50 rounded">
                            <span>{display}</span>
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : raw.startsWith('http') ? (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="inline-flex items-center gap-1 text-amber-400">
                                <AlertTriangle className="h-3 w-3" />
                                <span className="truncate">{raw}</span>
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side="right">Malformed URL — could not be parsed</TooltipContent>
                          </Tooltip>
                        ) : (
                          <span className="text-zinc-300">{raw}</span>
                        )}
                      </DetailRow>
                    )
                  })}
                </div>
              )}
            </TabsContent>

            {/* Biography */}
            <TabsContent value="biography" className="mt-4">
              {member.biography ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
                  <p className="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap">{member.biography}</p>
                </div>
              ) : (
                <p className="py-6 text-sm text-zinc-600">No biography recorded.</p>
              )}
            </TabsContent>

            {/* Family */}
            <TabsContent value="family" className="mt-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <div className="flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-900/60 p-1">
                  {(['list', 'graph'] as const).map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => setFamilyView(v)}
                      className={`rounded px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                        familyView === v ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'
                      }`}
                    >
                      {v === 'list' ? 'List' : 'Graph'}
                    </button>
                  ))}
                </div>
                <Button size="sm" variant="outline" onClick={() => setAddingFamily(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Family Member
                </Button>
              </div>
              {universe && familyView === 'list' && (
                <FamilyTab family={member.family as Record<string, unknown> | null} universeId={universe.id} />
              )}
              {universe && familyView === 'graph' && (
                <Suspense fallback={<Skeleton className="h-[480px] w-full" />}>
                  <MemberFamilyGraph
                    centerMember={member}
                    universeId={universe.id}
                    allMembers={allMembers?.items ?? []}
                  />
                </Suspense>
              )}
            </TabsContent>

            {/* Incidents */}
            <TabsContent value="incidents" className="mt-4">
              <div className="mb-3 flex justify-end">
                <Button size="sm" variant="outline" onClick={() => setCreatingIncident(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Incident
                </Button>
              </div>
              {!incidents || incidents.items.length === 0 ? (
                <p className="py-6 text-sm text-zinc-600">No incidents recorded.</p>
              ) : (
                <div className="overflow-hidden rounded-xl border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Date</th>
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Type</th>
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Victims</th>
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Verified</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {incidents.items.map((inc) => (
                        <tr key={inc.id} className="hover:bg-zinc-900/50 transition-colors">
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-zinc-300 hover:text-violet-400">
                              {inc.date ? <FuzzyDate value={inc.date} /> : '—'}
                            </Link>
                          </td>
                          <td className="px-4 py-3">
                            <Badge
                              variant="outline"
                              className={`text-xs ${inc.type === 'MURDER' ? 'border-rose-800 text-rose-400' : 'border-amber-800 text-amber-400'}`}
                            >
                              {inc.type}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-xs text-zinc-500">
                            {inc.victim_names.length > 0 ? inc.victim_names.join(', ') : '—'}
                          </td>
                          <td className="px-4 py-3">
                            {inc.verified ? (
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                                </TooltipTrigger>
                                <TooltipContent side="left">Verified incident</TooltipContent>
                              </Tooltip>
                            ) : <span className="text-zinc-600 text-xs">—</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="timeline" className="mt-4">
              <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                <MemberTimeline
                  incidents={incidents?.items ?? []}
                  dob={member.dob}
                  dateOfDeath={member.date_of_death}
                />
              </Suspense>
              <p className="mt-2 text-center text-[11px] text-zinc-600">Hover a dot for details, click to open the incident.</p>
            </TabsContent>
          </Tabs>

          {universe && (
            <MemberFormSheet universeId={universe.id} open={editing} onClose={() => setEditing(false)} initial={member} />
          )}
          {universe && duplicating && (
            <MemberFormSheet
              key={`dup-${member.id}`}
              universeId={universe.id}
              open={duplicating}
              onClose={() => setDuplicating(false)}
              copyFrom={{
                ...member,
                nickname: member.nickname ? `${member.nickname} (copy)` : member.nickname,
              }}
            />
          )}

          {universe && (
            <AddFamilyRelativeDialog
              member={member}
              universeId={universe.id}
              open={addingFamily}
              onClose={() => setAddingFamily(false)}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Member"
            description={`Permanently delete "${member.display_name}"? This cannot be undone.`}
            impact={incidents && incidents.items.length > 0 ? (
              <span>
                This member appears in <strong>{incidents.items.length}</strong> incident{incidents.items.length === 1 ? '' : 's'} and will be removed from each.
              </span>
            ) : null}
            confirmLabel="Delete"
            destructive
            pending={deleteMember.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />

          {universe && creatingIncident && (
            <IncidentFormSheet
              key={`new-incident-${member.id}`}
              universeId={universe.id}
              open={creatingIncident}
              onClose={() => setCreatingIncident(false)}
              defaultParticipants={[
                {
                  member_id: member.id,
                  member_name: member.display_name,
                  role: 'BYSTANDER',
                  outcome: 'UNKNOWN',
                },
              ]}
            />
          )}
        </>
      ) : null}
    </div>
    </TooltipProvider>
  )
}
