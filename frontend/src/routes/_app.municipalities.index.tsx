import { createFileRoute, Link } from '@tanstack/react-router'
import { AlertTriangle, ChevronRight, Map, MapPin, Pencil, Plus, Search, X } from 'lucide-react'
import { useState, useMemo } from 'react'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { EmptyState } from '@/components/EmptyState'
import { TreeSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useCreateMunicipality, useUpdateMunicipality, useMunicipalities } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import type { MunicipalityListItem, MunicipalityRead } from '@/lib/types'

export const Route = createFileRoute('/_app/municipalities/')({
  component: MunicipalitiesPage,
})

// ─── Form sheet (also exported for detail page) ───────────────────────────────

interface MunicipalityFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: MunicipalityRead
  /** When creating a new municipality, preselect this parent in the form. */
  defaultParentId?: string
  allMunicipalities?: MunicipalityListItem[]
}

export function MunicipalityFormSheet({ universeId, open, onClose, initial, defaultParentId, allMunicipalities }: MunicipalityFormProps) {
  const create = useCreateMunicipality()
  const update = useUpdateMunicipality(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const [name, setName] = useState(initial?.name ?? '')
  const [parentId, setParentId] = useState<string>(initial?.parent_id ?? defaultParentId ?? '')
  const [geometryText, setGeometryText] = useState<string>(
    initial?.geometry ? JSON.stringify(initial.geometry, null, 2) : ''
  )
  const [error, setError] = useState<string | null>(null)

  function parseGeometry(text: string): object | null | 'error' {
    if (!text.trim()) return null
    try {
      const parsed = JSON.parse(text)
      let geom = parsed
      if (parsed?.type === 'FeatureCollection') geom = parsed.features?.[0]?.geometry
      else if (parsed?.type === 'Feature') geom = parsed.geometry
      if (!['Polygon', 'MultiPolygon'].includes(geom?.type)) return 'error'
      return geom
    } catch {
      return 'error'
    }
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const geometry = parseGeometry(geometryText)
    if (geometry === 'error') {
      setError('Invalid GeoJSON — paste a Polygon/MultiPolygon geometry, a Feature, or a FeatureCollection whose first feature is a (Multi)Polygon')
      return
    }
    const body = { universe_id: universeId, name, parent_id: parentId || null, geometry }
    try {
      if (isEdit) {
        await update.mutateAsync(body)
        toast.success(`Updated "${name}"`)
      } else {
        await create.mutateAsync(body)
        toast.success(`Added "${name}"`)
        setName(''); setParentId(''); setGeometryText('')
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} municipality`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending
  const options = allMunicipalities?.filter((m) => m.id !== initial?.id) ?? []

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Municipality' : 'Add Municipality'}
        description={isEdit ? 'Update this municipality' : 'Add a city or district'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="m-name">Name *</Label>
            <Input id="m-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Detroit" />
          </div>
          {options.length > 0 && (
            <div className="space-y-1.5">
              <Label>Parent municipality</Label>
              <Select value={parentId || 'none'} onValueChange={(v) => setParentId(v === 'none' ? '' : v)}>
                <SelectTrigger><SelectValue placeholder="None (top-level)" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">— None —</SelectItem>
                  {options.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="m-geometry">
              Boundary GeoJSON <span className="text-zinc-500 font-normal">(for map)</span>
            </Label>
            <textarea
              id="m-geometry"
              value={geometryText}
              onChange={(e) => setGeometryText(e.target.value)}
              placeholder={'Paste a GeoJSON Polygon or MultiPolygon geometry here.\n{"type":"Polygon","coordinates":[[[lng,lat],...]]}'}
              rows={6}
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-300 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500/40 resize-y"
            />
            <p className="text-[11px] text-zinc-500">
              Accepts a <code className="text-zinc-400">Polygon</code>, <code className="text-zinc-400">MultiPolygon</code>, or a full GeoJSON <code className="text-zinc-400">Feature</code>. Get boundaries from{' '}
              <a href="https://osm-boundaries.com" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:underline">osm-boundaries.com</a> or{' '}
              <a href="https://overpass-turbo.eu" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:underline">Overpass Turbo</a>.
            </p>
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}

// ─── Row ──────────────────────────────────────────────────────────────────────

function MuniRow({
  m,
  indent = false,
  dim = false,
  orphan = false,
  expanded,
  onToggleExpand,
  onEdit,
}: {
  m: MunicipalityListItem
  indent?: boolean
  dim?: boolean
  orphan?: boolean
  expanded?: boolean
  onToggleExpand?: () => void
  onEdit: (m: MunicipalityListItem) => void
}) {
  const canExpand = m.child_count > 0 && !!onToggleExpand
  return (
    <div className={`group relative flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 transition-colors hover:border-zinc-700 hover:bg-zinc-900/60 ${dim ? 'opacity-60' : ''}`}>
      {indent && (
        <div className="absolute left-0 top-0 bottom-0 w-px ml-6 bg-zinc-800" />
      )}
      {indent && <div className="w-4 shrink-0" />}
      {canExpand ? (
        <button
          type="button"
          onClick={onToggleExpand}
          aria-expanded={expanded}
          aria-label={expanded ? `Collapse ${m.name}` : `Expand ${m.name}`}
          className="-ml-1 grid h-5 w-5 shrink-0 place-items-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
        >
          <ChevronRight className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-90' : ''}`} />
        </button>
      ) : (
        <MapPin className={`h-4 w-4 shrink-0 ${indent ? 'text-zinc-600' : 'text-zinc-500'}`} />
      )}
      <Link
        to="/municipalities/$id"
        params={{ id: m.id }}
        className="min-w-0 flex-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 rounded"
      >
        <span className={`text-sm ${indent ? 'text-zinc-300' : 'font-medium text-zinc-100'}`}>
          {m.name}
        </span>
      </Link>
      <div className="flex shrink-0 items-center gap-2">
        {orphan && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex items-center gap-1 rounded-full border border-amber-900/60 bg-amber-950/40 px-2 py-0.5 text-[11px] text-amber-400">
                <AlertTriangle className="h-3 w-3" /> orphan
              </span>
            </TooltipTrigger>
            <TooltipContent>This municipality's parent no longer exists.</TooltipContent>
          </Tooltip>
        )}
        {m.child_count > 0 && (
          canExpand ? (
            <button
              type="button"
              onClick={onToggleExpand}
              className="rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[11px] text-zinc-400 hover:border-zinc-600 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50"
            >
              {m.child_count} {m.child_count === 1 ? 'district' : 'districts'}
            </button>
          ) : (
            <span className="rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[11px] text-zinc-500">
              {m.child_count} {m.child_count === 1 ? 'district' : 'districts'}
            </span>
          )
        )}
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              className={`rounded-full px-2 py-0.5 text-[11px] font-medium tabular-nums ${
                m.incident_count > 0
                  ? 'bg-amber-500/10 text-amber-400'
                  : 'bg-zinc-800/60 text-zinc-600'
              }`}
            >
              {m.incident_count} {m.incident_count === 1 ? 'incident' : 'incidents'}
            </span>
          </TooltipTrigger>
          <TooltipContent>
            {m.incident_count > 0 ? 'Amber highlight = has recorded incidents' : 'No incidents recorded'}
          </TooltipContent>
        </Tooltip>
        <button
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); onEdit(m) }}
          aria-label={`Edit ${m.name}`}
          className="rounded-md p-1.5 text-zinc-600 transition-colors hover:bg-zinc-700 hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function MunicipalitiesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [creating, setCreating] = useState(false)
  const [editTarget, setEditTarget] = useState<MunicipalityListItem | null>(null)
  const [q, setQ] = useState('')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const { data, isLoading } = useMunicipalities(universe?.id ?? null)

  const items = data?.items ?? []

  function toggleExpand(id: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // Match any name containing the query; when searching, we keep the tree
  // structure but dim non-matching ancestors so context is preserved.
  const matchIds = useMemo(() => {
    if (!q.trim()) return null
    const lower = q.toLowerCase()
    return new Set(
      items.filter((m) => m.name.toLowerCase().includes(lower)).map((m) => m.id),
    )
  }, [items, q])

  if (!universe) return <NoUniverse />

  // Build tree: top-level items, each with their children
  const topLevel = items.filter((m) => !m.parent_id)
  const childMap: Record<string, MunicipalityListItem[]> = {}
  for (const m of items) {
    if (m.parent_id) {
      if (!childMap[m.parent_id]) childMap[m.parent_id] = []
      childMap[m.parent_id].push(m)
    }
  }

  const orphanIds = new Set(
    items.filter((m) => m.parent_id && !items.find((p) => p.id === m.parent_id)).map((m) => m.id),
  )

  // A parent is "relevant" when it or any child matches the query
  function branchMatches(parent: MunicipalityListItem): boolean {
    if (!matchIds) return true
    if (matchIds.has(parent.id)) return true
    return (childMap[parent.id] ?? []).some((c) => matchIds.has(c.id))
  }

  // While searching, force-expand any branch that has a matching child so
  // the user can see the matches without an extra click.
  const forcedExpanded = useMemo(() => {
    if (!matchIds) return null
    const ids = new Set<string>()
    for (const parent of items) {
      if (parent.parent_id) continue
      const children = childMap[parent.id] ?? []
      if (children.some((c) => matchIds.has(c.id))) ids.add(parent.id)
    }
    return ids
  }, [matchIds, items, childMap])

  const isExpanded = (id: string) =>
    forcedExpanded ? forcedExpanded.has(id) || expandedIds.has(id) : expandedIds.has(id)

  const parentsWithChildren = topLevel.filter((p) => (childMap[p.id]?.length ?? 0) > 0)
  const allExpanded = parentsWithChildren.length > 0 && parentsWithChildren.every((p) => expandedIds.has(p.id))
  function expandAll() {
    setExpandedIds(new Set(parentsWithChildren.map((p) => p.id)))
  }
  function collapseAll() {
    setExpandedIds(new Set())
  }

  const editItem = editTarget
    ? (items.find((m) => m.id === editTarget.id) ?? editTarget)
    : null

  return (
    <div className="space-y-4">
      <PageHeader
        title="Municipalities"
        description={`${data?.total ?? 0} total`}
        action={
          <div className="flex items-center gap-2">
            <Link to="/municipalities/map" search={{ focus: undefined }}>
              <Button size="sm" variant="outline">
                <Map className="mr-1.5 h-4 w-4" />Map view
              </Button>
            </Link>
            <Button size="sm" onClick={() => setCreating(true)}>
              <Plus className="mr-1.5 h-4 w-4" />Add
            </Button>
          </div>
        }
      />

      {/* Search + expand toggle */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search municipalities…"
            className="pl-9 pr-9"
          />
          {q && (
            <button onClick={() => setQ('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        {parentsWithChildren.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={allExpanded ? collapseAll : expandAll}
          >
            {allExpanded ? 'Collapse all' : 'Expand all'}
          </Button>
        )}
      </div>

      {/* List */}
      <TooltipProvider delayDuration={250}>
        {isLoading ? (
          <TreeSkeleton rows={8} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={MapPin}
            title="No municipalities yet"
            description="Add cities and districts to organise incidents geographically."
            action={
              <Button size="sm" onClick={() => setCreating(true)}>
                <Plus className="mr-1.5 h-4 w-4" /> Add the first one
              </Button>
            }
          />
        ) : matchIds && matchIds.size === 0 ? (
          <EmptyState icon={Search} title={`No municipalities match "${q}"`} />
        ) : (
          // Tree view — when searching, non-matches are dimmed; ancestors stay for context.
          <div className="space-y-2">
            {topLevel.filter(branchMatches).map((parent) => {
              const expanded = isExpanded(parent.id)
              const children = childMap[parent.id] ?? []
              return (
                <div key={parent.id} className="space-y-1">
                  <MuniRow
                    m={parent}
                    dim={!!matchIds && !matchIds.has(parent.id)}
                    expanded={expanded}
                    onToggleExpand={children.length > 0 ? () => toggleExpand(parent.id) : undefined}
                    onEdit={setEditTarget}
                  />
                  {expanded && children.map((child) => (
                    <MuniRow
                      key={child.id}
                      m={child}
                      indent
                      dim={!!matchIds && !matchIds.has(child.id)}
                      onEdit={setEditTarget}
                    />
                  ))}
                </div>
              )
            })}
            {/* Orphaned children (parent deleted) */}
            {Array.from(orphanIds)
              .map((id) => items.find((m) => m.id === id)!)
              .filter((m) => !matchIds || matchIds.has(m.id))
              .map((m) => (
                <MuniRow
                  key={m.id}
                  m={m}
                  orphan
                  onEdit={setEditTarget}
                />
              ))}
          </div>
        )}
      </TooltipProvider>

      {/* Create sheet */}
      <MunicipalityFormSheet
        universeId={universe.id}
        open={creating}
        onClose={() => setCreating(false)}
        allMunicipalities={items}
      />

      {/* Edit sheet */}
      {editItem && universe && (
        <MunicipalityFormSheet
          universeId={universe.id}
          open={!!editTarget}
          onClose={() => setEditTarget(null)}
          initial={editItem as MunicipalityRead}
          allMunicipalities={items}
        />
      )}
    </div>
  )
}
