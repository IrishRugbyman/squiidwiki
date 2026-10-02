import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { GangSwatch } from '@/components/gangs/GangSwatch'
import { Sheet, SheetClose, SheetContent } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { BRAND } from '@/lib/brand'
import { descendantIds, NATION_LABEL, NATION_NUMBER } from '@/lib/gangs'
import { useCreateGang, useGangs, useUpdateGang } from '@/lib/queries'
import type { GangListItem, GangNation, GangWrite, UUID } from '@/lib/types'

const NONE = '__none__'

interface GangFormProps {
  open: boolean
  onClose: () => void
  initial: GangListItem | null
  universeId: UUID
  /** Pre-select a parent when adding a branch from a card's page. */
  defaultParentId?: UUID
}

/**
 * Seeded from props at mount and never resynced, so one mounted sheet reused
 * for a second gang kept the first's values in any field the second leaves
 * empty - and saving wrote them. Keying on the target forces a fresh instance.
 * See SetFormSheet in routes/_app.$universe.sets.index.tsx for the full note.
 */
export function GangFormSheet(props: GangFormProps) {
  return <GangFormSheetInner key={props.initial?.id ?? `new-${props.defaultParentId ?? ''}`} {...props} />
}

function splitList(text: string): string[] {
  return text.split(',').map((s) => s.trim()).filter(Boolean)
}

function ColorField({ id, label, value, onChange, fallback }: {
  id: string
  label: string
  value: string
  onChange: (v: string) => void
  fallback: string
}) {
  return (
    <div className="space-y-1">
      <p className="text-[11px] text-zinc-400">{label}</p>
      <div className="flex items-center gap-1.5">
        <input
          id={id}
          type="color"
          value={value || fallback}
          onChange={(e) => onChange(e.target.value)}
          className="h-8 w-10 shrink-0 cursor-pointer rounded border border-zinc-700 bg-zinc-900 p-0.5"
          aria-label={label}
        />
        <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder={fallback} className="font-mono text-xs" />
      </div>
      {value && (
        <button type="button" onClick={() => onChange('')} className="text-[10px] text-zinc-400 hover:text-zinc-300">
          Clear
        </button>
      )}
    </div>
  )
}

function GangFormSheetInner({ open, onClose, initial, universeId, defaultParentId }: GangFormProps) {
  const create = useCreateGang(universeId)
  const update = useUpdateGang(universeId)
  const { data: gangsData } = useGangs(universeId)
  const [name, setName] = useState(initial?.name ?? '')
  const [aliases, setAliases] = useState((initial?.aliases ?? []).join(', '))
  const [description, setDescription] = useState(initial?.description ?? '')
  const [cardDescription, setCardDescription] = useState(initial?.card_description ?? '')
  const [color, setColor] = useState(initial?.color ?? '')
  const [colorSecondary, setColorSecondary] = useState(initial?.color_secondary ?? '')
  const [parentId, setParentId] = useState<string>(initial?.parent_id ?? defaultParentId ?? NONE)
  const [nation, setNation] = useState<string>(initial?.nation ?? NONE)
  const [origin, setOrigin] = useState(initial?.origin ?? '')
  const [foundedYear, setFoundedYear] = useState(initial?.founded_at?.year ? String(initial.founded_at.year) : '')
  const [foundedApprox, setFoundedApprox] = useState(initial?.founded_at?.approx ?? false)
  const [symbols, setSymbols] = useState((initial?.symbols ?? []).join(', '))
  const [error, setError] = useState<string | null>(null)

  const isEdit = !!initial
  // A card cannot sit under itself or under one of its own branches.
  const parentChoices = useMemo(() => {
    const all = gangsData?.items ?? []
    const blocked = initial ? descendantIds(initial.id, all) : new Set<UUID>()
    return all.filter((g) => !blocked.has(g.id)).sort((a, b) => a.name.localeCompare(b.name))
  }, [gangsData, initial])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const year = foundedYear.trim()
    if (year && !/^\d{3,4}$/.test(year)) {
      setError('Founded must be a year, like 1969')
      return
    }
    const aliasList = splitList(aliases)
    const symbolList = splitList(symbols)
    const body: GangWrite & { name: string } = {
      name: name.trim(),
      aliases: aliasList.length ? aliasList : null,
      description: description.trim() || null,
      color: color.trim() || null,
      color_secondary: colorSecondary.trim() || null,
      parent_id: parentId === NONE ? null : parentId,
      nation: nation === NONE ? null : (nation as GangNation),
      origin: origin.trim() || null,
      founded_at: year ? { year: Number(year), precision: 'Y', approx: foundedApprox } : null,
      symbols: symbolList.length ? symbolList : null,
      card_description: cardDescription.trim() || null,
    }
    try {
      if (isEdit && initial) {
        await update.mutateAsync({ id: initial.id, ...body })
        toast.success(`Updated ${body.name}`)
      } else {
        await create.mutateAsync(body)
        toast.success(`Created ${body.name}`)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? `Edit ${initial?.name}` : 'New gang'}
        description="A gang card or nation, claimed by sets and tagged on alliances and members."
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {isEdit && initial?.card_id && (
            <p className="rounded-md border border-violet-900/60 bg-violet-950/30 px-3 py-2 text-[11px] text-violet-200">
              Colours, nation, parent, origin, founding, symbols and history are shared by every universe that has this gang.
              Changing them here changes them everywhere.
            </p>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="gang-name">Name *</Label>
            <Input id="gang-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Gangster Disciples" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gang-aliases">Aliases (comma-separated)</Label>
            <Input id="gang-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="GD, BGD, Growth & Development" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Branch of</Label>
              <Select value={parentId} onValueChange={setParentId}>
                <SelectTrigger aria-label="Parent gang"><SelectValue placeholder="Top-level card" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>Top-level card</SelectItem>
                  {parentChoices.map((g) => (
                    <SelectItem key={g.id} value={g.id}>
                      <span className="inline-flex items-center gap-2">
                        <GangSwatch color={g.color} secondary={g.color_secondary} size="xs" />
                        {g.name}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Nation</Label>
              <Select value={nation} onValueChange={setNation}>
                <SelectTrigger aria-label="Nation"><SelectValue placeholder="None" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>None</SelectItem>
                  {(['FOLK', 'PEOPLE'] as GangNation[]).map((n) => (
                    <SelectItem key={n} value={n}>{NATION_LABEL[n]} ({NATION_NUMBER[n]})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <p className="-mt-2 text-[11px] text-zinc-500">
            Nation is for Chicago lineages. A branch inherits its parent&apos;s nation, so leave it empty there.
          </p>
          <div className="space-y-1.5">
            <Label>Colors</Label>
            <div className="grid grid-cols-2 gap-3">
              <ColorField id="gang-color" label="Primary (fill)" value={color} onChange={setColor} fallback={BRAND.strong} />
              <ColorField id="gang-color-secondary" label="Secondary (stripe)" value={colorSecondary} onChange={setColorSecondary} fallback="#000000" />
            </div>
            <p className="text-[11px] text-zinc-400">
              Territory polygons show diagonal stripes of both colors. Primary also tints pins, set avatars and alliance cards.
            </p>
          </div>
          <div className="grid grid-cols-[1fr_auto] gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="gang-origin">Origin</Label>
              <Input id="gang-origin" value={origin} onChange={(e) => setOrigin(e.target.value)} placeholder="Chicago, Englewood" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="gang-founded">Founded</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="gang-founded"
                  inputMode="numeric"
                  value={foundedYear}
                  onChange={(e) => setFoundedYear(e.target.value)}
                  placeholder="1969"
                  className="w-20"
                />
                <label className="flex items-center gap-1 text-[11px] text-zinc-400">
                  <input type="checkbox" checked={foundedApprox} onChange={(e) => setFoundedApprox(e.target.checked)} />
                  approx.
                </label>
              </div>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gang-symbols">Symbols (comma-separated)</Label>
            <Input id="gang-symbols" value={symbols} onChange={(e) => setSymbols(e.target.value)} placeholder="six-pointed star, pitchfork, heart with wings" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gang-card-desc">History</Label>
            <Textarea id="gang-card-desc" value={cardDescription} onChange={(e) => setCardDescription(e.target.value)} rows={4} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gang-desc">Local note</Label>
            <Textarea
              id="gang-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="What is particular to this universe: where it sits, how it rides here"
            />
            <p className="text-[11px] text-zinc-500">Only this universe sees the local note and the aliases above.</p>
          </div>
          {error && <p className="text-xs text-red-400" role="alert">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={create.isPending || update.isPending} className="flex-1">
              {isEdit ? 'Save' : 'Create'}
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
