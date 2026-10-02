import { createLazyFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { AlertTriangle, ChevronRight, Map, MapPin, MapPinOff, Pencil, Plus, Search, Shield, ShieldAlert, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '@/components/EmptyState'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { TreeSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useDebounce } from '@/hooks/useDebounce'
import { useMunicipalities } from '@/lib/queries'
import type { MunicipalityListItem } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import { MunicipalityFormSheet, type MunicipalitiesSearch, type MunicipalitySortKey } from './_app.$universe.municipalities.index'

// The Municipalities list, in its own chunk; the route file keeps
// validateSearch and the form sheet, which the municipality page imports.
export const Route = createLazyFileRoute('/_app/$universe/municipalities/')({
  component: MunicipalitiesPage,
})

const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const plural = (n: number, word: string, many = `${word}s`) => `${n.toLocaleString()} ${n === 1 ? word : many}`

function compare(sort: MunicipalitySortKey) {
  const byName = (a: MunicipalityListItem, b: MunicipalityListItem) =>
    a.name.localeCompare(b.name, undefined, { sensitivity: 'base', numeric: true })
  return (a: MunicipalityListItem, b: MunicipalityListItem) => {
    if (sort === 'incidents') return b.total_incident_count - a.total_incident_count || byName(a, b)
    if (sort === 'sets') return b.set_count - a.set_count || byName(a, b)
    // Places with no figure (hamlets, neighborhoods) sort last, not as zero.
    if (sort === 'population') return (b.population ?? -1) - (a.population ?? -1) || byName(a, b)
    return byName(a, b)
  }
}

// ─── Row ──────────────────────────────────────────────────────────────────────

/**
 * One municipality. A city's incident count includes its districts', and its
 * bar is scaled against the busiest city, so the list reads as a ranking at a
 * glance; a district's bar is scaled against its city's total.
 */
function MuniRow({ m, depth, max, dim, orphan, expanded, onToggle, onEdit }: {
  m: MunicipalityListItem
  depth: 0 | 1
  max: number
  dim?: boolean
  orphan?: boolean
  expanded?: boolean
  onToggle?: () => void
  onEdit: () => void
}) {
  const incidents = m.total_incident_count
  const share = max > 0 ? Math.max(incidents > 0 ? 3 : 0, (incidents / max) * 100) : 0
  return (
    <div className={`group flex items-center gap-2 border-b border-zinc-800/60 px-3 py-2 transition-colors last:border-0 hover:bg-zinc-900/60 ${dim ? 'opacity-50' : ''} ${depth === 1 ? 'bg-zinc-950/40' : ''}`}>
      <span className={`flex w-6 shrink-0 justify-center ${depth === 1 ? 'ml-4 sm:ml-6' : ''}`}>
        {onToggle ? (
          <button type="button" onClick={onToggle} aria-expanded={expanded} aria-label={`${expanded ? 'Collapse' : 'Expand'} ${m.name}`}
            className="grid h-6 w-6 place-items-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50">
            <ChevronRight className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-90' : ''}`} />
          </button>
        ) : (
          <MapPin className={`h-3.5 w-3.5 ${depth === 1 ? 'text-zinc-600' : 'text-zinc-400'}`} aria-hidden />
        )}
      </span>

      <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id: m.id }} className="min-w-0 flex-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50">
        <span className="flex items-center gap-2">
          <span className={`truncate text-sm ${depth === 0 ? 'font-medium text-zinc-100' : 'text-zinc-300'} group-hover:text-violet-300`}>{m.name}</span>
          {m.kind === 'NEIGHBORHOOD' && (
            <span title="Neighborhood: a named area that may overlap districts" className="shrink-0 rounded-full border border-zinc-700 px-1.5 py-0.5 text-[10px] text-zinc-400">hood</span>
          )}
          {m.aliases.length > 0 && <span className="hidden min-w-0 truncate text-[11px] text-zinc-400 sm:inline">{m.aliases.join(' · ')}</span>}
          {m.region && <span className="hidden shrink-0 rounded-full bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-300 md:inline">{m.region}</span>}
          {m.child_count > 0 && <span className="hidden shrink-0 text-[11px] text-zinc-500 sm:inline">{plural(m.child_count, 'sub-area')}</span>}
          {m.population !== null && (
            <span title={`Population, ${m.population_year}`} className="hidden shrink-0 text-[11px] tabular-nums text-zinc-500 lg:inline">
              pop. {m.population.toLocaleString()}
            </span>
          )}
          {orphan && (
            <span title="Its parent municipality no longer exists" className="inline-flex shrink-0 items-center gap-1 rounded-full border border-amber-900/60 bg-amber-950/40 px-1.5 py-0.5 text-[10px] text-amber-400">
              <AlertTriangle className="h-3 w-3" aria-hidden />orphan
            </span>
          )}
          {!m.has_geometry && (
            <span title="No boundary: it cannot be drawn on the map" className="shrink-0 text-zinc-500"><MapPinOff className="h-3.5 w-3.5" aria-label="No boundary" /></span>
          )}
        </span>
        {/* Share of incidents, on its own line so it never crowds the name. */}
        <span className="mt-1 block h-1 w-full max-w-56 overflow-hidden rounded-full bg-zinc-800/60" aria-hidden>
          <span className={`block h-full rounded-full ${depth === 0 ? 'bg-amber-500/70' : 'bg-amber-600/50'}`} style={{ width: `${share}%` }} />
        </span>
      </Link>

      <span title={plural(m.set_count, 'set')} className={`inline-flex w-12 shrink-0 items-center justify-end gap-1 text-xs tabular-nums ${m.set_count ? 'text-zinc-300' : 'text-zinc-600'}`}>
        <Shield className="h-3 w-3 text-zinc-500" aria-hidden />{m.set_count}
      </span>
      <span title={depth === 0 && m.child_count > 0 ? `${plural(incidents, 'incident')}, ${m.incident_count} filed on the city itself` : plural(incidents, 'incident')}
        className={`inline-flex w-14 shrink-0 items-center justify-end gap-1 text-xs tabular-nums ${incidents ? 'text-amber-300' : 'text-zinc-600'}`}>
        <ShieldAlert className="h-3 w-3 text-zinc-500" aria-hidden />{incidents}
      </span>
      <button onClick={onEdit} aria-label={`Edit ${m.name}`}
        className="shrink-0 rounded-md p-1.5 text-zinc-400 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 group-hover:opacity-100 pointer-fine:opacity-0">
        <Pencil className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function MunicipalitiesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const search = Route.useSearch()
  const navigate = useNavigate({ from: '/$universe/municipalities/' })
  const sort: MunicipalitySortKey = search.sort ?? 'name'
  const noBoundary = !!search.noBoundary

  const [q, setQ] = useState(search.q ?? '')
  const debouncedQ = useDebounce(q.trim(), 250)
  useEffect(() => {
    if (debouncedQ === (search.q ?? '')) return
    navigate({ search: (prev) => ({ ...prev, q: debouncedQ || undefined }), replace: true })
    // On debouncedQ alone: also firing on search.q would push the stale
    // debounced text back over a Back navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ])
  const [urlQ, setUrlQ] = useState(search.q)
  if (search.q !== urlQ) {
    setUrlQ(search.q)
    if ((search.q ?? '') !== q.trim()) setQ(search.q ?? '')
  }

  const [creating, setCreating] = useState(false)
  const [editTarget, setEditTarget] = useState<MunicipalityListItem | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const { data, isLoading } = useMunicipalities(universe?.id ?? null)
  const items = useMemo(() => data?.items ?? [], [data])

  const tree = useMemo(() => {
    const byId = new Set(items.map((m) => m.id))
    const children: Record<string, MunicipalityListItem[]> = {}
    const top: MunicipalityListItem[] = []
    const orphans: MunicipalityListItem[] = []
    for (const m of items) {
      if (!m.parent_id) top.push(m)
      else if (byId.has(m.parent_id)) (children[m.parent_id] ??= []).push(m)
      else orphans.push(m)
    }
    const cmp = compare(sort)
    top.sort(cmp)
    orphans.sort(cmp)
    for (const k of Object.keys(children)) children[k].sort(cmp)
    return { top, children, orphans }
  }, [items, sort])

  // A row matches on its own name, aliases and region, and the boundary filter; a city stays in
  // view, dimmed, while any of its districts match, so the match keeps its context.
  const matches = useMemo(() => {
    const terms = fold(q.trim()).split(/\s+/).filter(Boolean)
    if (terms.length === 0 && !noBoundary) return null
    return new Set(items
      .filter((m) => {
        const hay = fold([m.name, ...m.aliases, m.region ?? ''].join(' '))
        return terms.every((t) => hay.includes(t)) && (!noBoundary || !m.has_geometry)
      })
      .map((m) => m.id))
  }, [items, q, noBoundary])

  if (!universe) return <NoUniverse />

  const stats = {
    cities: tree.top.length,
    districts: items.filter((m) => m.kind === 'DISTRICT').length,
    neighborhoods: items.filter((m) => m.kind === 'NEIGHBORHOOD').length,
    unbounded: items.filter((m) => !m.has_geometry).length,
  }
  const maxCity = Math.max(0, ...tree.top.map((m) => m.total_incident_count))

  const branchVisible = (city: MunicipalityListItem) =>
    !matches || matches.has(city.id) || (tree.children[city.id] ?? []).some((c) => matches.has(c.id))
  // Searching opens every city holding a matching district.
  const isExpanded = (city: MunicipalityListItem) =>
    expandedIds.has(city.id) || (!!matches && (tree.children[city.id] ?? []).some((c) => matches.has(c.id)))
  const parents = tree.top.filter((m) => (tree.children[m.id]?.length ?? 0) > 0)
  const allExpanded = parents.length > 0 && parents.every((p) => expandedIds.has(p.id))
  const visibleTop = tree.top.filter(branchVisible)
  const visibleOrphans = tree.orphans.filter((m) => !matches || matches.has(m.id))

  function patch(next: Partial<MunicipalitiesSearch>) {
    navigate({ search: (prev) => {
      const merged: MunicipalitiesSearch = { ...prev, ...next }
      for (const k of Object.keys(merged) as (keyof MunicipalitiesSearch)[]) if (merged[k] === undefined) delete merged[k]
      return merged
    }, replace: true })
  }

  function toggle(id: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const editItem = editTarget ? (items.find((m) => m.id === editTarget.id) ?? editTarget) : null

  return (
    <div className="space-y-4 pb-8">
      <PageHeader
        title="Municipalities"
        description={isLoading ? 'Loading…' : items.length === 0 ? 'None yet'
          : [plural(stats.cities, 'city', 'cities'), plural(stats.districts, 'district'),
            ...(stats.neighborhoods ? [plural(stats.neighborhoods, 'neighborhood')] : [])].join(' · ')}
        action={
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" asChild>
              <Link from="/$universe" to="/$universe/municipalities/map" search={{ focus: undefined }}><Map className="mr-1.5 h-4 w-4" />Map</Link>
            </Button>
            <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add</Button>
          </div>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search cities and districts…" aria-label="Search municipalities"
            onKeyDown={(e) => { if (e.key === 'Escape' && q) { e.stopPropagation(); setQ('') } }}
            className="h-9 pl-8 pr-8 text-sm" />
          {q && (
            <button type="button" onClick={() => setQ('')} aria-label="Clear search"
              className="absolute right-1.5 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-white">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <Select value={sort} onValueChange={(v) => patch({ sort: v === 'name' ? undefined : v as MunicipalitySortKey })}>
          <SelectTrigger className="h-9 w-auto min-w-36 text-xs" aria-label="Sort"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="name">Name A→Z</SelectItem>
            <SelectItem value="incidents">Most incidents</SelectItem>
            <SelectItem value="sets">Most sets</SelectItem>
            <SelectItem value="population">Largest population</SelectItem>
          </SelectContent>
        </Select>
        {(stats.unbounded > 0 || noBoundary) && (
          <button onClick={() => patch({ noBoundary: noBoundary ? undefined : true })} aria-pressed={noBoundary}
            title="Municipalities with no boundary cannot be drawn on the map"
            className={`inline-flex h-9 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium transition-colors ${
              noBoundary ? 'border-violet-700/60 bg-violet-950/30 text-violet-200' : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-200'
            }`}>
            <MapPinOff className="h-3.5 w-3.5" aria-hidden />No boundary <span className="tabular-nums opacity-70">{stats.unbounded}</span>
          </button>
        )}
        {parents.length > 0 && !matches && (
          <Button variant="outline" size="sm" className="ml-auto h-9"
            onClick={() => setExpandedIds(allExpanded ? new Set() : new Set(parents.map((p) => p.id)))}>
            {allExpanded ? 'Collapse all' : 'Expand all'}
          </Button>
        )}
      </div>

      {isLoading ? (
        <TreeSkeleton rows={8} />
      ) : items.length === 0 ? (
        <EmptyState icon={MapPin} title="No municipalities yet" description="Add cities and districts to place incidents and sets."
          action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add the first one</Button>} />
      ) : visibleTop.length === 0 && visibleOrphans.length === 0 ? (
        <EmptyState icon={Search} title="No municipalities match"
          action={<Button size="sm" variant="outline" onClick={() => { setQ(''); navigate({ search: (p) => ({ sort: p.sort }), replace: true }) }}>Clear search and filters</Button>} />
      ) : (
        <div className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
          <div className="flex items-center gap-2 border-b border-zinc-800 bg-zinc-900/80 px-3 py-2 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            <span className="w-6" />
            <span className="flex-1">Municipality</span>
            <span className="w-12 text-right">Sets</span>
            <span className="w-14 text-right">Incidents</span>
            <span className="w-7" />
          </div>
          {visibleTop.map((city) => {
            const kids = tree.children[city.id] ?? []
            const open = kids.length > 0 && isExpanded(city)
            return (
              <div key={city.id}>
                <MuniRow m={city} depth={0} max={maxCity}
                  dim={!!matches && !matches.has(city.id)}
                  expanded={open}
                  onToggle={kids.length > 0 ? () => toggle(city.id) : undefined}
                  onEdit={() => setEditTarget(city)} />
                {/* While searching, only the matching districts: dimming the rest
                    buried a ZIP among Detroit's 34. A matching city shows them all. */}
                {open && kids.filter((c) => !matches || matches.has(city.id) || matches.has(c.id)).map((c) => (
                  <MuniRow key={c.id} m={c} depth={1} max={city.total_incident_count}
                    dim={!!matches && !matches.has(c.id)}
                    onEdit={() => setEditTarget(c)} />
                ))}
              </div>
            )
          })}
          {visibleOrphans.map((m) => (
            <MuniRow key={m.id} m={m} depth={0} max={maxCity} orphan onEdit={() => setEditTarget(m)} />
          ))}
        </div>
      )}

      <MunicipalityFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} allMunicipalities={items} />
      {editItem && (
        <MunicipalityFormSheet key={editItem.id} universeId={universe.id} open onClose={() => setEditTarget(null)}
          initial={editItem} allMunicipalities={items} />
      )}
    </div>
  )
}
