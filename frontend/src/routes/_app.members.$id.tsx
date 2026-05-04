import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import {
  AlertTriangle, CheckCircle2, Copy, Download, ExternalLink, GitFork,
  Pencil, Plus, Skull, Trash2, X,
} from 'lucide-react'
import { FacebookIcon, InstagramIcon, TwitterIcon } from '@/components/icons/SocialIcons'
import { lazy, Suspense, useState } from 'react'
import { toast } from 'sonner'
import { FuzzyDate } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { ageFromFuzzyDates, timeAgo } from '@/lib/utils'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  useMember, useMemberStats, useSets, useAlliances,
  useDeleteMember, useMemberIncidents, useAllMembers, useUpdateMember,
  useIncident, useMunicipality,
  useMemberAliases,
  useMemberIncarcerations, useCreateMemberIncarceration, useUpdateMemberIncarceration, useDeleteMemberIncarceration,
} from '@/lib/queries'
import type { IncidentListItem, MemberIncarcerationRead, MemberListItem, MemberRead } from '@/lib/types'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { downloadText } from '@/lib/download'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { MemberFormSheet, familyDictToEntries, ROLE_LABEL } from './_app.members.index'
import type { FamilyRole } from './_app.members.index'
import { AddFamilyRelativeDialog } from '@/components/AddFamilyRelativeDialog'
const PhotoGallery = lazy(() =>
  import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })),
)

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
      {member.primary_photo_thumb_url ? (
        <img src={member.primary_photo_thumb_url} alt={member.display_name} loading="lazy" decoding="async" className="h-6 w-6 rounded-full object-cover ring-1 ring-zinc-700" />
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

// ─── Incarceration form (shared by create + edit) ────────────────────────────

interface IncarcerationDraft {
  facility: string
  case_id: string
  notes: string
  from_date: FuzzyDateValue | null
  earliest_release_date: FuzzyDateValue | null
  max_discharge_date: FuzzyDateValue | null
  life_sentence: boolean
}

const EMPTY_INCARCERATION_DRAFT: IncarcerationDraft = {
  facility: '', case_id: '', notes: '',
  from_date: null, earliest_release_date: null, max_discharge_date: null,
  life_sentence: false,
}

function IncarcerationForm({
  draft, setDraft, onSubmit, onCancel, isPending, submitLabel, idPrefix,
}: {
  draft: IncarcerationDraft
  setDraft: React.Dispatch<React.SetStateAction<IncarcerationDraft>>
  onSubmit: () => Promise<void>
  onCancel: () => void
  isPending: boolean
  submitLabel: string
  idPrefix: string
}) {
  return (
    <form
      onSubmit={async (e) => { e.preventDefault(); await onSubmit() }}
      className="space-y-3 pb-1"
    >
      <Input
        value={draft.facility}
        onChange={(e) => setDraft((d) => ({ ...d, facility: e.target.value }))}
        placeholder="Facility name"
        className="h-7 text-sm"
      />
      <Input
        value={draft.case_id}
        onChange={(e) => setDraft((d) => ({ ...d, case_id: e.target.value }))}
        placeholder="Case number (optional)"
        className="h-7 text-sm"
      />
      <Input
        value={draft.notes}
        onChange={(e) => setDraft((d) => ({ ...d, notes: e.target.value }))}
        placeholder="Notes (optional)"
        className="h-7 text-sm"
      />
      <FuzzyDateInput
        idPrefix={`${idPrefix}-from`}
        label="From"
        value={draft.from_date}
        onChange={(v) => setDraft((d) => ({ ...d, from_date: v }))}
      />
      <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
        <input
          type="checkbox"
          checked={draft.life_sentence}
          onChange={(e) => setDraft((d) => ({ ...d, life_sentence: e.target.checked }))}
          className="h-3.5 w-3.5 rounded border-zinc-700 bg-zinc-900 accent-rose-600"
        />
        Life sentence (no release dates)
      </label>
      {!draft.life_sentence && (
        <>
          <FuzzyDateInput
            idPrefix={`${idPrefix}-earliest`}
            label="Earliest release date (state DOC only — leave blank for federal)"
            value={draft.earliest_release_date}
            onChange={(v) => setDraft((d) => ({ ...d, earliest_release_date: v }))}
          />
          <FuzzyDateInput
            idPrefix={`${idPrefix}-max`}
            label="Maximum discharge date"
            value={draft.max_discharge_date}
            onChange={(v) => setDraft((d) => ({ ...d, max_discharge_date: v }))}
          />
        </>
      )}
      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" size="sm" variant="ghost" className="h-7 px-2" onClick={onCancel}>
          <X className="h-3.5 w-3.5" />
        </Button>
        <Button type="submit" size="sm" className="h-7 px-3" disabled={isPending}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}

// ─── Family panel (right column) ──────────────────────────────────────────────

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

function FamilyPanel({
  family,
  universeId,
  familyCount,
  onAdd,
  onOpenGraph,
}: {
  family: Record<string, unknown> | null
  universeId: string
  familyCount: number
  onAdd: () => void
  onOpenGraph: () => void
}) {
  const { data: allMembers } = useAllMembers(universeId)
  const memberMap: Record<string, MemberListItem> = Object.fromEntries(
    (allMembers?.items ?? []).map((m) => [m.id, m])
  )

  const entries = familyDictToEntries(family)
  const grouped = (['father', 'son', 'brother', 'cousin', 'uncle', 'nephew'] as FamilyRole[])
    .map((role) => ({ role, ids: entries.filter((e) => e.role === role).map((e) => e.memberId) }))
    .filter((g) => g.ids.length > 0)

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-3">
      <div className="mb-2.5 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Family</p>
        <div className="flex items-center gap-3">
          {familyCount > 0 && (
            <button
              type="button"
              onClick={onOpenGraph}
              className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-violet-400 transition-colors"
            >
              <GitFork className="h-3 w-3" />Graph
            </button>
          )}
          <button
            type="button"
            onClick={onAdd}
            className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-violet-400 transition-colors"
          >
            <Plus className="h-3 w-3" />Add
          </button>
        </div>
      </div>

      {grouped.length === 0 ? (
        <p className="text-xs text-zinc-600">No family links recorded.</p>
      ) : (
        <div className="space-y-3">
          {grouped.map(({ role, ids }) => (
            <div key={role}>
              <div className="mb-1.5 flex items-center gap-1.5">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className={`text-[10px] font-semibold uppercase tracking-wider ${ROLE_COLOR[role]}`}>
                      {ROLE_LABEL[role]}{ids.length > 1 ? 's' : ''}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent side="right">{ROLE_TOOLTIP[role]}</TooltipContent>
                </Tooltip>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {ids.map((memberId) => (
                  <FamilyMemberLink key={memberId} memberId={memberId} member={memberMap[memberId]} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
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
  member, setName, allianceName, family, incidents, killedIn,
}: {
  member: MemberRead
  setName: string | null
  allianceName: string | null
  family: { role: FamilyRole; name: string }[]
  incidents: IncidentListItem[]
  killedIn: { type: string; date: FuzzyDateValue | null } | null
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
  if (killedIn) {
    const dateStr = killedIn.date ? formatFuzzyDateText(killedIn.date) : 'date unknown'
    lines.push(`- **Killed in:** ${killedIn.type} (${dateStr})`)
  }
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
  const { data: stats } = useMemberStats(member?.id ?? '', universe?.id ?? null)
  const { data: allSets } = useSets(universe?.id ?? null)
  const { data: allAlliances } = useAlliances(universe?.id ?? null)
  const memberUuid = member?.id ?? null
  const { data: incidents } = useMemberIncidents(memberUuid, universe?.id ?? null)
  const { data: aliases } = useMemberAliases(memberUuid, universe?.id ?? null)
  const { data: incarcerations } = useMemberIncarcerations(memberUuid, universe?.id ?? null)
  const createIncarceration = useCreateMemberIncarceration(memberUuid ?? '', universe?.id ?? '')
  const updateIncarceration = useUpdateMemberIncarceration(memberUuid ?? '', universe?.id ?? '')
  const deleteIncarceration = useDeleteMemberIncarceration(memberUuid ?? '', universe?.id ?? '')
  const [editingSpellId, setEditingSpellId] = useState<string | null>(null)
  const { data: killingIncident } = useIncident(
    member?.death_incident_id ?? '',
    member?.death_incident_id ? (universe?.id ?? null) : null,
  )
  const { data: killingMuni } = useMunicipality(
    killingIncident?.municipality_id ?? '',
    killingIncident?.municipality_id ? (universe?.id ?? null) : null,
  )

  useRecordRecent(member ? { type: 'member', id: member.id, slug: member.slug, label: member.display_name } : null)

  const deleteMember = useDeleteMember(universe?.id ?? '')
  const updateMember = useUpdateMember(memberUuid ?? '', universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [duplicating, setDuplicating] = useState(false)
  const [addingIncarceration, setAddingIncarceration] = useState(false)
  const [incarcerationDraft, setIncarcerationDraft] = useState<IncarcerationDraft>(EMPTY_INCARCERATION_DRAFT)
  const [deleting, setDeleting] = useState(false)
  const [creatingIncident, setCreatingIncident] = useState(false)
  const [addingFamily, setAddingFamily] = useState(false)
  const [familyGraphOpen, setFamilyGraphOpen] = useState(false)
  const [incidentsView, setIncidentsView] = useState<'list' | 'timeline'>('list')
  const [editingBio, setEditingBio] = useState(false)
  const [bioDraft, setBioDraft] = useState('')

  function startBioEdit() {
    setBioDraft(member?.biography ?? '')
    setEditingBio(true)
  }

  async function saveBio() {
    try {
      await updateMember.mutateAsync({ biography: bioDraft })
      toast.success('Biography updated')
      setEditingBio(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save biography')
    }
  }

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
      killedIn: killingIncident
        ? { type: killingIncident.type, date: killingIncident.date }
        : null,
    })
    const safeName = member.display_name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'member'
    downloadText(md, `${safeName}.md`, 'text/markdown;charset=utf-8')
  }

  const isAdmin = user?.global_role === 'ADMIN'
  const hasSocial = !!(member?.social_media && Object.values(member.social_media as Record<string, string>).some((v) => v))
  const hasIncarcerationPanel = (incarcerations && incarcerations.length > 0) || isAdmin
  const incidentCount = incidents?.items.length ?? 0
  const allStatsZero = !stats || (stats.shootings + stats.assists + stats.kills + stats.times_shot_survived === 0)

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
                {member.primary_photo_url ? (
                  <img
                    src={member.primary_photo_url}
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
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold leading-none text-white">
                    {member.display_name}
                    {!member.nickname_unknown && member.nickname && member.legal_name && member.legal_name !== member.display_name && (
                      <span className="ml-2 text-lg font-medium text-zinc-400">({member.legal_name})</span>
                    )}
                  </h1>
                  <CopyButton value={window.location.href} label="Copy link" className="opacity-40 hover:opacity-100" />
                </div>
                {(() => {
                  const aliasNames = [
                    ...(member.aliases ?? []),
                    ...((aliases ?? []).map((a) => a.alias)),
                  ].filter((v, i, arr) => v && arr.indexOf(v) === i)
                  return aliasNames.length > 0 ? (
                    <p className="mt-1 text-sm text-zinc-500">a/k/a {aliasNames.join(' · ')}</p>
                  ) : null
                })()}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <MemberStatusBadge status={member.status} />
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
                  <span className="text-[11px] text-zinc-600">Updated {timeAgo(member.updated_at)}</span>
                </div>
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
              {isAdmin && (
                <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
                </Button>
              )}
            </div>
          </div>

          {/* Killed-in card */}
          {member.status === 'DEAD' && member.death_incident_id && (
            <Link
              to="/incidents/$id"
              params={{ id: member.death_incident_id }}
              className="group flex items-center gap-3 rounded-xl border border-rose-900/60 bg-rose-950/30 px-4 py-3 transition-colors hover:border-rose-700 hover:bg-rose-950/50"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-rose-950/80">
                <Skull className="h-4 w-4 text-rose-400" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs uppercase tracking-wider text-rose-400">Killed in incident</p>
                <p className="mt-0.5 text-sm text-zinc-200">
                  {killingIncident ? (
                    <>
                      <span className="font-medium">{killingIncident.type}</span>
                      {killingIncident.date && (
                        <span className="text-zinc-400"> · <FuzzyDate value={killingIncident.date} /></span>
                      )}
                      {killingMuni && (
                        <span className="text-zinc-400"> · {killingMuni.name}</span>
                      )}
                    </>
                  ) : (
                    <span className="text-zinc-500">Loading incident…</span>
                  )}
                </p>
              </div>
              <span className="text-xs text-rose-400 opacity-0 transition-opacity group-hover:opacity-100">View →</span>
            </Link>
          )}

          {/* Biography — inline under hero */}
          {editingBio ? (
            <div className="space-y-2">
              <Textarea
                rows={10}
                value={bioDraft}
                onChange={(e) => setBioDraft(e.target.value)}
                placeholder="Background notes…"
                autoFocus
              />
              <div className="flex justify-end gap-2">
                <Button size="sm" variant="outline" onClick={() => setEditingBio(false)} disabled={updateMember.isPending}>Cancel</Button>
                <Button size="sm" onClick={saveBio} disabled={updateMember.isPending}>
                  {updateMember.isPending ? 'Saving…' : 'Save'}
                </Button>
              </div>
            </div>
          ) : member.biography ? (
            <div className="group relative rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
              <p className="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap">{member.biography}</p>
              <button type="button" onClick={startBioEdit} aria-label="Edit biography"
                className="absolute right-2 top-2 rounded p-1.5 text-zinc-500 opacity-0 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 focus-visible:opacity-100 group-hover:opacity-100">
                <Pencil className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button type="button" onClick={startBioEdit}
              className="flex w-full items-center gap-2 rounded-xl border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-600 hover:border-zinc-700 hover:text-zinc-400 transition-colors">
              <Pencil className="h-3 w-3" />Add biography
            </button>
          )}

          {/* Stats row */}
          {stats && !allStatsZero && (
            <div className="grid grid-cols-4 gap-2">
              <StatPill label="Shootings" value={stats.shootings} accent="text-amber-400" />
              <StatPill label="Assists" value={stats.assists} accent="text-violet-400" />
              <StatPill label="Kills" value={stats.kills} accent="text-rose-400" />
              <StatPill label="Survived" value={stats.times_shot_survived} accent="text-emerald-400" />
            </div>
          )}

          {/* Two-column wiki layout: identity facts + right panels */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_280px]">
            {/* Left: identity facts */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-1">
              <DetailRow label="Date of Birth">
                {member.dob ? (
                  <span className="flex items-center gap-2 flex-wrap">
                    <FuzzyDate value={member.dob} />
                    {member.dob.year && (() => {
                      const age = ageFromFuzzyDates(member.dob!, member.status === 'DEAD' ? member.date_of_death : null)
                      if (age === null) return null
                      return (
                        <span className="text-xs text-zinc-500">
                          {member.status === 'DEAD' ? `died aged ${age}` : `${age} years old`}
                        </span>
                      )
                    })()}
                  </span>
                ) : <span className="text-zinc-600">Unknown</span>}
              </DetailRow>
              {member.status === 'DEAD' && (
                <DetailRow label="Date of Death">
                  <span className="flex items-center gap-2">
                    <Skull className="h-3 w-3 text-zinc-500" />
                    {member.date_of_death ? <FuzzyDate value={member.date_of_death} /> : <span className="text-zinc-600">Unknown</span>}
                  </span>
                </DetailRow>
              )}
              <DetailRow label="Alliance">
                {member.alliance_id ? (
                  <Link to="/alliances/$id" params={{ id: member.alliance_id }} className="text-blue-400 hover:underline">
                    {allianceName(member.alliance_id)}
                  </Link>
                ) : <span className="text-zinc-600">—</span>}
              </DetailRow>
            </div>

            {/* Right: incarceration (top for LOCKED) + family + social */}
            {universe && (
              <div className="space-y-4">
                {hasIncarcerationPanel && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Incarceration</p>
                      {isAdmin && (
                        <button type="button" onClick={() => setAddingIncarceration((v) => !v)}
                          className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-violet-400 transition-colors">
                          <Plus className="h-3 w-3" />{addingIncarceration ? 'Cancel' : 'Add'}
                        </button>
                      )}
                    </div>

                    {addingIncarceration && (
                      <IncarcerationForm
                        draft={incarcerationDraft}
                        setDraft={setIncarcerationDraft}
                        idPrefix="inc-new"
                        isPending={createIncarceration.isPending}
                        submitLabel="Save"
                        onCancel={() => {
                          setIncarcerationDraft(EMPTY_INCARCERATION_DRAFT)
                          setAddingIncarceration(false)
                        }}
                        onSubmit={async () => {
                          await createIncarceration.mutateAsync({
                            facility: incarcerationDraft.facility || null,
                            case_id: incarcerationDraft.case_id || null,
                            notes: incarcerationDraft.notes || null,
                            from_date: incarcerationDraft.from_date,
                            earliest_release_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.earliest_release_date,
                            max_discharge_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.max_discharge_date,
                            life_sentence: incarcerationDraft.life_sentence,
                          })
                          setIncarcerationDraft(EMPTY_INCARCERATION_DRAFT)
                          setAddingIncarceration(false)
                        }}
                      />
                    )}

                    {incarcerations && incarcerations.length > 0 ? (
                      <div className="relative pl-4 space-y-0">
                        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-zinc-700/50" />
                        {incarcerations.map((spell: MemberIncarcerationRead) => (
                          <div key={spell.id} className="group relative pb-4 last:pb-0">
                            <div className="absolute -left-[13px] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-zinc-700 bg-zinc-900 ring-0 group-hover:border-violet-500 transition-colors" />
                            {editingSpellId === spell.id ? (
                              <IncarcerationForm
                                draft={incarcerationDraft}
                                setDraft={setIncarcerationDraft}
                                idPrefix={`inc-edit-${spell.id}`}
                                isPending={updateIncarceration.isPending}
                                submitLabel="Save"
                                onCancel={() => {
                                  setIncarcerationDraft(EMPTY_INCARCERATION_DRAFT)
                                  setEditingSpellId(null)
                                }}
                                onSubmit={async () => {
                                  await updateIncarceration.mutateAsync({
                                    spellId: spell.id,
                                    data: {
                                      facility: incarcerationDraft.facility || null,
                                      case_id: incarcerationDraft.case_id || null,
                                      notes: incarcerationDraft.notes || null,
                                      from_date: incarcerationDraft.from_date,
                                      earliest_release_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.earliest_release_date,
                                      max_discharge_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.max_discharge_date,
                                      life_sentence: incarcerationDraft.life_sentence,
                                    },
                                  })
                                  setIncarcerationDraft(EMPTY_INCARCERATION_DRAFT)
                                  setEditingSpellId(null)
                                }}
                              />
                            ) : (
                              <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-zinc-200 leading-snug">
                                    {spell.facility ?? 'Unknown facility'}
                                  </p>
                                  {spell.life_sentence ? (
                                    <p className="mt-0.5 text-[11px] font-medium text-rose-400">
                                      {spell.from_date ? <><FuzzyDate value={spell.from_date} />{' – '}</> : null}
                                      Life sentence
                                    </p>
                                  ) : (spell.from_date || spell.earliest_release_date || spell.max_discharge_date) && (
                                    <p className="mt-0.5 text-[11px] text-zinc-500">
                                      {spell.from_date ? <FuzzyDate value={spell.from_date} /> : '?'}
                                      {' – '}
                                      {spell.earliest_release_date && spell.max_discharge_date ? (
                                        <>
                                          Earliest: <FuzzyDate value={spell.earliest_release_date} />
                                          {' · Max: '}
                                          <FuzzyDate value={spell.max_discharge_date} />
                                        </>
                                      ) : spell.max_discharge_date ? (
                                        <>Max: <FuzzyDate value={spell.max_discharge_date} /></>
                                      ) : spell.earliest_release_date ? (
                                        <>Earliest: <FuzzyDate value={spell.earliest_release_date} /></>
                                      ) : (
                                        'present'
                                      )}
                                    </p>
                                  )}
                                  {spell.case_id && (
                                    <p className="mt-0.5 font-mono text-[11px] text-zinc-600">#{spell.case_id}</p>
                                  )}
                                  {spell.notes && (
                                    <p className="mt-0.5 text-[11px] text-zinc-500 italic">{spell.notes}</p>
                                  )}
                                </div>
                                {isAdmin && (
                                  <div className="mt-0.5 flex shrink-0 items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setIncarcerationDraft({
                                          facility: spell.facility ?? '',
                                          case_id: spell.case_id ?? '',
                                          notes: spell.notes ?? '',
                                          from_date: spell.from_date,
                                          earliest_release_date: spell.earliest_release_date,
                                          max_discharge_date: spell.max_discharge_date,
                                          life_sentence: spell.life_sentence,
                                        })
                                        setEditingSpellId(spell.id)
                                        setAddingIncarceration(false)
                                      }}
                                      className="text-zinc-700 hover:text-violet-400 transition-colors"
                                      aria-label="Edit incarceration"
                                    >
                                      <Pencil className="h-3 w-3" />
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => deleteIncarceration.mutate(spell.id)}
                                      className="text-zinc-700 hover:text-red-400 transition-colors"
                                      aria-label="Delete incarceration"
                                    >
                                      <Trash2 className="h-3 w-3" />
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      !addingIncarceration && <p className="text-xs text-zinc-600">No incarceration records.</p>
                    )}
                  </div>
                )}

                <FamilyPanel
                  family={member.family as Record<string, unknown> | null}
                  universeId={universe.id}
                  familyCount={familyCount}
                  onAdd={() => setAddingFamily(true)}
                  onOpenGraph={() => setFamilyGraphOpen(true)}
                />

                {hasSocial && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-3">
                    <p className="mb-2.5 text-xs font-medium uppercase tracking-wider text-zinc-500">Social</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(member.social_media as Record<string, string>).map(([platform, handle]) => {
                        if (!handle) return null
                        const raw = String(handle)
                        const url = socialUrl(platform, raw)
                        const display = raw.startsWith('http') ? (extractHost(raw) ?? raw) : `@${raw.replace(/^@/, '')}`
                        const Icon = SOCIAL_ICON[platform.toLowerCase()] ?? null
                        if (url) {
                          return (
                            <a key={platform} href={url} target="_blank" rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700/60 bg-zinc-800/60 px-2.5 py-1.5 text-xs text-zinc-400 hover:border-zinc-600 hover:text-white transition-colors">
                              {Icon && <Icon className="h-3.5 w-3.5" />}
                              <span className="capitalize">{platform}</span>
                              <ExternalLink className="h-2.5 w-2.5 opacity-50" />
                            </a>
                          )
                        }
                        return (
                          <Tooltip key={platform}>
                            <TooltipTrigger asChild>
                              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700/40 bg-zinc-800/40 px-2.5 py-1.5 text-xs text-zinc-600 cursor-default">
                                {Icon && <Icon className="h-3.5 w-3.5" />}
                                <span className="capitalize">{platform}</span>
                                {raw.startsWith('http') && <AlertTriangle className="h-2.5 w-2.5 text-amber-500" />}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              {raw.startsWith('http') ? 'Malformed URL' : display}
                            </TooltipContent>
                          </Tooltip>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Incidents section */}
          <section>
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Incidents</h2>
                {incidentCount > 0 && (
                  <Badge variant="secondary" className="px-1.5 py-0 text-xs">{incidentCount}</Badge>
                )}
                {incidentCount > 0 && (
                  <div className="flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-900/60 p-1">
                    {(['list', 'timeline'] as const).map((v) => (
                      <button key={v} type="button" onClick={() => setIncidentsView(v)}
                        className={`rounded px-2.5 py-0.5 text-[11px] font-medium transition-colors ${incidentsView === v ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>
                        {v === 'list' ? 'List' : 'Timeline'}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <Button size="sm" variant="outline" onClick={() => setCreatingIncident(true)}>
                <Plus className="mr-1.5 h-3.5 w-3.5" />Add Incident
              </Button>
            </div>
            {incidentCount === 0 ? (
              <p className="py-4 text-sm text-zinc-600">No incidents recorded.</p>
            ) : incidentsView === 'timeline' ? (
              <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                <MemberTimeline incidents={incidents!.items} dob={member.dob} dateOfDeath={member.date_of_death} />
              </Suspense>
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
                    {incidents!.items.map((inc) => (
                      <tr key={inc.id} className="hover:bg-zinc-900/50 transition-colors">
                        <td className="p-0">
                          <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-zinc-300 hover:text-violet-400">
                            {inc.date ? <FuzzyDate value={inc.date} /> : '—'}
                          </Link>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className={`text-xs ${inc.type === 'MURDER' ? 'border-rose-800 text-rose-400' : inc.type === 'FIGHT' ? 'border-violet-800 text-violet-400' : 'border-amber-800 text-amber-400'}`}>
                            {inc.type}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-xs text-zinc-500">
                          {inc.victim_names.length > 0 ? inc.victim_names.join(', ') : '—'}
                        </td>
                        <td className="px-4 py-3">
                          {inc.verified ? (
                            <Tooltip>
                              <TooltipTrigger asChild><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /></TooltipTrigger>
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
          </section>

          {/* Photos section */}
          {universe && (
            <section>
              <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Photos</h2>
              <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                <PhotoGallery entityType="member" entityId={member.id} universeId={universe.id} />
              </Suspense>
            </section>
          )}

          {/* Dialogs */}
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

          {universe && (
            <Dialog open={familyGraphOpen} onOpenChange={setFamilyGraphOpen}>
              <DialogContent className="max-w-3xl">
                <DialogHeader>
                  <DialogTitle>Family network — {member.display_name}</DialogTitle>
                  <DialogDescription>Direct kin links recorded for this member.</DialogDescription>
                </DialogHeader>
                <Suspense fallback={<Skeleton className="h-[480px] w-full" />}>
                  <MemberFamilyGraph
                    centerMember={member}
                    universeId={universe.id}
                    allMembers={allMembers?.items ?? []}
                  />
                </Suspense>
              </DialogContent>
            </Dialog>
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
