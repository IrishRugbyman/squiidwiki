import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { CheckCircle2, ExternalLink, FileText, MapPin, MoreHorizontal, Pencil, Plus, Trash2, UserPlus, Users } from 'lucide-react'
import { lazy, Suspense, useState } from 'react'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { DetailRow, PanelHeading } from '@/components/detail/DetailParts'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { CopyButton } from '@/components/CopyButton'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { AddParticipantToIncidentDialog } from '@/components/AddParticipantToIncidentDialog'
import { AddSourceToIncidentDialog } from '@/components/AddSourceToIncidentDialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Skeleton } from '@/components/ui/skeleton'
import { useEditShortcut } from '@/hooks/useKeymap'
import { INCIDENT_TYPE_ICON, INCIDENT_TYPE_TILE, OUTCOME_CHIP, OUTCOME_LABEL, ROLE_LABEL } from '@/lib/incidentColors'
import { useDeleteIncident, useIncident, useMunicipality } from '@/lib/queries'
import { MEMBER_STATUS_DOT } from '@/lib/statusColors'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import type { IncidentType, ParticipantRead, ParticipantRole } from '@/lib/types'
import { timeAgo } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth'
import { useRecordRecent } from '@/stores/recents'
import { useUniverseStore } from '@/stores/universe'
import { IncidentFormSheet } from './_app.$universe.incidents.index'
import { MemberFormSheet } from './_app.$universe.members.index'
import { SourceFormSheet } from './_app.$universe.sources.index'
import { LinkifiedText } from '@/components/LinkifiedText'

// The incident page, in its own chunk (the route file only declares it).
export const Route = createLazyFileRoute('/_app/$universe/incidents/$id')({
  component: IncidentDetailPage,
})

const PhotoGallery = lazy(() => import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })))
const IncidentMiniMap = lazy(() => import('@/components/maps/IncidentMiniMap'))

/** Who acted first, then who was hit, then who was only there. */
const ROLE_ORDER: ParticipantRole[] = ['SHOOTER', 'ASSISTED', 'VICTIM', 'BYSTANDER']
const ROLE_HEADING: Record<ParticipantRole, string> = {
  SHOOTER: 'Shooters', ASSISTED: 'Assisted', VICTIM: 'Victims', BYSTANDER: 'Bystanders',
}
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

/** "Murder, May 6 2018": the incident's name wherever it is listed (tab, recents, breadcrumb). */
function incidentLabel(type: IncidentType, date: FuzzyDateValue | null): string {
  const t = titleCase(type)
  if (!date?.year) return t
  if (date.month && date.day) return `${t}, ${MONTHS[date.month - 1]} ${date.day} ${date.year}`
  if (date.month) return `${t}, ${MONTHS[date.month - 1]} ${date.year}`
  return `${t}, ${date.year}`
}

const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase()

function ParticipantAvatar({ p, name }: { p: ParticipantRead; name: string }) {
  const [broken, setBroken] = useState(false)
  if (p.member_photo_url && !broken) {
    return <img src={p.member_photo_url} alt="" loading="lazy" onError={() => setBroken(true)} className="h-9 w-9 shrink-0 rounded-full object-cover ring-1 ring-zinc-700" />
  }
  return (
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-[11px] font-bold text-zinc-300 ring-1 ring-zinc-700" aria-hidden>
      {initials(name) || '?'}
    </span>
  )
}

function ParticipantRow({ p }: { p: ParticipantRead }) {
  const name = p.member_name ?? 'Unknown member'
  return (
    <li className="flex items-start gap-3 px-3 py-2.5">
      <ParticipantAvatar p={p} name={name} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          {p.member_name ? (
            <Link from="/$universe" to="/$universe/members/$id" params={{ id: p.member_slug ?? p.member_id }} className="text-sm font-medium text-white transition-colors hover:text-violet-300">
              {name}
            </Link>
          ) : (
            <span className="text-sm font-medium text-zinc-400">{name}</span>
          )}
          {p.member_status && (
            <span className="inline-flex items-center gap-1 text-[11px] text-zinc-400" title="Status now">
              <span className={`h-1.5 w-1.5 rounded-full ${MEMBER_STATUS_DOT[p.member_status]}`} aria-hidden />
              {titleCase(p.member_status)}
            </span>
          )}
          {p.set_name && (
            <Link from="/$universe" to="/$universe/sets/$id" params={{ id: p.set_slug ?? p.set_id! }} title="Current set"
              className="rounded-full bg-zinc-800/80 px-2 py-0.5 text-[11px] text-zinc-300 transition-colors hover:text-violet-300">
              {p.set_name}
            </Link>
          )}
        </div>
        {p.notes && <p className="mt-1 text-xs leading-snug text-zinc-400">{p.notes}</p>}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <Badge className={`border ${OUTCOME_CHIP[p.outcome]}`}>{OUTCOME_LABEL[p.outcome]}</Badge>
        {p.acquitted && (
          <Badge className="border border-amber-500/40 bg-amber-500/10 text-amber-400" title="A court cleared them of this role">Acquitted</Badge>
        )}
      </div>
    </li>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function IncidentDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const { data: incident, isLoading, isError, refetch } = useIncident(id, universe?.id ?? null)
  const { data: municipality } = useMunicipality(
    incident?.municipality_id ?? '',
    incident?.municipality_id ? (universe?.id ?? null) : null,
  )
  const deleteIncident = useDeleteIncident(universe?.id ?? '')

  useRecordRecent(incident ? { type: 'incident', id: incident.id, slug: null, label: incidentLabel(incident.type, incident.date) } : null)

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [addingParticipant, setAddingParticipant] = useState(false)
  const [creatingMember, setCreatingMember] = useState(false)
  const [addingSource, setAddingSource] = useState(false)
  const [creatingSource, setCreatingSource] = useState(false)

  useEditShortcut(() => incident && setEditing(true))

  if (isError) return <ErrorState title="Incident not found" onRetry={() => refetch()} />

  const label = incident ? incidentLabel(incident.type, incident.date) : 'Incident'

  async function handleDelete() {
    if (!incident) return
    try {
      await deleteIncident.mutateAsync(incident.id)
      navigate({ from: '/$universe', to: '/$universe/incidents' })
    } catch {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-5 pb-8">
      <Breadcrumbs items={[{ label: 'Incidents', to: '/$universe/incidents' }, { label }]} />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : incident ? (() => {
        const Icon = INCIDENT_TYPE_ICON[incident.type]
        const byRole = new Map<ParticipantRole, ParticipantRead[]>()
        for (const p of incident.participants) byRole.set(p.role, [...(byRole.get(p.role) ?? []), p])
        const killed = incident.participants.filter((p) => p.outcome === 'KILLED')
        const injured = incident.participants.filter((p) => p.outcome === 'INJURED')
        const hasCoords = incident.lat != null && incident.lng != null
        // The set most participants run with, to prefill a member created from here.
        const setCounts = new Map<string, number>()
        for (const p of incident.participants) if (p.set_id) setCounts.set(p.set_id, (setCounts.get(p.set_id) ?? 0) + 1)
        const defaultSetId = [...setCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]
        const participantCount = incident.participants.length + incident.set_participants.length

        return (
          <>
            {/* Header */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex min-w-0 items-start gap-3">
                <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg ${INCIDENT_TYPE_TILE[incident.type]}`}>
                  <Icon className="h-6 w-6" aria-hidden />
                </span>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h1 className="text-2xl font-bold leading-tight text-white">{titleCase(incident.type)}</h1>
                    {incident.verified ? (
                      <Badge className="border border-emerald-800/70 bg-emerald-950/30 text-emerald-300"><CheckCircle2 className="mr-1 h-3 w-3" />Verified</Badge>
                    ) : (
                      <span className="rounded-full border border-zinc-800 px-2 py-0.5 text-[11px] text-zinc-500">Unverified</span>
                    )}
                    <CopyButton value={window.location.href} label="Copy link to this incident" className="opacity-40 hover:opacity-100" />
                  </div>
                  <p className="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-zinc-300">
                    <FuzzyDate value={incident.date} fallback="Date unknown" />
                    {municipality && (
                      <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: municipality.id }} className="inline-flex items-center gap-1 text-zinc-300 transition-colors hover:text-violet-300">
                        <MapPin className="h-3 w-3" />{municipality.name}
                      </Link>
                    )}
                  </p>
                  {incident.location_text && <p className="mt-0.5 text-xs text-zinc-400">{incident.location_text}</p>}
                  {(killed.length > 0 || injured.length > 0) && (
                    <p className="mt-2 text-sm">
                      {killed.length > 0 && (
                        <span className="text-rose-300">Killed: {killed.map((p) => p.member_name ?? 'unknown').join(', ')}</span>
                      )}
                      {killed.length > 0 && injured.length > 0 && <span className="text-zinc-600"> · </span>}
                      {injured.length > 0 && (
                        <span className="text-amber-300">Injured: {injured.map((p) => p.member_name ?? 'unknown').join(', ')}</span>
                      )}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => setEditing(true)} title="Edit (e)"><Pencil className="mr-1.5 h-3.5 w-3.5" />Edit</Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button size="sm" variant="outline" aria-label="More actions"><MoreHorizontal className="h-3.5 w-3.5" /></Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => setAddingParticipant(true)}><UserPlus className="mr-2 h-3.5 w-3.5" />Add participant</DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setAddingSource(true)}><FileText className="mr-2 h-3.5 w-3.5" />Cite a source</DropdownMenuItem>
                    {user?.global_role === 'ADMIN' && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => setDeleting(true)} className="text-red-400 focus:text-red-300">
                          <Trash2 className="mr-2 h-3.5 w-3.5" />Delete incident
                        </DropdownMenuItem>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
              <div className="min-w-0 space-y-5">
                {incident.narrative ? (
                  <div className="group relative rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                    <p className="whitespace-pre-wrap pr-6 text-sm leading-relaxed text-zinc-300"><LinkifiedText text={incident.narrative} /></p>
                    <button type="button" onClick={() => setEditing(true)} aria-label="Edit narrative"
                      className="absolute right-2 top-2 rounded p-1.5 text-zinc-400 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 focus-visible:opacity-100 group-hover:opacity-100 pointer-fine:opacity-0">
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ) : (
                  <button type="button" onClick={() => setEditing(true)}
                    className="flex w-full items-center gap-2 rounded-lg border border-dashed border-zinc-800 px-4 py-3 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200">
                    <Pencil className="h-3 w-3" />Add what happened
                  </button>
                )}

                {/* Participants, by role */}
                <section>
                  <PanelHeading action={
                    <button type="button" onClick={() => setAddingParticipant(true)} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
                      <Plus className="h-3 w-3" />Add
                    </button>
                  }>Participants{participantCount > 0 ? ` (${participantCount})` : ''}</PanelHeading>
                  {participantCount === 0 ? (
                    <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No participants recorded.</p>
                  ) : (
                    <div className="space-y-3">
                      {ROLE_ORDER.filter((r) => byRole.has(r)).map((role) => (
                        <div key={role}>
                          <h3 className="mb-1 px-1 text-[11px] font-medium text-zinc-500">{ROLE_HEADING[role]}</h3>
                          <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                            {byRole.get(role)!.map((p) => <ParticipantRow key={p.member_id} p={p} />)}
                          </ul>
                        </div>
                      ))}
                      {incident.set_participants.length > 0 && (
                        <div>
                          <h3 className="mb-1 px-1 text-[11px] font-medium text-zinc-500" title="A set known to be involved where no member can be named">Attributed to a set</h3>
                          <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                            {incident.set_participants.map((p) => (
                              <li key={p.set_id} className="flex items-center gap-3 px-3 py-2.5">
                                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-zinc-800 ring-1 ring-zinc-700"><Users className="h-4 w-4 text-zinc-400" aria-hidden /></span>
                                <Link from="/$universe" to="/$universe/sets/$id" params={{ id: p.set_slug ?? p.set_id }} className="min-w-0 flex-1 truncate text-sm font-medium text-white transition-colors hover:text-violet-300">
                                  {p.set_name ?? 'Unknown set'}
                                </Link>
                                <Badge variant="outline" className="border-zinc-700 text-[11px] text-zinc-400">{ROLE_LABEL[p.role]}</Badge>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </section>

                {/* Sources */}
                <section>
                  <PanelHeading action={
                    <button type="button" onClick={() => setAddingSource(true)} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
                      <Plus className="h-3 w-3" />Cite
                    </button>
                  }>Sources{incident.sources.length > 0 ? ` (${incident.sources.length})` : ''}</PanelHeading>
                  {incident.sources.length === 0 ? (
                    <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No sources cited.</p>
                  ) : (
                    <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                      {incident.sources.map((s) => (
                        <li key={s.id} className="flex items-center gap-3 px-3 py-2.5">
                          <Link from="/$universe" to="/$universe/sources/$id" params={{ id: s.id }} className="group min-w-0 flex-1">
                            <span className="block truncate text-sm font-medium text-white transition-colors group-hover:text-violet-300">{s.title}</span>
                            {s.publication && <span className="block truncate text-[11px] text-zinc-500">{s.publication}</span>}
                          </Link>
                          <ReliabilityBadge reliability={s.reliability} />
                          <a href={s.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${s.title} in a new tab`}
                            className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-300">
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>

                {universe && (
                  <section>
                    <PanelHeading>Photos</PanelHeading>
                    <Suspense fallback={<Skeleton className="h-32 w-full" />}>
                      <PhotoGallery entityType="incident" entityId={incident.id} universeId={universe.id} />
                    </Suspense>
                  </section>
                )}
              </div>

              <aside className="min-w-0 space-y-5">
                {hasCoords && (
                  <section>
                    <PanelHeading>Location</PanelHeading>
                    <div className="h-56 overflow-hidden rounded-lg border border-zinc-800">
                      <Suspense fallback={<Skeleton className="h-full w-full" />}>
                        <IncidentMiniMap lat={incident.lat!} lng={incident.lng!} type={incident.type} />
                      </Suspense>
                    </div>
                  </section>
                )}
                <section>
                  <PanelHeading>Details</PanelHeading>
                  <dl className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                    <DetailRow label="Date"><FuzzyDate value={incident.date} fallback="Unknown" /></DetailRow>
                    <DetailRow label="Type">{titleCase(incident.type)}</DetailRow>
                    <DetailRow label="Municipality">
                      {municipality ? (
                        <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: municipality.id }} className="text-violet-400 hover:underline">{municipality.name}</Link>
                      ) : <span className="text-zinc-500">-</span>}
                    </DetailRow>
                    {incident.location_text && <DetailRow label="Place">{incident.location_text}</DetailRow>}
                    {hasCoords && (
                      <DetailRow label="Coordinates">
                        <span className="inline-flex items-center gap-1 font-mono text-xs text-zinc-300">
                          {incident.lat!.toFixed(5)}, {incident.lng!.toFixed(5)}
                          <CopyButton value={`${incident.lat}, ${incident.lng}`} label="Copy coordinates" className="opacity-50 hover:opacity-100" />
                        </span>
                      </DetailRow>
                    )}
                    <DetailRow label="Verified">{incident.verified ? 'Yes' : 'No'}</DetailRow>
                    <DetailRow label="Added"><span className="text-zinc-400">{timeAgo(incident.created_at)}</span></DetailRow>
                    <DetailRow label="Updated"><span className="text-zinc-400">{timeAgo(incident.updated_at)}</span></DetailRow>
                  </dl>
                </section>
              </aside>
            </div>

            {/* Mounted only while open: each loads the universe's members, sets,
                alliances and gangs for its pickers, which the page itself never needs. */}
            {universe && editing && <IncidentFormSheet universeId={universe.id} open onClose={() => setEditing(false)} initial={incident} />}
            {universe && addingParticipant && (
              <AddParticipantToIncidentDialog incident={incident} universeId={universe.id} open
                onClose={() => setAddingParticipant(false)} onCreateNew={() => { setAddingParticipant(false); setCreatingMember(true) }} />
            )}
            {universe && creatingMember && (
              <MemberFormSheet universeId={universe.id} open onClose={() => setCreatingMember(false)} defaultSetId={defaultSetId} />
            )}
            {universe && addingSource && (
              <AddSourceToIncidentDialog incident={incident} universeId={universe.id} open
                onClose={() => setAddingSource(false)} onCreateNew={() => { setAddingSource(false); setCreatingSource(true) }} />
            )}
            {universe && creatingSource && <SourceFormSheet universeId={universe.id} open onClose={() => setCreatingSource(false)} />}

            <ConfirmDialog
              open={deleting}
              title="Delete incident"
              description={`Permanently delete this ${incident.type.toLowerCase()}? This cannot be undone.`}
              impact={participantCount > 0 || killed.length > 0 ? (
                <span>
                  {incident.participants.length > 0 && <>It leaves the timeline of {incident.participants.length} member{incident.participants.length === 1 ? '' : 's'}. </>}
                  {killed.length > 0 && <>{killed.map((p) => p.member_name ?? 'A member').join(', ')} stay{killed.length === 1 ? 's' : ''} marked dead, with no incident linked to the death.</>}
                </span>
              ) : null}
              confirmLabel="Delete"
              destructive
              pending={deleteIncident.isPending}
              onConfirm={handleDelete}
              onCancel={() => setDeleting(false)}
            />
          </>
        )
      })() : null}
    </div>
  )
}
