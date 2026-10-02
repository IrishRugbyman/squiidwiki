import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { allianceRefsOf } from '@/lib/setGangs'
import { GitFork, MoreHorizontal, Network, Pencil, Plus, Search, Shield, Swords, Trash2, UserPlus, Users, X } from 'lucide-react'
import { lazy, Suspense, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { CopyButton } from '@/components/CopyButton'
import { DetailRow, IncidentRow, None, PanelHeading, StatStrip } from '@/components/detail/DetailParts'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { MemberAvatar } from '@/components/members/MemberFormSheet'
import { AddMemberToAllianceDialog } from '@/components/AddMemberToAllianceDialog'
import { AddSetToAllianceDialog } from '@/components/AddSetToAllianceDialog'
import { AddAllianceRelationshipDialog, AllianceRelationshipsPanel } from '@/components/alliances/AllianceRelationships'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { AllianceStatusBadge, MemberStatusBadge, SetStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useEditShortcut } from '@/hooks/useKeymap'
import { useAlliance, useAllianceIncidents, useAllianceMembers, useAllianceRelationships, useAllSets, useDeleteAlliance, useUpdateSet } from '@/lib/queries'
import { nonPrimaryVariantsText } from '@/lib/setDisplay'
import { MEMBER_STATUS_CHIP_ACTIVE, MEMBER_STATUS_DOT, MEMBER_STATUS_ORDER } from '@/lib/statusColors'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { IncidentListItem, MemberListItem, MemberStatus, SetListItem } from '@/lib/types'
import { currentAffiliations, timeAgo } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth'
import { useRecordRecent } from '@/stores/recents'
import { useUniverseStore } from '@/stores/universe'
import { AllianceFormSheet } from './_app.$universe.alliances.index'
import { SetAvatar, SetFormSheet } from './_app.$universe.sets.index'
import { MemberFormSheet } from './_app.$universe.members.index'
import { LinkifiedText } from '@/components/LinkifiedText'

// The alliance page, in its own chunk (the route file only declares it).
export const Route = createLazyFileRoute('/_app/$universe/alliances/$id')({
  component: AllianceDetailPage,
})

const AllianceRelationshipGraph = lazy(() =>
  import('@/components/graphs/AllianceRelationshipGraph').then((m) => ({ default: m.AllianceRelationshipGraph })),
)
const PhotoGallery = lazy(() => import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })))

const MEMBER_STEP = 50
const INCIDENT_STEP = 10
const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()
const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

const UNDATED = '￿'
function dateKey(d: FuzzyDateValue | null | undefined): string {
  if (!d?.year) return UNDATED
  return `${String(d.year).padStart(4, '0')}-${String(d.month ?? 0).padStart(2, '0')}-${String(d.day ?? 0).padStart(2, '0')}`
}

function SetCard({ set, members, onRemove }: { set: SetListItem; members: number; onRemove: () => void }) {
  const aka = nonPrimaryVariantsText(set.name_variants)
  return (
    <div className="group relative flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/30 px-3 py-2.5 transition-colors hover:border-zinc-700 hover:bg-zinc-900/60">
      <SetAvatar name={set.name} thumbUrl={set.primary_photo_thumb_url} gangColor={set.gang_color} />
      <Link from="/$universe" to="/$universe/sets/$id" params={{ id: set.slug ?? set.id }} className="min-w-0 flex-1 after:absolute after:inset-0 focus-visible:outline-none">
        <span className="block truncate text-sm font-medium text-white group-hover:text-violet-300">{set.name}</span>
        <span className="flex items-center gap-2 text-[11px] text-zinc-400">
          <span className="inline-flex items-center gap-1 tabular-nums" title={plural(members, 'current member')}><Users className="h-3 w-3" aria-hidden />{members}</span>
          {aka && <span className="truncate">{aka}</span>}
        </span>
      </Link>
      <SetStatusBadge status={set.status} />
      <button type="button" onClick={onRemove} aria-label={`Remove ${set.name} from the alliance`}
        className="relative z-10 rounded p-1 text-zinc-500 transition-opacity hover:bg-red-950/40 hover:text-red-400 focus-visible:opacity-100 group-hover:opacity-100 pointer-fine:opacity-0">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function AllianceDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: alliance, isLoading, isError, refetch } = useAlliance(id, universeId)
  // The whole universe's sets: the cards resolve the alliance's set_ids, and the
  // graph resolves the allies and enemies of any set at all.
  const { data: allSets } = useAllSets(universeId)
  // Sub-resources are typed by UUID and 422 on a slug, so they wait for the id.
  const { data: members, isLoading: membersLoading } = useAllianceMembers(alliance?.id ?? '', universeId)
  const { data: incidents, isLoading: incidentsLoading } = useAllianceIncidents(alliance?.id ?? '', universeId)
  const { data: relationships } = useAllianceRelationships(alliance?.id ?? null, universeId)
  const deleteAlliance = useDeleteAlliance(universe?.id ?? '')

  useRecordRecent(alliance ? { type: 'alliance', id: alliance.id, slug: alliance.slug, label: alliance.name } : null)

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [addingSet, setAddingSet] = useState(false)
  const [addingRel, setAddingRel] = useState(false)
  const [creatingSet, setCreatingSet] = useState(false)
  const [addingMember, setAddingMember] = useState(false)
  const [creatingMember, setCreatingMember] = useState(false)
  const [removingSetId, setRemovingSetId] = useState<string | null>(null)
  const [showGraph, setShowGraph] = useState(false)
  const [memberQuery, setMemberQuery] = useState('')
  const [memberStatus, setMemberStatus] = useState<MemberStatus | 'ALL'>('ALL')
  const [memberLimit, setMemberLimit] = useState(MEMBER_STEP)
  const [incidentLimit, setIncidentLimit] = useState(INCIDENT_STEP)

  useEditShortcut(() => alliance && setEditing(true))

  const memberItems = useMemo<MemberListItem[]>(() => members?.items ?? [], [members])
  const incidentItems = useMemo<IncidentListItem[]>(
    () => [...(incidents?.items ?? [])].sort((a, b) => {
      // Newest first, undated last.
      const ka = dateKey(a.date), kb = dateKey(b.date)
      if ((ka === UNDATED) !== (kb === UNDATED)) return ka === UNDATED ? 1 : -1
      return kb.localeCompare(ka)
    }),
    [incidents],
  )
  const allianceSets = useMemo(() => {
    const ids = new Set(alliance?.set_ids ?? [])
    return (allSets?.items ?? []).filter((s) => ids.has(s.id)).sort((a, b) => b.member_count - a.member_count || a.name.localeCompare(b.name))
  }, [allSets, alliance])
  const allianceSetIds = useMemo(() => new Set(allianceSets.map((s) => s.id)), [allianceSets])

  const memberCountBySetId = useMemo(() => {
    const m: Record<string, number> = {}
    for (const x of memberItems) for (const aff of currentAffiliations(x.affiliations)) m[aff.set_id] = (m[aff.set_id] ?? 0) + 1
    return m
  }, [memberItems])

  const statusCounts = useMemo(() => {
    const c: Partial<Record<MemberStatus, number>> = {}
    for (const m of memberItems) c[m.status] = (c[m.status] ?? 0) + 1
    return c
  }, [memberItems])

  const filteredMembers = useMemo(() => {
    const q = memberQuery.trim().toLowerCase()
    return memberItems
      .filter((m) => memberStatus === 'ALL' || m.status === memberStatus)
      .filter((m) => !q || m.display_name.toLowerCase().includes(q) || !!m.aliases?.some((a) => a.toLowerCase().includes(q)))
      .sort((a, b) => a.display_name.localeCompare(b.display_name, undefined, { sensitivity: 'base', numeric: true }))
  }, [memberItems, memberQuery, memberStatus])

  // Paged lists start over when what they show changes.
  const [limitsFor, setLimitsFor] = useState(filteredMembers)
  if (limitsFor !== filteredMembers) {
    setLimitsFor(filteredMembers)
    setMemberLimit(MEMBER_STEP)
  }

  if (isError) return <ErrorState title="Alliance not found" onRetry={() => refetch()} />

  function showMembers(status: MemberStatus | 'ALL') {
    setMemberStatus(status)
    setMemberQuery('')
    document.getElementById('alliance-members')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function handleDelete() {
    if (!alliance) return
    try {
      await deleteAlliance.mutateAsync(alliance.id)
      navigate({ from: '/$universe', to: '/$universe/alliances' })
    } catch {
      setDeleting(false)
    }
  }

  const removingSet = removingSetId ? allianceSets.find((s) => s.id === removingSetId) ?? null : null
  const killings = incidentItems.filter((i) => i.type === 'MURDER').length
  const directMembers = memberItems.filter((m) => m.alliance_id === alliance?.id).length

  return (
    <div className="space-y-5 pb-8">
      <Breadcrumbs items={[{ label: 'Alliances', to: '/$universe/alliances' }, { label: alliance?.name ?? 'Alliance' }]} />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : alliance ? (
        <>
          {/* Header */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex min-w-0 items-start gap-4">
              <SetAvatar name={alliance.name} thumbUrl={alliance.primary_photo_url} size="xl" />
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-2xl font-bold leading-tight text-white">{alliance.name}</h1>
                  <CopyButton value={window.location.href} label="Copy link to this alliance" className="opacity-40 hover:opacity-100" />
                </div>
                {alliance.aliases && alliance.aliases.length > 0 && (
                  <p className="mt-0.5 text-sm text-zinc-400">a/k/a {alliance.aliases.join(', ')}</p>
                )}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <AllianceStatusBadge status={alliance.status} />
                  {alliance.founded_at && (
                    <span className="rounded-full border border-zinc-800 bg-zinc-900/50 px-2 py-0.5 text-[11px] text-zinc-400">
                      Founded <FuzzyDate value={alliance.founded_at} />
                    </span>
                  )}
                  <span className="text-[11px] text-zinc-400">Updated {timeAgo(alliance.updated_at)}</span>
                </div>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)} title="Edit (e)"><Pencil className="mr-1.5 h-3.5 w-3.5" />Edit</Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="outline" aria-label="More actions"><MoreHorizontal className="h-3.5 w-3.5" /></Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setAddingSet(true)}><Shield className="mr-2 h-3.5 w-3.5" />Add a set</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setAddingMember(true)}><UserPlus className="mr-2 h-3.5 w-3.5" />Add a member</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setAddingRel(true)}><Swords className="mr-2 h-3.5 w-3.5" />Add an ally or enemy</DropdownMenuItem>
                  {user?.global_role === 'ADMIN' && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setDeleting(true)} className="text-red-400 focus:text-red-300">
                        <Trash2 className="mr-2 h-3.5 w-3.5" />Delete alliance
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <StatStrip cells={[
            { label: 'Sets', value: alliance.set_ids.length, accent: 'text-violet-400', onClick: () => document.getElementById('alliance-sets')?.scrollIntoView({ behavior: 'smooth', block: 'start' }) },
            { label: 'Members', value: memberItems.length, accent: 'text-sky-400', onClick: () => showMembers('ALL'), title: 'Current members of its sets, plus members tagged to it directly' },
            { label: 'Locked', value: statusCounts.LOCKED ?? 0, accent: 'text-orange-400', onClick: () => showMembers('LOCKED') },
            { label: 'Dead', value: statusCounts.DEAD ?? 0, accent: 'text-zinc-200', onClick: () => showMembers('DEAD') },
            { label: 'Incidents', value: incidentItems.length, accent: 'text-amber-400', onClick: () => document.getElementById('alliance-incidents')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), title: 'Incidents involving its members' },
            { label: 'Murders', value: killings, accent: 'text-rose-400', title: 'Murders involving its members, on either side' },
          ]} />

          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="min-w-0 space-y-6">
              {alliance.description ? (
                <div className="group relative rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                  <p className="whitespace-pre-wrap pr-6 text-sm leading-relaxed text-zinc-300"><LinkifiedText text={alliance.description} /></p>
                  <button type="button" onClick={() => setEditing(true)} aria-label="Edit description"
                    className="absolute right-2 top-2 rounded p-1.5 text-zinc-400 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 focus-visible:opacity-100 group-hover:opacity-100 pointer-fine:opacity-0">
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <button type="button" onClick={() => setEditing(true)}
                  className="flex w-full items-center gap-2 rounded-lg border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200">
                  <Pencil className="h-3 w-3" />Add a description
                </button>
              )}

              {/* Sets */}
              <section id="alliance-sets" className="scroll-mt-4">
                <PanelHeading action={
                  <span className="flex items-center gap-3">
                    {allianceSets.length > 0 && (
                      <button type="button" onClick={() => setShowGraph((v) => !v)} aria-pressed={showGraph}
                        className={`inline-flex items-center gap-1 text-xs transition-colors hover:text-violet-400 ${showGraph ? 'text-violet-300' : 'text-zinc-400'}`}>
                        <GitFork className="h-3 w-3" />{showGraph ? 'Hide graph' : 'Graph'}
                      </button>
                    )}
                    <button type="button" onClick={() => setAddingSet(true)} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
                      <Plus className="h-3 w-3" />Add
                    </button>
                  </span>
                }>Sets ({alliance.set_ids.length})</PanelHeading>
                {showGraph && universe && allianceSets.length > 0 && (
                  <div className="mb-3">
                    <Suspense fallback={<Skeleton className="h-[480px] w-full" />}>
                      <AllianceRelationshipGraph allianceSets={allianceSets} allSets={allSets?.items ?? []} memberCountBySetId={memberCountBySetId} universeId={universe.id} />
                    </Suspense>
                  </div>
                )}
                {alliance.set_ids.length === 0 ? (
                  <EmptyState icon={Network} title="No sets yet" description="Attach existing sets, or create one within this alliance."
                    action={<Button size="sm" onClick={() => setAddingSet(true)}><Plus className="mr-1.5 h-4 w-4" />Add the first set</Button>} />
                ) : !allSets ? (
                  <Skeleton className="h-28 w-full" />
                ) : (
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {allianceSets.map((s) => (
                      <SetCard key={s.id} set={s} members={memberCountBySetId[s.id] ?? 0} onRemove={() => setRemovingSetId(s.id)} />
                    ))}
                  </div>
                )}
              </section>

              {/* Members */}
              <section id="alliance-members" className="scroll-mt-4">
                <PanelHeading action={
                  <button type="button" onClick={() => setAddingMember(true)} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
                    <Plus className="h-3 w-3" />Add
                  </button>
                }>Members ({memberItems.length})</PanelHeading>
                {membersLoading ? (
                  <Skeleton className="h-40 w-full" />
                ) : memberItems.length === 0 ? (
                  <EmptyState icon={Users} title="No members" description="Members of its sets appear here, and so do members added to it directly."
                    action={<Button size="sm" onClick={() => setAddingMember(true)}><Plus className="mr-1.5 h-4 w-4" />Add a member</Button>} />
                ) : (
                  <>
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      {memberItems.length > 8 && (
                        <div className="relative min-w-[180px] max-w-xs flex-1">
                          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
                          <Input className="h-8 pl-8 text-sm" placeholder="Filter by name or alias…" aria-label="Filter members" value={memberQuery} onChange={(e) => setMemberQuery(e.target.value)} />
                        </div>
                      )}
                      <div className="flex flex-wrap items-center gap-1">
                        {(['ALL', ...MEMBER_STATUS_ORDER] as const)
                          .filter((s) => s === 'ALL' || (statusCounts[s] ?? 0) > 0 || memberStatus === s)
                          .map((s) => {
                            const active = memberStatus === s
                            return (
                              <button key={s} type="button" onClick={() => setMemberStatus(s)} aria-pressed={active}
                                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                                  active ? (s === 'ALL' ? 'border-violet-500/60 bg-violet-500/10 text-violet-200' : MEMBER_STATUS_CHIP_ACTIVE[s]) : 'border-zinc-800 bg-zinc-900/40 text-zinc-400 hover:text-zinc-300'
                                }`}>
                                {s !== 'ALL' && <span className={`h-1.5 w-1.5 rounded-full ${MEMBER_STATUS_DOT[s]}`} aria-hidden />}
                                {s === 'ALL' ? 'All' : titleCase(s)}
                                <span className="tabular-nums opacity-70">{s === 'ALL' ? memberItems.length : statusCounts[s] ?? 0}</span>
                              </button>
                            )
                          })}
                      </div>
                    </div>
                    {filteredMembers.length === 0 ? (
                      <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No members match.</p>
                    ) : (
                      <ul className="divide-y divide-zinc-800/70 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                        {filteredMembers.slice(0, memberLimit).map((m) => {
                          const sets = currentAffiliations(m.affiliations).filter((a) => allianceSetIds.has(a.set_id))
                          return (
                            <li key={m.id} className="flex items-center gap-3 px-3 py-2">
                              <MemberAvatar member={m} />
                              <Link from="/$universe" to="/$universe/members/$id" params={{ id: m.slug ?? m.id }} className="group min-w-0 flex-1">
                                <span className="block truncate text-sm font-medium text-white group-hover:text-violet-300">{m.display_name}</span>
                                {m.aliases && m.aliases.length > 0 && <span className="block truncate text-[11px] text-zinc-500">{m.aliases.slice(0, 3).join(' · ')}</span>}
                              </Link>
                              <span className="hidden max-w-[40%] flex-wrap justify-end gap-1 sm:flex">
                                {sets.length > 0 ? sets.map((a) => (
                                  <Link key={a.set_id} from="/$universe" to="/$universe/sets/$id" params={{ id: a.set_slug ?? a.set_id }}
                                    className="rounded-full bg-zinc-800/80 px-2 py-0.5 text-[11px] text-zinc-300 transition-colors hover:text-violet-300">
                                    {a.set_name}
                                  </Link>
                                )) : m.alliance_id === alliance.id ? (
                                  <span className="text-[11px] text-zinc-500" title="Tagged to the alliance itself, not through one of its sets">Direct</span>
                                ) : null}
                              </span>
                              <span className="hidden w-24 text-right text-xs text-zinc-400 md:block">
                                {m.date_of_death ? <FuzzyDate value={m.date_of_death} /> : null}
                              </span>
                              <MemberStatusBadge status={m.status} />
                            </li>
                          )
                        })}
                      </ul>
                    )}
                    {filteredMembers.length > memberLimit && (
                      <Button variant="outline" className="mt-2 w-full" onClick={() => setMemberLimit((n) => n + MEMBER_STEP)}>
                        Show {Math.min(MEMBER_STEP, filteredMembers.length - memberLimit)} more ({filteredMembers.length - memberLimit} left)
                      </Button>
                    )}
                  </>
                )}
              </section>

              {/* Incidents */}
              <section id="alliance-incidents" className="scroll-mt-4">
                <PanelHeading>Incidents ({incidentItems.length})</PanelHeading>
                {incidentsLoading ? (
                  <Skeleton className="h-40 w-full" />
                ) : incidentItems.length === 0 ? (
                  <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No incidents involve its members.</p>
                ) : (
                  <>
                    <div className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                      {incidentItems.slice(0, incidentLimit).map((inc) => <IncidentRow key={inc.id} inc={inc} />)}
                    </div>
                    {incidentItems.length > incidentLimit && (
                      <Button variant="outline" className="mt-2 w-full" onClick={() => setIncidentLimit((n) => n + 50)}>
                        Show {Math.min(50, incidentItems.length - incidentLimit)} more ({incidentItems.length - incidentLimit} left)
                      </Button>
                    )}
                  </>
                )}
              </section>
            </div>

            <aside className="min-w-0 space-y-5">
              <section>
                <PanelHeading>Details</PanelHeading>
                <dl className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                  <DetailRow label="Status"><AllianceStatusBadge status={alliance.status} /></DetailRow>
                  <DetailRow label="Founded">{alliance.founded_at ? <FuzzyDate value={alliance.founded_at} /> : <None />}</DetailRow>
                  <DetailRow label="Also known as">{alliance.aliases?.length ? alliance.aliases.join(', ') : <None />}</DetailRow>
                  <DetailRow label="Sets">{plural(alliance.set_ids.length, 'set')}</DetailRow>
                  <DetailRow label="Members">
                    {plural(memberItems.length, 'member')}
                    {directMembers > 0 && <span className="text-zinc-500"> ({directMembers} direct)</span>}
                  </DetailRow>
                  <DetailRow label="Added"><span className="text-zinc-400">{timeAgo(alliance.created_at)}</span></DetailRow>
                </dl>
              </section>
              {universe && (
                <section>
                  <PanelHeading>Allies and enemies</PanelHeading>
                  {relationships ? (
                    <AllianceRelationshipsPanel allianceId={alliance.id} universeId={universe.id} relationships={relationships} onAdd={() => setAddingRel(true)} />
                  ) : (
                    <Skeleton className="h-20 w-full" />
                  )}
                </section>
              )}
              {universe && (
                <section>
                  <PanelHeading>Photos</PanelHeading>
                  <Suspense fallback={<Skeleton className="h-32 w-full" />}>
                    <PhotoGallery entityType="alliance" entityId={alliance.id} universeId={universe.id} />
                  </Suspense>
                </section>
              )}
            </aside>
          </div>

          {/* Mounted only while open: each loads the universe's pickers. */}
          {universe && editing && (
            <AllianceFormSheet universeId={universe.id} open onClose={() => setEditing(false)} initial={alliance}
              onSaved={(updated) => {
                setEditing(false)
                const newId = updated.slug ?? updated.id
                if (newId !== id) navigate({ from: '/$universe', to: '/$universe/alliances/$id', params: { id: newId } })
              }} />
          )}
          {universe && addingSet && (
            <AddSetToAllianceDialog allianceId={alliance.id} allianceName={alliance.name} universeId={universe.id} currentSetIds={alliance.set_ids}
              open onClose={() => setAddingSet(false)} onCreateNew={() => { setAddingSet(false); setCreatingSet(true) }} />
          )}
          {universe && addingRel && (
            <AddAllianceRelationshipDialog allianceId={alliance.id} allianceName={alliance.name} universeId={universe.id}
              existing={relationships ?? []} open onClose={() => setAddingRel(false)} />
          )}
          {universe && creatingSet && (
            <SetFormSheet universeId={universe.id} open onClose={() => setCreatingSet(false)} defaultAllianceId={alliance.id} />
          )}
          {universe && addingMember && (
            <AddMemberToAllianceDialog allianceId={alliance.id} allianceName={alliance.name} universeId={universe.id}
              open onClose={() => setAddingMember(false)} onCreateNew={() => { setAddingMember(false); setCreatingMember(true) }} />
          )}
          {universe && creatingMember && (
            <MemberFormSheet universeId={universe.id} open onClose={() => setCreatingMember(false)} defaultAllianceId={alliance.id} />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete alliance"
            description={`Permanently delete "${alliance.name}"? This cannot be undone. Its sets and members stay, unaffiliated.`}
            impact={alliance.set_ids.length || memberItems.length ? (
              // Incidents are untouched: they hang off members, not the alliance.
              <span>{plural(alliance.set_ids.length, 'set')} and {plural(memberItems.length, 'current member')} lose this alliance.</span>
            ) : null}
            confirmLabel="Delete"
            destructive
            pending={deleteAlliance.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />

          {removingSet && universe && (
            <RemoveSetConfirm set={removingSet} allianceId={alliance.id} universeId={universe.id} memberCount={memberCountBySetId[removingSet.id] ?? 0} onClose={() => setRemovingSetId(null)} />
          )}
        </>
      ) : null}
    </div>
  )
}

function RemoveSetConfirm({ set, allianceId, universeId, memberCount, onClose }: {
  set: SetListItem
  allianceId: string
  universeId: string
  memberCount: number
  onClose: () => void
}) {
  const update = useUpdateSet(set.id)

  async function handleConfirm() {
    try {
      // Only this alliance: the set keeps any other it is in.
      await update.mutateAsync({
        universe_id: universeId,
        alliance_ids: allianceRefsOf(set).map((a) => a.id).filter((id) => id !== allianceId),
      })
      toast.success(`Removed "${set.name}" from the alliance`)
      onClose()
    } catch {
      // The global mutation handler has already reported it.
    }
  }

  return (
    <ConfirmDialog
      open
      title="Remove set from alliance"
      description={`Detach "${set.name}" from this alliance? The set itself is not deleted.`}
      impact={memberCount > 0 ? <span>{plural(memberCount, 'current member')} of it leave the alliance's roster, unless tagged to it directly.</span> : null}
      confirmLabel="Remove"
      destructive
      pending={update.isPending}
      onConfirm={handleConfirm}
      onCancel={onClose}
    />
  )
}
