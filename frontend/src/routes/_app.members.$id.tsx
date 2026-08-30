import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import {
  AlertTriangle, ChevronRight, Copy, Download, ExternalLink, GitFork,
  Mic, Pencil, Plus, Rat, Skull, Trash2, X,
} from 'lucide-react'
import { FacebookIcon, InstagramIcon, TwitterIcon } from '@/components/icons/SocialIcons'
import { lazy, Suspense, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { FuzzyDate } from '@/components/FuzzyDate'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { ageFromFuzzyDates, currentAffiliations, timeAgo } from '@/lib/utils'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  useMember,
  useDeleteMember, useMemberIncidents, useMembersByIds, useUpdateMember,
  useCreateMemberIncarceration, useUpdateMemberIncarceration, useDeleteMemberIncarceration,
} from '@/lib/queries'
import type { IncidentListItem, MemberIncarcerationRead, MemberRead } from '@/lib/types'
import {
  controllingSpell, formatTermRange, groupIncarcerations, incarcerationStatus,
  incarcerationSummary, OPEN_SENTENCE_LABEL, parseSentenceNotes,
} from '@/lib/incarceration'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { downloadText } from '@/lib/download'
import {
  INCIDENT_TYPE_CHIP, INCIDENT_TYPE_LABEL,
  ROLE_CHIP as PARTICIPANT_ROLE_CHIP,
  ROLE_LABEL as PARTICIPANT_ROLE_LABEL,
  OUTCOME_LABEL,
} from '@/lib/incidentColors'
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
import { socialEntries, socialHandle } from '@/lib/social'

const MemberTimeline = lazy(() =>
  import('@/components/graphs/MemberTimeline').then((m) => ({ default: m.MemberTimeline })),
)

export const Route = createFileRoute('/_app/members/$id')({
  component: MemberDetailPage,
})

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatPill({ label, value, accent = 'text-white' }: { label: string; value: number; accent?: string }) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <span className={`text-2xl font-bold tabular-nums ${accent}`}>{value}</span>
      <span className="mt-0.5 text-[11px] text-zinc-400">{label}</span>
    </div>
  )
}

function DetailRow({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-4 border-b border-zinc-800/70 py-2.5 last:border-0">
      <span className="w-32 shrink-0 text-xs text-zinc-400">{label}</span>
      <span className="text-sm text-zinc-200">{children}</span>
    </div>
  )
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

function FamilyMemberLink({ memberId, member }: { memberId: string; member: MemberRead | undefined }) {
  if (!member) {
    return <span className="text-xs text-zinc-400 font-mono">{memberId.slice(0, 8)}…</span>
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
  /** When the spell actually ended. Set means historical: the two dates below
   *  become projections that were overtaken, and stop reaching the calendar. */
  to_date: FuzzyDateValue | null
  earliest_release_date: FuzzyDateValue | null
  max_discharge_date: FuzzyDateValue | null
  life_sentence: boolean
}

const EMPTY_INCARCERATION_DRAFT: IncarcerationDraft = {
  facility: '', case_id: '', notes: '',
  from_date: null, to_date: null, earliest_release_date: null, max_discharge_date: null,
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
      <Textarea
        value={draft.notes}
        onChange={(e) => setDraft((d) => ({ ...d, notes: e.target.value }))}
        placeholder="Notes (optional)"
        rows={3}
        className="text-sm"
      />
      <FuzzyDateInput
        idPrefix={`${idPrefix}-from`}
        label="From"
        value={draft.from_date}
        onChange={(v) => setDraft((d) => ({ ...d, from_date: v }))}
      />
      <FuzzyDateInput
        idPrefix={`${idPrefix}-to`}
        label="To (actually released — leave blank if still inside)"
        value={draft.to_date}
        onChange={(v) => setDraft((d) => ({ ...d, to_date: v }))}
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
            label="Earliest release date (state DOC only, leave blank for federal)"
            value={draft.earliest_release_date}
            onChange={(v) => setDraft((d) => ({ ...d, earliest_release_date: v }))}
          />
          <FuzzyDateInput
            idPrefix={`${idPrefix}-max`}
            label="Maximum discharge date"
            value={draft.max_discharge_date}
            onChange={(v) => setDraft((d) => ({ ...d, max_discharge_date: v }))}
          />
          {draft.to_date && (
            <p className="text-[11px] text-zinc-500">
              This spell has ended, so both dates above are kept as the record of what was projected. They no longer appear on the calendar.
            </p>
          )}
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
  spouse: 'text-rose-400',
  father: 'text-amber-400',
  son: 'text-sky-400',
  brother: 'text-violet-400',
  cousin: 'text-emerald-400',
  uncle: 'text-orange-400',
  nephew: 'text-pink-400',
}

const ROLE_TOOLTIP: Record<FamilyRole, string> = {
  spouse: 'Married or long-term partner',
  father: 'Biological or adoptive father',
  son: 'Male child of this member',
  brother: 'Brother (shared parent)',
  cousin: 'Shares a grandparent',
  uncle: "Sibling of this member's parent",
  nephew: "Child of this member's sibling",
}

function FamilyPanel({
  family,
  relatives,
  familyCount,
  onAdd,
  onOpenGraph,
}: {
  family: Record<string, unknown> | null
  relatives: Record<string, MemberRead>
  familyCount: number
  onAdd: () => void
  onOpenGraph: () => void
}) {
  const memberMap = relatives

  const entries = familyDictToEntries(family)
  const grouped = (['spouse', 'father', 'son', 'brother', 'cousin', 'uncle', 'nephew'] as FamilyRole[])
    .map((role) => ({ role, ids: entries.filter((e) => e.role === role).map((e) => e.memberId) }))
    .filter((g) => g.ids.length > 0)

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3">
      <div className="mb-2.5 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">Family</p>
        <div className="flex items-center gap-3">
          {familyCount > 0 && (
            <button
              type="button"
              onClick={onOpenGraph}
              className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-violet-400 transition-colors"
            >
              <GitFork className="h-3 w-3" />Graph
            </button>
          )}
          <button
            type="button"
            onClick={onAdd}
            className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-violet-400 transition-colors"
          >
            <Plus className="h-3 w-3" />Add
          </button>
        </div>
      </div>

      {grouped.length === 0 ? (
        <p className="text-xs text-zinc-400">No family links recorded.</p>
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
    for (const role of (['spouse', 'father', 'son', 'brother', 'cousin', 'uncle', 'nephew'] as FamilyRole[])) {
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
      const victims = inc.victim_names.length > 0 ? `  (victims: ${inc.victim_names.join(', ')}` : ''
      const verified = inc.verified ? ' [verified]' : ''
      lines.push(`- ${dateStr}: ${inc.type}${victims}${verified}`)
    }
    lines.push('')
  }

  const socialRows = socialEntries(member.social_media)
  if (socialRows.length > 0) {
    lines.push('## Social')
    lines.push('')
    for (const { platform, raw } of socialRows) {
      lines.push(`- **${platform.charAt(0).toUpperCase() + platform.slice(1)}:** ${raw}`)
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
  const stats = member?.stats ?? null
  const memberUuid = member?.id ?? null
  const { data: incidents } = useMemberIncidents(memberUuid, universe?.id ?? null)
  const aliases = member?.aliases_detail ?? []
  // Memoised so the grouping below has a stable input: `?? []` builds a fresh
  // array every render, which would defeat the memo it feeds.
  const incarcerations = useMemo(() => member?.incarcerations ?? [], [member?.incarcerations])
  // One card per court file: the table holds one row per OTIS sentence.
  const incarcerationGroups = useMemo(() => groupIncarcerations(incarcerations), [incarcerations])
  const incarcerationSummaryData = useMemo(() => incarcerationSummary(incarcerationGroups), [incarcerationGroups])
  const createIncarceration = useCreateMemberIncarceration(memberUuid ?? '', universe?.id ?? '')
  const updateIncarceration = useUpdateMemberIncarceration(memberUuid ?? '', universe?.id ?? '')
  const deleteIncarceration = useDeleteMemberIncarceration(memberUuid ?? '', universe?.id ?? '')
  const [editingSpellId, setEditingSpellId] = useState<string | null>(null)
  const [expandedCaseKey, setExpandedCaseKey] = useState<string | null>(null)
  const killedIn = member?.killed_in ?? null

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

  const familyEntryList = useMemo(
    () => familyDictToEntries((member?.family as Record<string, unknown> | null) ?? null),
    [member?.family],
  )
  const familyCount = familyEntryList.length
  const familyIds = useMemo(
    () => Array.from(new Set(familyEntryList.map((e) => e.memberId))),
    [familyEntryList],
  )
  const relatives = useMembersByIds(universe?.id ?? null, familyIds)

  function handleExport() {
    if (!member) return
    const familyEntries = familyEntryList
      .map((e) => ({ role: e.role, name: relatives[e.memberId]?.display_name ?? e.memberId.slice(0, 8) + '…' }))
    const md = buildMemberMarkdown({
      member,
      setName: member.primary_set_name ?? null,
      allianceName: member.alliance_name ?? null,
      family: familyEntries,
      incidents: incidents?.items ?? [],
      killedIn: killedIn
        ? { type: killedIn.type, date: killedIn.date }
        : null,
    })
    const safeName = member.display_name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'member'
    downloadText(md, `${safeName}.md`, 'text/markdown;charset=utf-8')
  }

  const isAdmin = user?.global_role === 'ADMIN'
  const hasSocial = socialEntries(member?.social_media).length > 0
  const hasIncarcerationPanel = (incarcerations && incarcerations.length > 0) || isAdmin
  const incidentCount = incidents?.items.length ?? 0
  const allStatsZero = !stats || (stats.shootings + stats.assists + stats.kills + stats.times_shot_survived === 0)

  if (isError) return <ErrorState title="Member not found" onRetry={() => refetch()} />

  return (
    <TooltipProvider delayDuration={200}>
    <div className="space-y-5">
      <Breadcrumbs
        items={[
          member?.primary_set_id && member.primary_set_name
            ? { label: member.primary_set_name, to: `/sets/${member.primary_set_slug ?? member.primary_set_id}` }
            : { label: 'Members', to: '/members' },
          { label: member?.display_name ?? 'Member' },
        ]}
      />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : member ? (
        <>
          {/* Hero header */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-4">
              <div className="shrink-0">
                {member.primary_photo_url ? (
                  <img
                    src={member.primary_photo_url}
                    alt={`Photo of ${member.display_name}`}
                    loading="lazy"
                    decoding="async"
                    className="h-20 w-20 rounded-lg object-cover ring-1 ring-zinc-600/80 shadow-lg shadow-black/30"
                  />
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-lg bg-zinc-800 text-2xl font-bold text-zinc-400 ring-1 ring-zinc-700">
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
                    <p className="mt-1 text-sm text-zinc-400">a/k/a {aliasNames.join(' · ')}</p>
                  ) : null
                })()}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <MemberStatusBadge status={member.status} />
                  {member.is_rapper && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-fuchsia-950/50 px-2.5 py-0.5 text-xs text-fuchsia-300 ring-1 ring-fuchsia-800/60">
                      <Mic className="h-3 w-3" />Rapper
                    </span>
                  )}
                  {member.is_snitch && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-950/50 px-2.5 py-0.5 text-xs text-amber-300 ring-1 ring-amber-800/60">
                      <Rat className="h-3 w-3" />Snitch
                    </span>
                  )}
                  {currentAffiliations(member.affiliations).map((aff) => (
                    <Link
                      key={aff.id ?? aff.set_id}
                      to="/sets/$id"
                      params={{ id: aff.set_slug ?? aff.set_id }}
                      className={`rounded-full px-2.5 py-0.5 text-xs text-zinc-400 hover:text-violet-400 transition-colors ${aff.is_primary ? 'bg-zinc-800/70 ring-1 ring-violet-700/30 hover:bg-zinc-800' : 'bg-zinc-900/50 hover:bg-zinc-800/60'}`}
                    >
                      {aff.set_name}
                    </Link>
                  ))}
                  {member.alliance_id && member.alliance_name && (
                    <Link
                      to="/alliances/$id"
                      params={{ id: member.alliance_slug ?? member.alliance_id }}
                      className="rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-blue-400 transition-colors"
                    >
                      {member.alliance_name}
                    </Link>
                  )}
                  <span className="text-[11px] text-zinc-400">Updated {timeAgo(member.updated_at)}</span>
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
              className="group flex items-center gap-3 rounded-lg border border-rose-900/60 bg-rose-950/30 px-4 py-3 transition-colors hover:border-rose-700 hover:bg-rose-950/50"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-rose-950/80">
                <Skull className="h-4 w-4 text-rose-400" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs uppercase tracking-wider text-rose-400">Killed in incident</p>
                <p className="mt-0.5 text-sm text-zinc-200">
                  {killedIn ? (
                    <>
                      <span className="font-medium">{killedIn.type}</span>
                      {killedIn.date && (
                        <span className="text-zinc-400"> · <FuzzyDate value={killedIn.date} /></span>
                      )}
                      {killedIn.municipality_name && (
                        <span className="text-zinc-400"> · {killedIn.municipality_name}</span>
                      )}
                    </>
                  ) : (
                    <span className="text-zinc-400">Loading incident…</span>
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
            <div className="group relative rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <p className="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap">{member.biography}</p>
              <button type="button" onClick={startBioEdit} aria-label="Edit biography"
                className="absolute right-2 top-2 rounded p-1.5 text-zinc-400 opacity-0 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 focus-visible:opacity-100 group-hover:opacity-100">
                <Pencil className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button type="button" onClick={startBioEdit}
              className="flex w-full items-center gap-2 rounded-lg border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-400 hover:border-zinc-700 hover:text-zinc-200 transition-colors">
              <Pencil className="h-3 w-3" />Add biography
            </button>
          )}

          {/* Stats row */}
          {stats && !allStatsZero && (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <StatPill label="Shootings" value={stats.shootings} accent="text-amber-400" />
              <StatPill label="Assists" value={stats.assists} accent="text-violet-400" />
              <StatPill label="Kills" value={stats.kills} accent="text-rose-400" />
              <StatPill label="Survived" value={stats.times_shot_survived} accent="text-emerald-400" />
            </div>
          )}

          {/* Two-column wiki layout: identity facts + right panels */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_280px] lg:items-start">
            {/* Left: identity facts + incidents */}
            <div className="flex flex-col gap-4">
              {(member.dob || member.status === 'DEAD' || member.alliance_id) && (
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-1">
              {member.dob && (
                <DetailRow label="Date of Birth">
                  <span className="flex items-center gap-2 flex-wrap">
                    <FuzzyDate value={member.dob} />
                    {member.dob.year && (() => {
                      const age = ageFromFuzzyDates(member.dob!, member.status === 'DEAD' ? member.date_of_death : null)
                      if (age === null) return null
                      return (
                        <span className="text-xs text-zinc-400">
                          {member.status === 'DEAD' ? `died aged ${age}` : `${age} years old`}
                        </span>
                      )
                    })()}
                  </span>
                </DetailRow>
              )}
              {member.status === 'DEAD' && (
                <DetailRow label="Date of Death">
                  <span className="flex items-center gap-2">
                    <Skull className="h-3 w-3 text-zinc-400" />
                    {member.date_of_death ? <FuzzyDate value={member.date_of_death} /> : <span className="text-zinc-400">Unknown</span>}
                  </span>
                </DetailRow>
              )}
              {member.alliance_id && member.alliance_name && (
                <DetailRow label="Alliance">
                  <Link to="/alliances/$id" params={{ id: member.alliance_slug ?? member.alliance_id }} className="text-blue-400 hover:underline">
                    {member.alliance_name}
                  </Link>
                </DetailRow>
              )}
              </div>
              )}

              {/* Incidents section */}
              <section>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-400">Incidents</h2>
                    {incidentCount > 0 && (
                      <Badge variant="secondary" className="px-1.5 py-0 text-xs">{incidentCount}</Badge>
                    )}
                    {incidentCount > 0 && (
                      <div className="flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-900/60 p-1">
                        {(['list', 'timeline'] as const).map((v) => (
                          <button key={v} type="button" onClick={() => setIncidentsView(v)}
                            className={`rounded px-2.5 py-0.5 text-[11px] font-medium transition-colors ${incidentsView === v ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'}`}>
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
                  <p className="py-4 text-sm text-zinc-400">No incidents recorded.</p>
                ) : incidentsView === 'timeline' ? (
                  <Suspense fallback={<Skeleton className="h-40 w-full" />}>
                    <MemberTimeline incidents={incidents!.items} dob={member.dob} dateOfDeath={member.date_of_death} />
                  </Suspense>
                ) : (
                  <div className="overflow-hidden rounded-lg border border-zinc-800">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-zinc-800 bg-zinc-900/50">
                          <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Date</th>
                          <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Type</th>
                          <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Their role</th>
                          <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Victims</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800">
                        {incidents!.items.map((inc) => (
                          <tr key={inc.id} className="hover:bg-zinc-900/50 transition-colors">
                            <td className="p-0">
                              {/* Verified is a dot in the date cell rather than a column of its
                                  own: it is true for a small minority, so a whole column spent
                                  rendering an em dash costs more width than the flag is worth.
                                  The slot is always reserved so dates stay aligned. */}
                              <Link to="/incidents/$id" params={{ id: inc.id }} className="flex items-center gap-2 px-4 py-3 text-zinc-300 hover:text-violet-400">
                                {inc.verified ? (
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" aria-label="Verified incident" />
                                    </TooltipTrigger>
                                    <TooltipContent side="right">Verified incident</TooltipContent>
                                  </Tooltip>
                                ) : (
                                  <span className="h-1.5 w-1.5 shrink-0" aria-hidden />
                                )}
                                {inc.date ? <FuzzyDate value={inc.date} /> : '—'}
                              </Link>
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant="outline" className={`text-xs ${INCIDENT_TYPE_CHIP[inc.type]}`}>
                                {INCIDENT_TYPE_LABEL[inc.type]}
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              {inc.viewer_role ? (
                                <span className="inline-flex items-center gap-1.5">
                                  <Badge variant="outline" className={`text-xs border ${PARTICIPANT_ROLE_CHIP[inc.viewer_role]}`}>
                                    {PARTICIPANT_ROLE_LABEL[inc.viewer_role]}
                                  </Badge>
                                  {inc.viewer_outcome && inc.viewer_outcome !== 'UNKNOWN' && (
                                    <span className="text-[11px] text-zinc-400">{OUTCOME_LABEL[inc.viewer_outcome]}</span>
                                  )}
                                </span>
                              ) : <span className="text-zinc-400 text-xs">—</span>}
                            </td>
                            <td className="px-4 py-3 text-xs text-zinc-400">
                              {inc.victim_names.length > 0 ? inc.victim_names.join(', ') : '—'}
                            </td>

                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>

            {/* Right: incarceration (top for LOCKED) + family + social */}
            {universe && (
              <div className="space-y-4">
                {hasIncarcerationPanel && (
                  <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">Incarceration</p>
                      {isAdmin && (
                        <button type="button" onClick={() => setAddingIncarceration((v) => !v)}
                          className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-violet-400 transition-colors">
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
                            to_date: incarcerationDraft.to_date,
                            earliest_release_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.earliest_release_date,
                            max_discharge_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.max_discharge_date,
                            life_sentence: incarcerationDraft.life_sentence,
                          })
                          setIncarcerationDraft(EMPTY_INCARCERATION_DRAFT)
                          setAddingIncarceration(false)
                        }}
                      />
                    )}

{incarcerationGroups.length > 0 ? (
                      <div className="space-y-2">
                        {/* Facility and release dates describe the man, not any one
                            court file, so they head the panel once rather than
                            repeating down every card. */}
                        {incarcerationSummaryData && (
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-[11px] text-zinc-400">
                            {incarcerationSummaryData.facility && (
                              <span className="text-zinc-200">{incarcerationSummaryData.facility}</span>
                            )}
                            {incarcerationSummaryData.lifeSentence && (
                              <span className="font-medium text-rose-400">Life sentence</span>
                            )}
                            {incarcerationSummaryData.earliestRelease && (
                              <span>
                                Earliest{' '}
                                <span className="text-zinc-200 tabular-nums">
                                  <FuzzyDate value={incarcerationSummaryData.earliestRelease} />
                                </span>
                              </span>
                            )}
                            {incarcerationSummaryData.maxDischarge && (
                              <span>
                                Max{' '}
                                <span className="text-zinc-200 tabular-nums">
                                  <FuzzyDate value={incarcerationSummaryData.maxDischarge} />
                                </span>
                              </span>
                            )}
                          </div>
                        )}

                        <ul className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                          {incarcerationGroups.map((group) => {
                            const status = incarcerationStatus(group)
                            const head = parseSentenceNotes(controllingSpell(group).notes)
                            const term = formatTermRange(head.minimum, head.maximum)
                            const expanded = expandedCaseKey === group.key
                            return (
                              <li key={group.key}>
                                <button
                                  type="button"
                                  onClick={() => setExpandedCaseKey(expanded ? null : group.key)}
                                  aria-expanded={expanded}
                                  className="flex w-full items-start gap-1.5 px-2.5 py-2 text-left transition-colors hover:bg-zinc-900/60"
                                >
                                  <ChevronRight
                                    className={`mt-0.5 h-3 w-3 shrink-0 text-zinc-500 transition-transform ${expanded ? 'rotate-90' : ''}`}
                                  />
                                  {/* The offence gets the full width of its own
                                      line: this panel sits in a ~230px column, and
                                      sharing that line with the term and the status
                                      truncated every charge to "Ass…". */}
                                  <span className="min-w-0 flex-1">
                                    <span
                                      className={`block truncate text-xs leading-snug ${status === 'discharged' ? 'text-zinc-400' : 'text-zinc-200'}`}
                                      title={head.offense ?? undefined}
                                    >
                                      {head.offense ?? group.caseId ?? 'Sentence'}
                                    </span>
                                    {/* Year, term, count and status all live on the
                                        second line. Sharing the first line with the
                                        status chip truncated every charge to "Ass…"
                                        in this ~230px column. */}
                                    <span className="mt-0.5 flex flex-wrap items-center gap-x-1.5 text-[10px] text-zinc-500">
                                      <span className="font-mono tabular-nums">{group.from?.year ?? '—'}</span>
                                      {term && (
                                        <>
                                          <span aria-hidden>·</span>
                                          <span className="whitespace-nowrap font-mono tabular-nums">{term}</span>
                                        </>
                                      )}
                                      {group.spells.length > 1 && (
                                        <>
                                          <span aria-hidden>·</span>
                                          <span className="whitespace-nowrap tabular-nums">{group.spells.length} counts</span>
                                        </>
                                      )}
                                      <span aria-hidden>·</span>
                                      {/* The long form of "open" is in the title:
                                          OTIS records no discharge, which is not the
                                          same claim as "in this prison today". */}
                                      {status === 'discharged' && group.to?.year ? (
                                        <span className="whitespace-nowrap tabular-nums">out {group.to.year}</span>
                                      ) : status === 'life' ? (
                                        <span className="font-medium text-rose-400">life</span>
                                      ) : status === 'projected' ? (
                                        <span className="text-amber-400/80">serving</span>
                                      ) : (
                                        <span className="italic" title={OPEN_SENTENCE_LABEL}>open</span>
                                      )}
                                    </span>
                                  </span>
                                </button>

                                {expanded && (
                                  <div className="space-y-2 border-t border-zinc-800/60 bg-zinc-950/40 px-3 py-2.5">
                                    <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px] text-zinc-500">
                                      {group.caseId && head.offense && (
                                        <span className="font-mono text-zinc-400">#{group.caseId}</span>
                                      )}
                                      {head.county && <span>{head.county} County</span>}
                                      {head.convictionType && <span>{head.convictionType}</span>}
                                      {head.dateOfOffense && <span>Offence {head.dateOfOffense}</span>}
                                    </div>

                                    {group.spells.map((spell: MemberIncarcerationRead) => {
                                      const detail = parseSentenceNotes(spell.notes)
                                      const spellTerm = formatTermRange(detail.minimum, detail.maximum)
                                      if (editingSpellId === spell.id) {
                                        return (
                                          <IncarcerationForm
                                            key={spell.id}
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
                                                  to_date: incarcerationDraft.to_date,
                                                  earliest_release_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.earliest_release_date,
                                                  max_discharge_date: incarcerationDraft.life_sentence ? null : incarcerationDraft.max_discharge_date,
                                                  life_sentence: incarcerationDraft.life_sentence,
                                                },
                                              })
                                              setIncarcerationDraft(EMPTY_INCARCERATION_DRAFT)
                                              setEditingSpellId(null)
                                            }}
                                          />
                                        )
                                      }
                                      return (
                                        <div key={spell.id} className="group flex items-start justify-between gap-2">
                                          <div className="min-w-0">
                                            {(detail.offense || detail.extra.length === 0) && (
                                            <p className="text-[11px] text-zinc-300">
                                              {detail.offense ?? (detail.extra.length === 0 && (
                                                <span className="italic text-zinc-500">No offence recorded</span>
                                              ))}
                                              {spellTerm && (
                                                <span className="ml-1.5 whitespace-nowrap font-mono text-zinc-500 tabular-nums">{spellTerm}</span>
                                              )}
                                            </p>
                                            )}
                                            <p className="text-[10px] text-zinc-500">
                                              {detail.mcl.length > 0 && <span className="font-mono">MCL {detail.mcl.join(' / ')}</span>}
                                              {detail.dischargeReason && <span> · {detail.dischargeReason}</span>}
                                              {spell.to_date && (
                                                <span> · discharged <FuzzyDate value={spell.to_date} /></span>
                                              )}
                                            </p>
                                            {detail.extra.length > 0 && (
                                              <p className="mt-0.5 whitespace-pre-line text-[10px] italic text-zinc-400">
                                                {detail.extra.join('\n')}
                                              </p>
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
                                                    to_date: spell.to_date,
                                                    earliest_release_date: spell.earliest_release_date,
                                                    max_discharge_date: spell.max_discharge_date,
                                                    life_sentence: spell.life_sentence,
                                                  })
                                                  setEditingSpellId(spell.id)
                                                  setAddingIncarceration(false)
                                                }}
                                                className="text-zinc-500 transition-colors hover:text-violet-400"
                                                aria-label="Edit sentence"
                                              >
                                                <Pencil className="h-3 w-3" />
                                              </button>
                                              <button
                                                type="button"
                                                onClick={() => deleteIncarceration.mutate(spell.id)}
                                                className="text-zinc-500 transition-colors hover:text-red-400"
                                                aria-label="Delete sentence"
                                              >
                                                <Trash2 className="h-3 w-3" />
                                              </button>
                                            </div>
                                          )}
                                        </div>
                                      )
                                    })}
                                  </div>
                                )}
                              </li>
                            )
                          })}
                        </ul>
                      </div>
                    ) : (
                      !addingIncarceration && <p className="text-xs text-zinc-400">No incarceration records.</p>
                    )}
                  </div>
                )}

                <FamilyPanel
                  family={member.family as Record<string, unknown> | null}
                  relatives={relatives}
                  familyCount={familyCount}
                  onAdd={() => setAddingFamily(true)}
                  onOpenGraph={() => setFamilyGraphOpen(true)}
                />

                {hasSocial && (
                  <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3">
                    <p className="mb-2.5 text-xs font-medium uppercase tracking-wider text-zinc-400">Social</p>
                    <div className="flex flex-wrap gap-2">
                      {socialEntries(member.social_media).map(({ platform, raw, key }) => {
                        const url = socialUrl(platform, raw)
                        const display = socialHandle(raw)
                        const Icon = SOCIAL_ICON[platform.toLowerCase()] ?? null
                        if (url) {
                          return (
                            <Tooltip key={key}>
                              <TooltipTrigger asChild>
                                <a href={url} target="_blank" rel="noopener noreferrer"
                                  className="inline-flex max-w-full items-center gap-1.5 rounded-lg border border-zinc-700/60 bg-zinc-800/60 px-2.5 py-1.5 text-xs text-zinc-400 hover:border-zinc-600 hover:text-white transition-colors">
                                  {Icon && <Icon className="h-3.5 w-3.5 shrink-0" />}
                                  <span className="truncate">{display}</span>
                                  <ExternalLink className="h-2.5 w-2.5 shrink-0 opacity-50" />
                                </a>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="capitalize">{platform}</TooltipContent>
                            </Tooltip>
                          )
                        }
                        return (
                          <Tooltip key={key}>
                            <TooltipTrigger asChild>
                              <span className="inline-flex max-w-full items-center gap-1.5 rounded-lg border border-zinc-700/40 bg-zinc-800/40 px-2.5 py-1.5 text-xs text-zinc-400 cursor-default">
                                {Icon && <Icon className="h-3.5 w-3.5 shrink-0" />}
                                <span className="truncate">{display}</span>
                                {raw.startsWith('http') && <AlertTriangle className="h-2.5 w-2.5 shrink-0 text-amber-500" />}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              {raw.startsWith('http') ? 'Malformed URL' : platform}
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

          {/* Photos section */}
          {universe && (
            <section>
              <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-400">Photos</h2>
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
                  <DialogTitle>Family network: {member.display_name}</DialogTitle>
                  <DialogDescription>Direct kin links recorded for this member.</DialogDescription>
                </DialogHeader>
                <Suspense fallback={<Skeleton className="h-[480px] w-full" />}>
                  <MemberFamilyGraph centerMember={member} universeId={universe.id} />
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
                  acquitted: false,
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
