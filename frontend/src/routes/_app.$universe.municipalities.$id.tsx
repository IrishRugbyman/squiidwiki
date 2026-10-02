import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { AlertTriangle, ChevronRight, CheckCircle2, ExternalLink, Map, MapPin, Pencil, Plus, Shield, Trash2 } from 'lucide-react'
import { lazy, Suspense, useState } from 'react'
import type { MapMetric } from '@/components/maps/MunicipalityMap'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { LinkifiedText } from '@/components/LinkifiedText'
import { ReliabilityBadge, SetStatusBadge } from '@/components/StatusBadge'
import { PanelHeading } from '@/components/detail/DetailParts'
import { AttachSourcesDialog } from '@/components/AttachSourcesDialog'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  useMunicipality, useMunicipalities, useDeleteMunicipality, useUpdateMunicipality,
  useIncidentsByMunicipality, useMunicipalityGeoJSON, useAllSets,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { MunicipalityFormSheet } from './_app.$universe.municipalities.index'
import { SetFormSheet } from './_app.$universe.sets.index'
import { IncidentFormSheet } from './_app.$universe.incidents.index'
import { SourceFormSheet } from './_app.$universe.sources.index'
import { INCIDENT_TYPE_LABEL, INCIDENT_TYPE_TEXT } from '@/lib/incidentColors'
import type { MunicipalityKind, MunicipalityListItem } from '@/lib/types'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'

const MunicipalityMap = lazy(() => import('@/components/maps/MunicipalityMap'))
const PhotoGallery = lazy(() => import('@/components/media/PhotoGallery').then((m) => ({ default: m.PhotoGallery })))

type ChildKind = Exclude<MunicipalityKind, 'CITY'>
const pct = (x: number) => `${Math.round(x * 100)}%`

const CHILD_KIND_LABEL: Record<ChildKind, { one: string; many: string; of: string }> = {
  DISTRICT: { one: 'District', many: 'Districts', of: 'District of' },
  NEIGHBORHOOD: { one: 'Neighborhood', many: 'Neighborhoods', of: 'Neighborhood in' },
}

export const Route = createFileRoute('/_app/$universe/municipalities/$id')({
  component: MunicipalityDetailPage,
})

function MunicipalityDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const { data: municipality, isLoading, isError, refetch } = useMunicipality(id, universe?.id ?? null)
  const { data: allMunicipalities } = useMunicipalities(universe?.id ?? null)
  const { data: incidentData, isLoading: incidentsLoading } = useIncidentsByMunicipality(id, universe?.id ?? null)
  const deleteMunicipality = useDeleteMunicipality(universe?.id ?? '')
  const updateMunicipality = useUpdateMunicipality(municipality?.id ?? '', universe?.id ?? '')
  const { data: allSets } = useAllSets(universe?.id ?? null)

  useRecordRecent(municipality ? { type: 'municipality', id: municipality.id, slug: null, label: municipality.name } : null)

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEditShortcut(() => municipality && setEditing(true))

  const allItems = allMunicipalities?.items ?? []
  const parent = municipality?.parent_id
    ? allItems.find((m) => m.id === municipality.parent_id)
    : null
  const children = allItems.filter((m) => m.parent_id === id)
  const childrenByKind: Record<ChildKind, MunicipalityListItem[]> = {
    DISTRICT: children.filter((c) => c.kind === 'DISTRICT'),
    NEIGHBORHOOD: children.filter((c) => c.kind === 'NEIGHBORHOOD'),
  }
  const mappableKinds = (['DISTRICT', 'NEIGHBORHOOD'] as ChildKind[]).filter((k) =>
    childrenByKind[k].some((c) => c.has_geometry),
  )
  const incidents = incidentData?.items ?? []
  // Sets anchored here (a city) or claiming it as territory (a district or neighborhood).
  const sets = (allSets?.items ?? [])
    .filter((st) => !st.is_reserved && (st.municipality_id === id || st.territory_ids.includes(id)))
    .sort((a, b) => a.name.localeCompare(b.name))

  // Districts partition the city and neighborhoods overlap them, so the map
  // draws one kind at a time. Only fetched when there are mappable children.
  const [mapKindChoice, setMapKind] = useState<ChildKind | null>(null)
  const mapKind = mapKindChoice && mappableKinds.includes(mapKindChoice) ? mapKindChoice : mappableKinds[0]
  const { data: childrenGeoJSON } = useMunicipalityGeoJSON(
    mapKind ? universe?.id ?? null : null,
    mapKind ? id : undefined,
    mapKind,
  )

  const [addingSource, setAddingSource] = useState(false)
  const [creatingSource, setCreatingSource] = useState(false)
  const [districtMetric, setDistrictMetric] = useState<MapMetric>('incidents')
  const [creatingChild, setCreatingChild] = useState(false)
  const [creatingSet, setCreatingSet] = useState(false)
  const [creatingIncident, setCreatingIncident] = useState(false)

  async function handleDelete() {
    if (!municipality) return
    try {
      await deleteMunicipality.mutateAsync(municipality.id)
      navigate({ from: '/$universe', to: '/$universe/municipalities' })
    } catch {
      setDeleting(false)
    }
  }

  if (isError) return <ErrorState title="Municipality not found" onRetry={() => refetch()} />

  const breadcrumbItems = [
    { label: 'Municipalities', to: '/$universe/municipalities' },
    ...(parent ? [{ label: parent.name, to: `/$universe/municipalities/${parent.id}` }] : []),
    { label: municipality?.name ?? 'Municipality' },
  ]

  return (
    <div className="space-y-6">
      <Breadcrumbs items={breadcrumbItems} />

      {/* Header */}
      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : municipality ? (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-zinc-800/80 p-3">
              <MapPin className="h-6 w-6 text-zinc-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-2xl font-bold text-white">{municipality.name}</h1>
                <CopyButton value={window.location.href} label="Copy link to this municipality" className="opacity-60 hover:opacity-100" />
              </div>
              {municipality.aliases.length > 0 && (
                <p className="mt-0.5 text-sm text-zinc-300">
                  <span className="text-zinc-400">aka </span>{municipality.aliases.join(' · ')}
                </p>
              )}
              {(parent || municipality.region) && (
                <p className="mt-0.5 flex flex-wrap items-center gap-2 text-sm text-zinc-400">
                  {parent && municipality.kind !== 'CITY' && (
                    <span>
                      {CHILD_KIND_LABEL[municipality.kind].of}{' '}
                      <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: parent.id }} className="text-zinc-400 hover:text-white transition-colors">
                        {parent.name}
                      </Link>
                    </span>
                  )}
                  {municipality.kind === 'NEIGHBORHOOD' && municipality.overlaps.length > 0 && (
                    <span>
                      · in{' '}
                      {municipality.overlaps.map((o, i) => (
                        <span key={o.id}>
                          {i > 0 && (i === municipality.overlaps.length - 1 ? ' and ' : ', ')}
                          <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: o.id }} className="text-zinc-300 hover:text-white transition-colors">{o.name}</Link>
                          {municipality.overlaps.length > 1 && <span className="text-zinc-500"> ({pct(o.share_of_neighborhood)})</span>}
                        </span>
                      ))}
                    </span>
                  )}
                  {municipality.region && (
                    <Link from="/$universe" to="/$universe/municipalities" search={{ q: municipality.region }}
                      title={`Every place in ${municipality.region}`}
                      className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300 transition-colors hover:bg-zinc-700 hover:text-white">
                      {municipality.region}
                    </Link>
                  )}
                </p>
              )}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {municipality.has_geometry && (
              <Link from="/$universe" to="/$universe/municipalities/map" search={{ focus: municipality.id }}>
                <Button size="sm" variant="outline">
                  <Map className="mr-1.5 h-3.5 w-3.5" />View on map
                </Button>
              </Link>
            )}
            {municipality.kind === 'CITY' && <Button size="sm" variant="outline" onClick={() => setCreatingChild(true)}>
              <Plus className="mr-1.5 h-3.5 w-3.5" />Add sub-area
            </Button>}
            <Button size="sm" variant="outline" onClick={() => setCreatingSet(true)}>
              <Plus className="mr-1.5 h-3.5 w-3.5" />Create Set
            </Button>
            <Button size="sm" variant="outline" onClick={() => setCreatingIncident(true)}>
              <Plus className="mr-1.5 h-3.5 w-3.5" />Create Incident
            </Button>
            <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
              <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
            </Button>
            {user?.global_role === 'ADMIN' && (
              <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
              </Button>
            )}
          </div>
        </div>
      ) : null}

      {/* Stats row */}
      {municipality && (
        <div className={`grid grid-cols-2 gap-3 ${children.length > 0 ? 'sm:grid-cols-4' : 'sm:grid-cols-3'}`}>
          {municipality.population !== null && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 text-center"
              title={municipality.population_source ?? undefined}>
              <div className="text-2xl font-bold tabular-nums text-white">{municipality.population.toLocaleString()}</div>
              <div className="mt-0.5 text-xs text-zinc-400">Population ({municipality.population_year})</div>
              {municipality.population_source && (
                <div className="mt-0.5 truncate text-[10px] text-zinc-500">{municipality.population_source}</div>
              )}
            </div>
          )}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 text-center">
            <div className="text-2xl font-bold tabular-nums text-white">{incidents.length}</div>
            <div className="mt-0.5 text-xs text-zinc-400">Incidents</div>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 text-center">
            <div className="text-2xl font-bold tabular-nums text-white">{sets.length}</div>
            <div className="mt-0.5 text-xs text-zinc-400">Sets</div>
          </div>
          {children.length > 0 && (
            <div className={`rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 text-center ${municipality.population === null ? 'col-span-2 sm:col-span-1' : ''}`}>
              <div className="text-2xl font-bold tabular-nums text-white">{children.length}</div>
              <div className="mt-0.5 text-xs text-zinc-400">
                {(['DISTRICT', 'NEIGHBORHOOD'] as ChildKind[])
                  .filter((k) => childrenByKind[k].length > 0)
                  .map((k) => CHILD_KIND_LABEL[k].many).join(' & ')}
              </div>
            </div>
          )}
        </div>
      )}

      {municipality && universe && (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0 space-y-6">
            <section>
              <PanelHeading action={
                <button type="button" onClick={() => setEditing(true)} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
                  <Pencil className="h-3 w-3" />{municipality.description ? 'Edit' : 'Add'}
                </button>
              }>About</PanelHeading>
              {municipality.description ? (
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300"><LinkifiedText text={municipality.description} /></p>
              ) : (
                <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">Nothing written about {municipality.name} yet.</p>
              )}
            </section>

            <section>
              <PanelHeading>Photos</PanelHeading>
              <Suspense fallback={<Skeleton className="h-32 w-full" />}>
                <PhotoGallery entityType="municipality" entityId={municipality.id} universeId={universe.id} />
              </Suspense>
            </section>
          </div>

          <aside className="min-w-0 space-y-6">
            {municipality.kind === 'DISTRICT' && municipality.overlaps.length > 0 && (
              <section>
                <PanelHeading>Neighborhoods ({municipality.overlaps.length})</PanelHeading>
                <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                  {municipality.overlaps.map((o) => (
                    <li key={o.id}>
                      <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: o.id }} className="group flex items-center gap-2.5 px-3 py-2 transition-colors hover:bg-zinc-800/40">
                        <MapPin className="h-3.5 w-3.5 shrink-0 text-zinc-400" aria-hidden />
                        <span className="min-w-0 flex-1 truncate text-sm text-zinc-200 group-hover:text-violet-300">{o.name}</span>
                        <span className="shrink-0 text-[11px] tabular-nums text-zinc-400"
                          title={`Covers ${pct(o.share_of_district)} of ${municipality.name}; ${pct(o.share_of_neighborhood)} of ${o.name} lies here`}>
                          {pct(o.share_of_district)} of {municipality.name}
                          {o.share_of_neighborhood < 0.95 && ` · ${pct(o.share_of_neighborhood)} of it`}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            <section>
              <PanelHeading>Sets{sets.length > 0 ? ` (${sets.length})` : ''}</PanelHeading>
              {sets.length === 0 ? (
                <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No sets on file here.</p>
              ) : (
                <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                  {sets.map((st) => (
                    <li key={st.id}>
                      <Link from="/$universe" to="/$universe/sets/$id" params={{ id: st.slug ?? st.id }} className="group flex items-center gap-2.5 px-3 py-2 transition-colors hover:bg-zinc-800/40">
                        <Shield className="h-3.5 w-3.5 shrink-0" style={{ color: st.gang_color ?? undefined }} aria-hidden />
                        <span className="min-w-0 flex-1 truncate text-sm text-zinc-200 group-hover:text-violet-300">{st.name}</span>
                        {st.status !== 'ACTIVE' && <SetStatusBadge status={st.status} />}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <PanelHeading action={
                <button type="button" onClick={() => setAddingSource(true)} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
                  <Plus className="h-3 w-3" />Cite
                </button>
              }>Sources{municipality.sources.length > 0 ? ` (${municipality.sources.length})` : ''}</PanelHeading>
              {municipality.sources.length === 0 ? (
                <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No sources cited.</p>
              ) : (
                <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
                  {municipality.sources.map((src) => (
                    <li key={src.id} className="flex items-center gap-3 px-3 py-2.5">
                      <Link from="/$universe" to="/$universe/sources/$id" params={{ id: src.id }} className="group min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-white transition-colors group-hover:text-violet-300">{src.title}</span>
                        {src.publication && <span className="block truncate text-[11px] text-zinc-500">{src.publication}</span>}
                      </Link>
                      <ReliabilityBadge reliability={src.reliability} />
                      <a href={src.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${src.title} in a new tab`}
                        className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-300">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </aside>
        </div>
      )}

      {/* Sub-districts map — only when at least one child has geometry */}
      {childrenGeoJSON && childrenGeoJSON.features.length > 0 && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 overflow-hidden">
          <div className="border-b border-zinc-800 px-4 py-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                {mapKind ? CHILD_KIND_LABEL[mapKind].many : 'Districts'} map
              </h2>
              {mappableKinds.length > 1 && (
                <div className="inline-flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-0.5" role="tablist" aria-label="Layer">
                  {mappableKinds.map((k) => (
                    <button
                      key={k}
                      role="tab"
                      aria-selected={mapKind === k}
                      onClick={() => setMapKind(k)}
                      className={`rounded-md px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
                        mapKind === k ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'
                      }`}
                    >
                      {CHILD_KIND_LABEL[k].many}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <div className="inline-flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-0.5" role="tablist">
                {(['incidents', 'sets'] as MapMetric[]).map((key) => (
                  <button
                    key={key}
                    role="tab"
                    aria-selected={districtMetric === key}
                    onClick={() => setDistrictMetric(key)}
                    className={`rounded-md px-2.5 py-0.5 text-[11px] font-medium capitalize transition-colors ${
                      districtMetric === key ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-zinc-300'
                    }`}
                  >
                    {key}
                  </button>
                ))}
              </div>
              <span className="text-[11px] text-zinc-400">
                {childrenGeoJSON.features.length} of {mapKind ? childrenByKind[mapKind].length : children.length} mapped · click to zoom
              </span>
            </div>
          </div>
          <div className="h-[420px] relative">
            <Suspense fallback={
              <div className="flex h-full items-center justify-center bg-zinc-900">
                <div className="flex flex-col items-center gap-2 text-zinc-400">
                  <MapPin className="h-8 w-8 animate-pulse" />
                  <span className="text-sm">Loading map…</span>
                </div>
              </div>
            }>
              <MunicipalityMap geojson={childrenGeoJSON} metric={districtMetric} />
            </Suspense>
          </div>
        </div>
      )}

      {/* Sub-areas, one panel per kind */}
      {(['DISTRICT', 'NEIGHBORHOOD'] as ChildKind[]).filter((k) => childrenByKind[k].length > 0).map((k) => (
        <div key={k} className="rounded-lg border border-zinc-800 bg-zinc-900/30">
          <div className="border-b border-zinc-800 px-4 py-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">{CHILD_KIND_LABEL[k].many} ({childrenByKind[k].length})</h2>
          </div>
          <div className="grid grid-cols-1 gap-1 p-2 sm:grid-cols-2 lg:grid-cols-3">
            {childrenByKind[k].map((child) => (
              <Link
                key={child.id}
                from="/$universe" to="/$universe/municipalities/$id"
                params={{ id: child.id }}
                className="group flex items-center gap-2 rounded-md border border-transparent px-3 py-2 transition-colors hover:border-zinc-700 hover:bg-zinc-800/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
              >
                <MapPin className="h-3.5 w-3.5 shrink-0 text-zinc-400 group-hover:text-zinc-200" />
                <span className="min-w-0 flex-1 truncate text-sm text-zinc-300 group-hover:text-white">
                  {child.name}
                  {child.aliases.length > 0 && <span className="ml-1.5 text-xs text-zinc-500">{child.aliases[0]}</span>}
                </span>
                <span className={`text-xs tabular-nums ${child.incident_count > 0 ? 'text-amber-400' : 'text-zinc-400'}`}>
                  {child.incident_count}
                </span>
                <ChevronRight className="h-3.5 w-3.5 text-zinc-500 group-hover:text-zinc-400" />
              </Link>
            ))}
          </div>
        </div>
      ))}

      {/* Incidents */}
      <TooltipProvider delayDuration={250}>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/30">
          <div className="border-b border-zinc-800 px-4 py-3 flex items-center justify-between gap-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Incidents</h2>
            <div className="flex items-center gap-3">
              <Link
                from="/$universe" to="/$universe/incidents"
                search={{ municipality_id: id }}
                className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
              >
                Filter incidents here →
              </Link>
              <Link from="/$universe" to="/$universe/incidents" className="text-xs text-zinc-400 hover:text-violet-400 transition-colors">
                All incidents →
              </Link>
            </div>
          </div>
          <div className="divide-y divide-zinc-800/60">
            {incidentsLoading ? (
              <div className="space-y-1 p-4">
                {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-10 w-full animate-pulse rounded-md bg-zinc-800" />)}
              </div>
            ) : incidents.length === 0 ? (
              <p className="px-4 py-6 text-sm text-zinc-400">No incidents recorded in {municipality?.name}.</p>
            ) : (
              incidents.map((inc) => (
                <Link
                  key={inc.id}
                  from="/$universe" to="/$universe/incidents/$id"
                  params={{ id: inc.id }}
                  className="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-zinc-800/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
                >
                  <AlertTriangle className={`h-3.5 w-3.5 shrink-0 ${INCIDENT_TYPE_TEXT[inc.type]}`} />
                  <span className="text-sm font-medium text-zinc-300 group-hover:text-white">{INCIDENT_TYPE_LABEL[inc.type]}</span>
                  {inc.victim_names.length > 0 && (
                    <span className="text-sm text-zinc-400">victims: {inc.victim_names.slice(0, 2).join(', ')}{inc.victim_names.length > 2 ? ` +${inc.victim_names.length - 2}` : ''}</span>
                  )}
                  <span className="ml-auto text-xs text-zinc-400">
                    {inc.date ? <FuzzyDate value={inc.date} /> : 'Unknown date'}
                  </span>
                  {inc.verified && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
                      </TooltipTrigger>
                      <TooltipContent>Verified incident</TooltipContent>
                    </Tooltip>
                  )}
                </Link>
              ))
            )}
          </div>
        </div>
      </TooltipProvider>

      {/* Sheets / dialogs */}
      {universe && municipality && (
        <MunicipalityFormSheet
          universeId={universe.id}
          open={editing}
          onClose={() => setEditing(false)}
          initial={municipality}
          allMunicipalities={allItems as MunicipalityListItem[]}
        />
      )}

      {universe && (
        <MunicipalityFormSheet
          universeId={universe.id}
          open={creatingChild}
          onClose={() => setCreatingChild(false)}
          defaultParentId={id}
          allMunicipalities={allItems as MunicipalityListItem[]}
        />
      )}

      {universe && municipality && addingSource && (
        <AttachSourcesDialog
          universeId={universe.id}
          existingIds={municipality.sources.map((src) => src.id)}
          open
          onClose={() => setAddingSource(false)}
          onCreateNew={() => { setAddingSource(false); setCreatingSource(true) }}
          onAttach={(source_ids) => updateMunicipality.mutateAsync({ source_ids })}
          attaching={updateMunicipality.isPending}
        />
      )}
      {universe && creatingSource && <SourceFormSheet universeId={universe.id} open onClose={() => setCreatingSource(false)} />}

      {universe && (
        <SetFormSheet
          universeId={universe.id}
          open={creatingSet}
          onClose={() => setCreatingSet(false)}
          defaultMunicipalityId={id}
        />
      )}

      {universe && (
        <IncidentFormSheet
          universeId={universe.id}
          open={creatingIncident}
          onClose={() => setCreatingIncident(false)}
          defaultMunicipalityId={id}
        />
      )}

      <ConfirmDialog
        open={deleting}
        title="Delete Municipality"
        description={`Permanently delete "${municipality?.name}"? This cannot be undone.`}
        impact={(() => {
          const parts: string[] = []
          if (children.length) parts.push(`${children.length} sub-area${children.length === 1 ? '' : 's'} will be orphaned`)
          if (incidents.length) parts.push(`${incidents.length} incident${incidents.length === 1 ? '' : 's'} will lose this location`)
          if (!parts.length) return null
          return <span>{parts.join('. ')}.</span>
        })()}
        confirmLabel="Delete"
        destructive
        pending={deleteMunicipality.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleting(false)}
      />
    </div>
  )
}
