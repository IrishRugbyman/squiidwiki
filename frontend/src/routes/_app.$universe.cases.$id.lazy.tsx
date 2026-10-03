import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ExternalLink, FileText, Gavel, Link2, MoreHorizontal, Pencil, Plus, Trash2, UserPlus, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { AttachSourcesDialog } from '@/components/AttachSourcesDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { DefendantDialog } from '@/components/cases/DefendantDialog'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { CopyButton } from '@/components/CopyButton'
import { DetailRow, IncidentRow, PanelHeading, UniverseChip } from '@/components/detail/DetailParts'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate } from '@/components/FuzzyDate'
import { LinkifiedText } from '@/components/LinkifiedText'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useDebounce } from '@/hooks/useDebounce'
import { useEditShortcut } from '@/hooks/useKeymap'
import {
  CASE_KIND_LABEL, courtAndDocket, DISPOSITION_CHIP, DISPOSITION_LABEL, formatSentence, JURISDICTION_LABEL, servedByMember,
} from '@/lib/courtCases'
import { INCIDENT_TYPE_LABEL } from '@/lib/incidentColors'
import { MEMBER_STATUS_DOT } from '@/lib/statusColors'
import {
  useCourtCase, useDeleteCourtCase, useDeleteDefendant, useIncidentSearch, useUniverses, useUpdateCourtCase,
} from '@/lib/queries'
import type { CourtCaseBrief, CourtCaseReadDetail, DefendantRead, UUID } from '@/lib/types'
import { paramsIn } from '@/lib/universeRoutes'
import { useAuthStore } from '@/stores/auth'
import { useRecordRecent } from '@/stores/recents'
import { useUniverseStore } from '@/stores/universe'
import { SourceFormSheet } from './_app.$universe.sources.index'
import { CourtCaseFormSheet } from './_app.$universe.cases.index'

// The court case page, in its own chunk (the route file only declares it).
export const Route = createLazyFileRoute('/_app/$universe/cases/$id')({
  component: CourtCaseDetailPage,
})

const titleCase = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

function CaseLink({ c }: { c: CourtCaseBrief }) {
  return (
    <Link from="/$universe" to="/$universe/cases/$id" params={paramsIn(c.universe_slug, c.slug ?? c.id)}
      className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-200 transition-colors hover:bg-zinc-900/60 hover:text-violet-300">
      <Gavel className="h-3.5 w-3.5 shrink-0 text-zinc-500" aria-hidden />
      <span className="min-w-0 flex-1 truncate">{c.name}</span>
      <span className="shrink-0 text-[11px] text-zinc-500">{c.kind !== 'CRIMINAL' ? CASE_KIND_LABEL[c.kind] : courtAndDocket(c)}</span>
      <UniverseChip slug={c.universe_slug} />
    </Link>
  )
}

function DefendantRow({ d, onEdit, onRemove }: { d: DefendantRead; onEdit: () => void; onRemove: () => void }) {
  const name = d.member_name ?? d.label ?? 'Unnamed defendant'
  const sentence = formatSentence(d.sentence_months, d.life_sentence)
  const supervised = formatSentence(d.supervised_release_months)
  return (
    <li className="group flex items-start gap-3 px-3 py-2.5">
      <span className="w-10 shrink-0 pt-0.5 font-mono text-[11px] text-zinc-500">{d.defendant_number ?? ''}</span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          {d.member_id ? (
            <Link from="/$universe" to="/$universe/members/$id" params={paramsIn(d.member_universe_slug, d.member_slug ?? d.member_id)}
              className="text-sm font-medium text-white transition-colors hover:text-violet-300">{name}</Link>
          ) : (
            <span className="text-sm font-medium text-zinc-300" title="No member in the wiki">{name}</span>
          )}
          {d.member_id && d.label && d.label !== name && <span className="text-xs text-zinc-500">{d.label}</span>}
          {d.member_status && (
            <span className="inline-flex items-center gap-1 text-[11px] text-zinc-400" title="Status now">
              <span className={`h-1.5 w-1.5 rounded-full ${MEMBER_STATUS_DOT[d.member_status]}`} aria-hidden />
              {titleCase(d.member_status)}
            </span>
          )}
          {d.cooperated && <span className="rounded-full border border-amber-800/60 px-1.5 py-0.5 text-[10px] text-amber-300">Cooperated</span>}
        </div>
        {d.charges.length > 0 && (
          <ul className="mt-1 space-y-0.5 text-xs text-zinc-400">
            {d.charges.map((c, i) => (
              <li key={i}>
                {c.count != null && <span className="text-zinc-500">Count {c.count}: </span>}
                {c.offense}
                {c.statute && <span className="ml-1 font-mono text-[11px] text-zinc-500">{c.statute}</span>}
              </li>
            ))}
          </ul>
        )}
        {d.notes && <p className="mt-1 text-xs leading-snug text-zinc-400">{d.notes}</p>}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1 text-right">
        <Badge className={`border ${DISPOSITION_CHIP[d.disposition]}`}>{DISPOSITION_LABEL[d.disposition]}</Badge>
        {sentence && <span className="text-xs tabular-nums text-zinc-300">{sentence}</span>}
        {supervised && <span className="text-[11px] tabular-nums text-zinc-500">+{supervised} supervised</span>}
        {d.sentenced_at?.year && <span className="text-[11px] text-zinc-500"><FuzzyDate value={d.sentenced_at} /></span>}
      </div>
      <div className="flex shrink-0 items-center gap-0.5 transition-opacity pointer-fine:opacity-0 group-hover:opacity-100 focus-within:opacity-100">
        <button type="button" onClick={onEdit} aria-label={`Edit ${name}`} className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"><Pencil className="h-3.5 w-3.5" /></button>
        <button type="button" onClick={onRemove} aria-label={`Remove ${name}`} className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-red-300"><X className="h-3.5 w-3.5" /></button>
      </div>
    </li>
  )
}

/** Link incidents to the case. A case can cover an incident in another universe
 *  (a Michigan case over an Ohio shooting), so the search runs in the universe picked. */
function LinkIncidentsDialog({ c, open, onClose }: { c: CourtCaseReadDetail; open: boolean; onClose: () => void }) {
  const update = useUpdateCourtCase(c.id, c.universe_id)
  const { data: universes } = useUniverses()
  const [searchUniverse, setSearchUniverse] = useState<UUID>(c.universe_id)
  const [query, setQuery] = useState('')
  const debounced = useDebounce(query, 200)
  const { data: hits = [] } = useIncidentSearch(searchUniverse, debounced)
  const linked = new Set(c.incidents.map((i) => i.id))

  async function link(id: UUID) {
    await update.mutateAsync({ incident_ids: [...c.incidents.map((i) => i.id), id] })
    toast.success('Incident linked')
    setQuery('')
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Link2 className="h-4 w-4 text-violet-400" />Link an incident</DialogTitle>
          <DialogDescription>An act the case covers. Its defendants' verdicts then apply to their part in it.</DialogDescription>
        </DialogHeader>
        <div className="flex gap-2">
          <Select value={searchUniverse} onValueChange={(v) => { if (v) setSearchUniverse(v) }}>
            <SelectTrigger className="w-36 shrink-0" aria-label="Universe to search"><SelectValue /></SelectTrigger>
            <SelectContent>
              {(universes?.items ?? []).map((u) => <SelectItem key={u.id} value={u.id}>{u.name}</SelectItem>)}
            </SelectContent>
          </Select>
          <Input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search incidents by place or narrative" />
        </div>
        <ul className="max-h-72 divide-y divide-zinc-800/70 overflow-y-auto rounded-md border border-zinc-800">
          {query.length >= 2 && hits.length === 0 && <li className="px-3 py-2 text-xs text-zinc-500">No match.</li>}
          {hits.map((inc) => (
            <li key={inc.id}>
              <button type="button" disabled={linked.has(inc.id) || update.isPending} onClick={() => link(inc.id)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-zinc-200 hover:bg-zinc-800 disabled:opacity-40">
                <span className="w-20 shrink-0 text-xs text-zinc-400"><FuzzyDate value={inc.date} fallback="Undated" /></span>
                <span className="shrink-0 text-xs text-zinc-500">{INCIDENT_TYPE_LABEL[inc.type]}</span>
                <span className="min-w-0 flex-1 truncate">{inc.location_text ?? inc.municipality_name ?? ''}</span>
                {linked.has(inc.id) && <span className="text-[11px] text-zinc-500">linked</span>}
              </button>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  )
}

function CourtCaseDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const { data: c, isLoading, isError, refetch } = useCourtCase(id, universe?.id ?? null)
  const update = useUpdateCourtCase(c?.id ?? '', c?.universe_id ?? '')
  const deleteCase = useDeleteCourtCase(c?.universe_id ?? '')
  const deleteDefendant = useDeleteDefendant(c?.id ?? '', c?.universe_id ?? '')

  useRecordRecent(c ? { type: 'case', id: c.id, slug: c.slug, label: c.name } : null)

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [defendant, setDefendant] = useState<DefendantRead | 'new' | null>(null)
  const [removing, setRemoving] = useState<DefendantRead | null>(null)
  const [linking, setLinking] = useState(false)
  const [citing, setCiting] = useState(false)
  const [creatingSource, setCreatingSource] = useState(false)

  useEditShortcut(() => c && setEditing(true))

  if (isError) return <ErrorState title="Court case not found" onRetry={() => refetch()} />

  async function handleDelete() {
    if (!c) return
    try {
      await deleteCase.mutateAsync(c.id)
      navigate({ from: '/$universe', to: '/$universe/cases' })
    } catch {
      setDeleting(false)
    }
  }

  async function unlinkIncident(incidentId: UUID) {
    if (!c) return
    await update.mutateAsync({ incident_ids: c.incidents.filter((i) => i.id !== incidentId).map((i) => i.id) })
    toast.success('Incident unlinked')
  }

  const plus = (onClick: () => void, label: string) => (
    <button type="button" onClick={onClick} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
      <Plus className="h-3 w-3" />{label}
    </button>
  )

  return (
    <div className="space-y-5 pb-8">
      <Breadcrumbs items={[{ label: 'Court cases', to: '/$universe/cases' }, { label: c?.name ?? 'Court case' }]} />

      {isLoading || !c ? <DetailHeaderSkeleton /> : (
        <>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex min-w-0 items-start gap-3">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-zinc-800 text-zinc-200 ring-1 ring-zinc-700">
                <Gavel className="h-6 w-6" aria-hidden />
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-2xl font-bold leading-tight text-white">{c.name}</h1>
                  {c.kind !== 'CRIMINAL' && <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[11px] text-zinc-300">{CASE_KIND_LABEL[c.kind]}</span>}
                  <CopyButton value={window.location.href} label="Copy link to this case" className="opacity-40 hover:opacity-100" />
                </div>
                <p className="mt-1 text-sm text-zinc-300">
                  {c.court}{c.docket && <span className="ml-2 font-mono text-zinc-200">{c.docket}</span>}
                </p>
                <p className="mt-0.5 flex flex-wrap gap-x-3 text-xs text-zinc-400">
                  {c.filed_at?.year && <span>Filed <FuzzyDate value={c.filed_at} /></span>}
                  {c.closed_at?.year && <span>Closed <FuzzyDate value={c.closed_at} /></span>}
                  {c.judge && <span>{c.judge}</span>}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)} title="Edit (e)"><Pencil className="mr-1.5 h-3.5 w-3.5" />Edit</Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="outline" aria-label="More actions"><MoreHorizontal className="h-3.5 w-3.5" /></Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setDefendant('new')}><UserPlus className="mr-2 h-3.5 w-3.5" />Add defendant</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setLinking(true)}><Link2 className="mr-2 h-3.5 w-3.5" />Link an incident</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setCiting(true)}><FileText className="mr-2 h-3.5 w-3.5" />Cite a source</DropdownMenuItem>
                  {user?.global_role === 'ADMIN' && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setDeleting(true)} className="text-red-400 focus:text-red-300">
                        <Trash2 className="mr-2 h-3.5 w-3.5" />Delete case
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
            <div className="min-w-0 space-y-5">
              {c.summary && (
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300"><LinkifiedText text={c.summary} /></p>
                </div>
              )}

              <section>
                <PanelHeading action={plus(() => setDefendant('new'), 'Add')}>
                  Defendants{c.defendants.length > 0 ? ` (${c.defendants.length})` : ''}
                </PanelHeading>
                {c.defendants.length === 0 ? (
                  <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No defendants recorded.</p>
                ) : (
                  <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {c.defendants.map((d) => (
                      <DefendantRow key={d.id} d={d} onEdit={() => setDefendant(d)} onRemove={() => setRemoving(d)} />
                    ))}
                  </ul>
                )}
              </section>

              <section>
                <PanelHeading action={plus(() => setLinking(true), 'Link')}>
                  Incidents{c.incidents.length > 0 ? ` (${c.incidents.length})` : ''}
                </PanelHeading>
                {c.incidents.length === 0 ? (
                  <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No incidents linked.</p>
                ) : (
                  <ul className="divide-y divide-zinc-800/70 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {c.incidents.map((inc) => (
                      <li key={inc.id} className="group flex items-center">
                        <div className="min-w-0 flex-1"><IncidentRow inc={inc} /></div>
                        <button type="button" onClick={() => unlinkIncident(inc.id)} aria-label="Unlink this incident" title="Unlink"
                          className="mr-2 rounded p-1.5 text-zinc-400 transition-opacity hover:bg-zinc-800 hover:text-red-300 pointer-fine:opacity-0 group-hover:opacity-100 focus-visible:opacity-100">
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section>
                <PanelHeading action={plus(() => setCiting(true), 'Cite')}>
                  Sources{c.sources.length > 0 ? ` (${c.sources.length})` : ''}
                </PanelHeading>
                {c.sources.length === 0 ? (
                  <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No sources cited.</p>
                ) : (
                  <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {c.sources.map((s) => (
                      <li key={s.id} className="flex items-center gap-3 px-3 py-2.5">
                        <Link from="/$universe" to="/$universe/sources/$id" params={paramsIn(c.universe_slug, s.id)} className="group min-w-0 flex-1">
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
            </div>

            <aside className="min-w-0 space-y-5">
              <section>
                <PanelHeading>Details</PanelHeading>
                <dl className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                  <DetailRow label="Court">{c.court}</DetailRow>
                  <DetailRow label="Docket">{c.docket ? <span className="font-mono">{c.docket}</span> : <span className="text-zinc-500">-</span>}</DetailRow>
                  {c.docket_aliases.length > 0 && (
                    <DetailRow label="Also written">
                      <span className="flex flex-col font-mono text-xs">{c.docket_aliases.map((a) => <span key={a}>{a}</span>)}</span>
                    </DetailRow>
                  )}
                  <DetailRow label="Jurisdiction">{JURISDICTION_LABEL[c.jurisdiction]}</DetailRow>
                  <DetailRow label="Kind">{CASE_KIND_LABEL[c.kind]}</DetailRow>
                  <DetailRow label="Filed"><FuzzyDate value={c.filed_at} fallback="Unknown" /></DetailRow>
                  <DetailRow label="Closed"><FuzzyDate value={c.closed_at} fallback="Open or unknown" /></DetailRow>
                  {c.judge && <DetailRow label="Judge">{c.judge}</DetailRow>}
                  {c.courtlistener_ids.length > 0 && (
                    <DetailRow label="CourtListener">
                      <span className="flex flex-wrap gap-x-2">
                        {c.courtlistener_ids.map((n) => (
                          <a key={n} href={`https://www.courtlistener.com/docket/${n}/`} target="_blank" rel="noopener noreferrer" className="font-mono text-xs text-violet-400 hover:underline">{n}</a>
                        ))}
                      </span>
                    </DetailRow>
                  )}
                </dl>
              </section>

              {c.sets.length > 0 && (
                <section>
                  <PanelHeading>Sets</PanelHeading>
                  <div className="flex flex-wrap gap-1.5">
                    {c.sets.map((s) => (
                      <Link key={s.id} from="/$universe" to="/$universe/sets/$id" params={paramsIn(c.universe_slug, s.slug ?? s.id)}
                        className="rounded-full bg-zinc-800/80 px-2.5 py-1 text-xs text-zinc-200 transition-colors hover:text-violet-300">{s.name}</Link>
                    ))}
                  </div>
                </section>
              )}

              {(c.parent || c.children.length > 0) && (
                <section>
                  <PanelHeading>Related cases</PanelHeading>
                  <div className="divide-y divide-zinc-800/70 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {c.parent && <CaseLink c={c.parent} />}
                    {c.children.map((ch) => <CaseLink key={ch.id} c={ch} />)}
                  </div>
                </section>
              )}

              {c.spells.length > 0 && (
                <section>
                  <PanelHeading>Time served</PanelHeading>
                  <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                    {servedByMember(c.spells).map((s) => (
                      <li key={s.memberId} className="px-3 py-2 text-sm">
                        <Link from="/$universe" to="/$universe/members/$id" params={paramsIn(s.memberUniverseSlug, s.memberSlug ?? s.memberId)}
                          className="font-medium text-zinc-100 hover:text-violet-300">{s.memberName ?? 'Member'}</Link>
                        <span className="block text-xs text-zinc-400">
                          {s.facility ?? 'Facility unknown'}
                          {' · '}<FuzzyDate value={s.from} fallback="?" />
                          {' to '}{s.running ? (s.life ? 'life' : 'now') : <FuzzyDate value={s.to} fallback="?" />}
                          {s.counts > 1 && <span className="text-zinc-500"> · {s.counts} counts</span>}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </aside>
          </div>

          {editing && <CourtCaseFormSheet universeId={c.universe_id} open onClose={() => setEditing(false)} initial={c} />}
          {defendant && (
            <DefendantDialog caseId={c.id} universeId={c.universe_id} open onClose={() => setDefendant(null)}
              initial={defendant === 'new' ? undefined : defendant} />
          )}
          {linking && <LinkIncidentsDialog c={c} open onClose={() => setLinking(false)} />}
          {citing && (
            <AttachSourcesDialog
              universeId={c.universe_id}
              existingIds={c.sources.map((s) => s.id)}
              open
              onClose={() => setCiting(false)}
              onCreateNew={() => { setCiting(false); setCreatingSource(true) }}
              onAttach={(ids) => update.mutateAsync({ source_ids: ids })}
              attaching={update.isPending}
            />
          )}
          {creatingSource && <SourceFormSheet universeId={c.universe_id} open onClose={() => setCreatingSource(false)} />}
          <ConfirmDialog
            open={!!removing}
            onCancel={() => setRemoving(null)}
            destructive
            pending={deleteDefendant.isPending}
            title="Remove this defendant?"
            description={removing ? `${removing.member_name ?? removing.label ?? 'This defendant'} is taken off the case.` : ''}
            impact={removing?.disposition === 'ACQUITTED' ? 'Their acquittal stops applying to the incidents this case covers.' : undefined}
            confirmLabel="Remove"
            onConfirm={() => {
              if (!removing) return
              deleteDefendant.mutate(removing.id, { onSettled: () => setRemoving(null) })
            }}
          />
          <ConfirmDialog
            open={deleting}
            onCancel={() => setDeleting(false)}
            destructive
            pending={deleteCase.isPending}
            title={`Delete ${c.name}?`}
            description="The case, its defendants and its links go. Members, incidents and spells stay."
            impact={`${c.defendants.length} defendants, ${c.incidents.length} incident links, ${c.spells.length} spells unlinked`}
            confirmLabel="Delete case"
            onConfirm={handleDelete}
          />
        </>
      )}
    </div>
  )
}
