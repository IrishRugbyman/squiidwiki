import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Copy, MapPin, Mic, MoreHorizontal, Pencil, Swords, Trash2, Users } from 'lucide-react'
import { lazy, Suspense, useState } from 'react'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { CopyButton } from '@/components/CopyButton'
import { DetailRow, IncidentRow, None, PanelHeading, StatStrip } from '@/components/detail/DetailParts'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { LinkifiedText } from '@/components/LinkifiedText'
import { NameVariantChips } from '@/components/names/NameVariantChips'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { CitationsPanel } from '@/components/sources/CitationsPanel'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Skeleton } from '@/components/ui/skeleton'
import { useEditShortcut } from '@/hooks/useKeymap'
import { useDeleteRapGroup, useRapGroup } from '@/lib/queries'
import type { RapGroupReadDetail } from '@/lib/types'
import { timeAgo } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth'
import { useRecordRecent } from '@/stores/recents'
import { useUniverseStore } from '@/stores/universe'
import { RAP_KIND_LABEL, RAP_ROLE_LABEL, RAP_STATUS_LABEL, RapGroupFormSheet } from './_app.$universe.rap-groups.index'
import { SetAvatar } from './_app.$universe.sets.index'

// The rap group / label page, in its own chunk. Not a set: no map, no set stats.
export const Route = createLazyFileRoute('/_app/$universe/rap-groups/$id')({
  component: RapGroupDetailPage,
})

const PhotoGallery = lazy(() => import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })))

const INCIDENT_STEP = 25
const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

const KIND_PILL: Record<RapGroupReadDetail['kind'], string> = {
  GROUP: 'bg-fuchsia-950/50 text-fuchsia-300 ring-1 ring-fuchsia-800/60',
  LABEL: 'bg-sky-950/50 text-sky-300 ring-1 ring-sky-800/60',
}

function MemberThumb({ name, url }: { name: string; url: string | null }) {
  const [broken, setBroken] = useState(false)
  if (url && !broken) {
    return <img src={url} alt="" loading="lazy" decoding="async" onError={() => setBroken(true)} className="h-7 w-7 shrink-0 rounded-full object-cover ring-1 ring-zinc-700" />
  }
  return (
    <span aria-hidden className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-xs font-medium text-zinc-300 ring-1 ring-zinc-700">
      {name.charAt(0).toUpperCase()}
    </span>
  )
}

function RapGroupDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const universeId = universe?.id ?? null
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: group, isLoading, isError, refetch } = useRapGroup(id, universeId)
  const deleteGroup = useDeleteRapGroup(universe?.id ?? '')
  useRecordRecent(group ? { type: 'rap_group', id: group.id, slug: group.slug, label: group.name } : null)

  const [editing, setEditing] = useState(false)
  const [duplicating, setDuplicating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [incidentLimit, setIncidentLimit] = useState(INCIDENT_STEP)

  useEditShortcut(() => group && setEditing(true))

  if (isError) return <ErrorState title="Rap group not found" onRetry={() => refetch()} />

  async function handleDelete() {
    if (!group) return
    try {
      await deleteGroup.mutateAsync(group.id)
      navigate({ from: '/$universe', to: '/$universe/rap-groups' })
    } catch {
      setDeleting(false)
    }
  }

  const noun = group?.kind === 'LABEL' ? 'label' : 'rap group'
  const allies = (group?.relationships ?? []).filter((r) => r.type === 'FRIEND')
  const enemies = (group?.relationships ?? []).filter((r) => r.type === 'ENEMY')
  const incidents = group?.incidents ?? []
  const deadCount = (group?.members ?? []).filter((m) => m.status === 'DEAD').length
  const lockedCount = (group?.members ?? []).filter((m) => m.status === 'LOCKED').length

  return (
    <div className="space-y-5 pb-8">
      <Breadcrumbs items={[{ label: 'Rap groups & labels', to: '/$universe/rap-groups' }, { label: group?.name ?? 'Rap group' }]} />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : group ? (
        <>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex min-w-0 items-start gap-4">
              <SetAvatar name={group.name} thumbUrl={group.primary_photo_url} size="xl" />
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-2xl font-bold leading-tight text-white">{group.name}</h1>
                  <CopyButton value={window.location.href} label={`Copy link to this ${noun}`} className="opacity-40 hover:opacity-100" />
                </div>
                <NameVariantChips variants={group.name_variants} />
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs ${KIND_PILL[group.kind]}`}>
                    <Mic className="h-3 w-3" aria-hidden />{RAP_KIND_LABEL[group.kind]}
                  </span>
                  <Badge variant="secondary" className={group.status === 'ACTIVE' ? 'text-emerald-300' : 'text-zinc-400'}>{RAP_STATUS_LABEL[group.status].toUpperCase()}</Badge>
                  {group.municipality && (
                    <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: group.municipality.slug ?? group.municipality.id }}
                      className="inline-flex items-center gap-1 rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-violet-300">
                      <MapPin className="h-3 w-3" />{group.municipality.name}
                    </Link>
                  )}
                  {(group.active_from || group.active_to) && (
                    <span className="rounded-full border border-zinc-800 bg-zinc-900/50 px-2 py-0.5 text-[11px] text-zinc-400">
                      Active {group.active_from ? <FuzzyDate value={group.active_from} /> : '?'} to {group.active_to ? <FuzzyDate value={group.active_to} /> : 'present'}
                    </span>
                  )}
                  <span className="text-[11px] text-zinc-400">Updated {timeAgo(group.updated_at)}</span>
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
                  <DropdownMenuItem onClick={() => setDuplicating(true)}><Copy className="mr-2 h-3.5 w-3.5" />Duplicate</DropdownMenuItem>
                  {user?.global_role === 'ADMIN' && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setDeleting(true)} className="text-red-400 focus:text-red-300">
                        <Trash2 className="mr-2 h-3.5 w-3.5" />Delete {noun}
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <StatStrip cells={[
            { label: group.kind === 'LABEL' ? 'Artists' : 'Members', value: group.members.length, accent: 'text-fuchsia-400' },
            { label: 'Locked', value: lockedCount, accent: 'text-orange-400' },
            { label: 'Dead', value: deadCount, accent: 'text-zinc-200' },
            { label: 'Sets', value: group.sets_represented.length, accent: 'text-violet-400', title: 'Sets its members belong to' },
            { label: 'Incidents', value: incidents.length, accent: 'text-amber-400', title: 'Incidents involving its members' },
          ]} />

          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="min-w-0 space-y-5">
              {group.bio && (
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300"><LinkifiedText text={group.bio} /></p>
                </div>
              )}

              <section>
                <PanelHeading>{group.kind === 'LABEL' ? 'Artists' : 'Members'} ({group.members.length})</PanelHeading>
                {group.members.length === 0 ? (
                  <EmptyState icon={Users} title="No members yet" description={`Add the people in this ${noun} from Edit.`}
                    action={<Button size="sm" onClick={() => setEditing(true)}><Pencil className="mr-1.5 h-3.5 w-3.5" />Edit</Button>} />
                ) : (
                  <div className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {group.members.map((m) => (
                      <div key={m.member_id} className="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-3 py-2.5">
                        <Link from="/$universe" to="/$universe/members/$id" params={{ id: m.slug ?? m.member_id }}
                          className="group flex min-w-0 flex-1 basis-48 items-center gap-3 focus-visible:outline-none">
                          <MemberThumb name={m.display_name} url={m.primary_photo_thumb_url} />
                          <span className="min-w-0">
                            <span className="block truncate text-sm font-medium text-white transition-colors group-hover:text-fuchsia-300 group-focus-visible:text-fuchsia-300">{m.display_name}</span>
                            <span className="block text-[11px] text-zinc-400">
                              {RAP_ROLE_LABEL[m.role]}
                              {(m.since || m.until) && (
                                <> · {m.since ? <FuzzyDate value={m.since} /> : '?'} to {m.until ? <FuzzyDate value={m.until} /> : 'present'}</>
                              )}
                            </span>
                          </span>
                        </Link>
                        <span className="flex flex-wrap items-center gap-1.5">
                          {m.sets.map((s) => (
                            <Link key={s.id} from="/$universe" to="/$universe/sets/$id" params={{ id: s.slug ?? s.id }}
                              className="rounded-full bg-zinc-800/70 px-2 py-0.5 text-[11px] text-zinc-300 ring-1 ring-violet-700/30 transition-colors hover:bg-zinc-800 hover:text-violet-400">
                              {s.name}
                            </Link>
                          ))}
                          <MemberStatusBadge status={m.status} />
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <PanelHeading>Incidents ({incidents.length})</PanelHeading>
                {incidents.length === 0 ? (
                  <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No incidents involve its members.</p>
                ) : (
                  <>
                    <div className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                      {incidents.slice(0, incidentLimit).map((inc) => <IncidentRow key={inc.id} inc={inc} />)}
                    </div>
                    {incidents.length > incidentLimit && (
                      <Button size="sm" variant="outline" className="mt-2" onClick={() => setIncidentLimit((n) => n + INCIDENT_STEP)}>
                        Show more ({incidents.length - incidentLimit} left)
                      </Button>
                    )}
                  </>
                )}
              </section>

              {universe && (
                <section>
                  <PanelHeading>Photos</PanelHeading>
                  <Suspense fallback={<Skeleton className="h-32 w-full" />}>
                    <PhotoGallery entityType="rap_group" entityId={group.id} universeId={universe.id} />
                  </Suspense>
                </section>
              )}
            </div>

            <aside className="min-w-0 space-y-5">
              <section>
                <PanelHeading>Details</PanelHeading>
                <dl className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                  <DetailRow label="Kind">{RAP_KIND_LABEL[group.kind]}</DetailRow>
                  <DetailRow label="Status">{RAP_STATUS_LABEL[group.status]}</DetailRow>
                  <DetailRow label="Active from">{group.active_from ? <FuzzyDate value={group.active_from} /> : <None />}</DetailRow>
                  <DetailRow label="Active to">{group.active_to ? <FuzzyDate value={group.active_to} /> : <None />}</DetailRow>
                  <DetailRow label="Home area">{group.municipality?.name ?? <None />}</DetailRow>
                  <DetailRow label="Added"><span className="text-zinc-400">{timeAgo(group.created_at)}</span></DetailRow>
                </dl>
              </section>

              <section>
                <PanelHeading>Sets represented</PanelHeading>
                {group.sets_represented.length === 0 ? (
                  <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">None of its members are in a set.</p>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {group.sets_represented.map((s) => (
                      <Link key={s.id} from="/$universe" to="/$universe/sets/$id" params={{ id: s.slug ?? s.id }}
                        className="inline-flex items-center gap-1.5 rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-300 ring-1 ring-violet-700/30 transition-colors hover:bg-zinc-800 hover:text-violet-400">
                        {s.name}
                        <span className="tabular-nums text-zinc-500">{s.count}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <PanelHeading>Feuds and allies</PanelHeading>
                {allies.length + enemies.length === 0 ? (
                  <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No allies or enemies on file.</p>
                ) : (
                  <ul className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {[...enemies, ...allies].map((r) => (
                      <li key={r.rap_group_id}>
                        <Link from="/$universe" to="/$universe/rap-groups/$id" params={{ id: r.slug ?? r.rap_group_id }}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-200 transition-colors hover:bg-zinc-900/60 hover:text-white">
                          {r.type === 'ENEMY'
                            ? <Swords className="h-3.5 w-3.5 shrink-0 text-red-400" aria-label="Enemy" />
                            : <Users className="h-3.5 w-3.5 shrink-0 text-emerald-400" aria-label="Ally" />}
                          <span className="min-w-0 flex-1 truncate">{r.name}</span>
                          <span className="text-[10px] text-zinc-500">{r.type === 'ENEMY' ? 'Enemy' : 'Ally'}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              {universe && (
                <CitationsPanel universeId={universe.id} entityType="rap_group" entityId={group.id} citations={group.citations ?? []} />
              )}
            </aside>
          </div>

          {/* Mounted only while open: each loads the universe's pickers. */}
          {universe && editing && (
            <RapGroupFormSheet universeId={universe.id} open onClose={() => setEditing(false)} initial={group}
              onSaved={(updated) => {
                setEditing(false)
                const newId = updated.slug ?? updated.id
                if (newId !== id) navigate({ from: '/$universe', to: '/$universe/rap-groups/$id', params: { id: newId } })
              }} />
          )}
          {universe && duplicating && (
            <RapGroupFormSheet universeId={universe.id} open onClose={() => setDuplicating(false)} copyFrom={group}
              onSaved={(created) => navigate({ from: '/$universe', to: '/$universe/rap-groups/$id', params: { id: created.slug ?? created.id } })} />
          )}

          <ConfirmDialog
            open={deleting}
            title={`Delete ${noun}`}
            description={`Permanently delete "${group.name}"? This cannot be undone. Its members stay.`}
            impact={group.members.length ? <span>{plural(group.members.length, 'member')} lose this {noun} on their page.</span> : null}
            confirmLabel="Delete"
            destructive
            pending={deleteGroup.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
