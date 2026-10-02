import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { toast } from 'sonner'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useCreateMunicipality, useMunicipality, useUpdateMunicipality } from '@/lib/queries'
import type { MunicipalityKind, MunicipalityListItem, MunicipalityRead } from '@/lib/types'
import { textParam } from '@/lib/searchParams'

export type MunicipalitySortKey = 'name' | 'incidents' | 'sets' | 'population'

export interface MunicipalitiesSearch {
  q?: string
  sort?: MunicipalitySortKey
  /** Only municipalities with no boundary, which the map cannot draw. */
  noBoundary?: boolean
}

// The page is in _app.$universe.municipalities.index.lazy.tsx, its own chunk; this file
// keeps the URL schema and the form sheet, which the municipality page imports.
export const Route = createFileRoute('/_app/$universe/municipalities/')({
  validateSearch: (s: Record<string, unknown>): MunicipalitiesSearch => ({
    q: textParam(s.q),
    sort: s.sort === 'incidents' || s.sort === 'sets' || s.sort === 'population' ? s.sort : undefined,
    noBoundary: s.noBoundary === true || s.noBoundary === 'true' ? true : undefined,
  }),
})

// ─── Form sheet (also exported for detail page) ───────────────────────────────

interface MunicipalityFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  /**
   * A list row is enough: the sheet loads the full record before it opens,
   * since a list row has no boundary or description and saving the form
   * would write those back as empty.
   */
  initial?: MunicipalityRead | MunicipalityListItem
  /** When creating a new municipality, preselect this parent in the form. */
  defaultParentId?: string
  allMunicipalities?: MunicipalityListItem[]
}

/**
 * Seeded from props at mount and never resynced, so one mounted sheet reused
 * for a second municipality kept the first's values in any field the second leaves
 * empty - and saving wrote them. Keying on the target forces a fresh instance.
 * See SetFormSheet in routes/_app.$universe.sets.index.tsx for the full note.
 */
export function MunicipalityFormSheet(props: MunicipalityFormProps) {
  const partial = props.initial && !('description' in props.initial) ? props.initial : null
  const { data: full } = useMunicipality(partial?.id ?? '', partial ? props.universeId : null)
  const initial = partial ? full : (props.initial as MunicipalityRead | undefined)
  if (partial && !full) return null
  return <MunicipalityFormSheetInner key={initial?.id ?? 'new'} {...props} initial={initial} />
}

function MunicipalityFormSheetInner({ universeId, open, onClose, initial, defaultParentId, allMunicipalities }: MunicipalityFormProps & { initial?: MunicipalityRead }) {
  const create = useCreateMunicipality()
  const update = useUpdateMunicipality(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const [name, setName] = useState(initial?.name ?? '')
  const [parentId, setParentId] = useState<string>(initial?.parent_id ?? defaultParentId ?? '')
  const [kind, setKind] = useState<Exclude<MunicipalityKind, 'CITY'>>(
    initial?.kind === 'NEIGHBORHOOD' ? 'NEIGHBORHOOD' : 'DISTRICT'
  )
  const [aliases, setAliases] = useState((initial?.aliases ?? []).join(', '))
  const [region, setRegion] = useState(initial?.region ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
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
      setError('Invalid GeoJSON. Paste a Polygon/MultiPolygon geometry, a Feature, or a FeatureCollection whose first feature is a (Multi)Polygon')
      return
    }
    const body = {
      universe_id: universeId,
      name,
      parent_id: parentId || null,
      // A top-level row is always a city; the backend refuses anything else.
      kind: parentId ? kind : 'CITY',
      aliases: aliases.split(',').map((a) => a.trim()).filter(Boolean),
      region: region.trim() || null,
      description: description.trim() || null,
      geometry,
    }
    try {
      if (isEdit) {
        await update.mutateAsync(body)
        toast.success(`Updated "${name}"`)
      } else {
        await create.mutateAsync(body)
        toast.success(`Added "${name}"`)
        setName(''); setParentId(''); setGeometryText('')
        setAliases(''); setRegion(''); setDescription('')
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} municipality`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending
  // Only cities can hold sub-districts: the hierarchy is one level deep.
  const options = allMunicipalities?.filter((m) => m.id !== initial?.id && m.parent_id === null) ?? []
  const regions = [...new Set((allMunicipalities ?? []).map((m) => m.region).filter((r): r is string => !!r))].sort()

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Municipality' : 'Add Municipality'}
        description={isEdit ? 'Update this municipality' : 'Add a city, district or neighborhood'}
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
                  <SelectItem value="none">None</SelectItem>
                  {options.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {parentId && (
            <div className="space-y-1.5">
              <Label>Kind</Label>
              <Select value={kind} onValueChange={(v) => setKind(v as typeof kind)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="DISTRICT">District (splits the city, e.g. a ZIP code)</SelectItem>
                  <SelectItem value="NEIGHBORHOOD">Neighborhood (may overlap districts)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="m-aliases">Aliases <span className="text-zinc-400 font-normal">(comma-separated)</span></Label>
            <Input id="m-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. The Hole, Zone 6" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-region">Region</Label>
            <Input id="m-region" list="m-regions" value={region} onChange={(e) => setRegion(e.target.value)} placeholder="e.g. Downriver" />
            <datalist id="m-regions">
              {regions.map((r) => <option key={r} value={r} />)}
            </datalist>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-description">Description</Label>
            <textarea
              id="m-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={8}
              placeholder="History and character of the place. Its sets, incidents and aliases show from their own records."
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-400 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500/40 resize-y"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-geometry">
              Boundary GeoJSON <span className="text-zinc-400 font-normal">(for map)</span>
            </Label>
            <textarea
              id="m-geometry"
              value={geometryText}
              onChange={(e) => setGeometryText(e.target.value)}
              placeholder={'Paste a GeoJSON Polygon or MultiPolygon geometry here.\n{"type":"Polygon","coordinates":[[[lng,lat],...]]}'}
              rows={6}
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-300 placeholder:text-zinc-400 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500/40 resize-y"
            />
            <p className="text-[11px] text-zinc-400">
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
