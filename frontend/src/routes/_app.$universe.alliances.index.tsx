import { createFileRoute } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { RankedPicker } from '@/components/sets/RankedPicker'
import { NameVariantsEditor } from '@/components/names/NameVariantsEditor'
import { cleanVariants, seedVariants } from '@/lib/nameVariants'
import { EmojiField } from '@/components/names/EmojiField'
import { useEmojiField } from '@/hooks/useEmojiField'
import { formatEmojiInput } from '@/lib/emoji'
import { variantDisplay, variantsToDisplayName } from '@/lib/setDisplay'
import { useCreateAlliance, useGangs, useMemberSearch, useMunicipalities, useUpdateAlliance } from '@/lib/queries'
import type { AllianceRead, AllianceReadDetail, AllianceStatus, NameVariant } from '@/lib/types'
import { textParam } from '@/lib/searchParams'

export type AllianceSortKey = 'name' | 'status' | 'set_count' | 'member_count'

export interface AlliancesSearch {
  q?: string
  status?: AllianceStatus
  sort?: AllianceSortKey
  order?: 'asc' | 'desc'
}

const SORT_KEYS: AllianceSortKey[] = ['name', 'status', 'set_count', 'member_count']

// The page is in _app.$universe.alliances.index.lazy.tsx, its own chunk; this file keeps
// the URL schema and the form sheet, which the alliance page imports.
export const Route = createFileRoute('/_app/$universe/alliances/')({
  validateSearch: (s: Record<string, unknown>): AlliancesSearch => ({
    q: textParam(s.q),
    status: s.status === 'ACTIVE' || s.status === 'DORMANT' || s.status === 'EXTINCT' ? s.status : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as AllianceSortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
  }),
})

interface AllianceFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  /** Edit mode. */
  initial?: AllianceReadDetail
  /** Duplicate mode: create, seeded from this alliance. */
  copyFrom?: AllianceReadDetail
  onSaved?: (data: AllianceRead) => void
}

/**
 * Seeded from props at mount and never resynced, so one mounted sheet reused
 * for a second alliance kept the first's values in any field the second leaves
 * empty - and saving wrote them. Keying on the target forces a fresh instance.
 * See SetFormSheet in routes/_app.$universe.sets.index.tsx for the full note.
 */
export function AllianceFormSheet(props: AllianceFormProps) {
  return <AllianceFormSheetInner key={props.initial?.id ?? (props.copyFrom ? `dup-${props.copyFrom.id}` : 'new')} {...props} />
}

function AllianceFormSheetInner({ universeId, open, onClose, initial, copyFrom, onSaved }: AllianceFormProps) {
  const create = useCreateAlliance()
  const update = useUpdateAlliance(initial?.id ?? '', universeId)
  const { data: gangsData } = useGangs(universeId)
  const { data: munisData } = useMunicipalities(universeId)
  const isEdit = !!initial
  const src = initial ?? copyFrom

  const [variants, setVariants] = useState<NameVariant[]>(() =>
    copyFrom && !initial
      ? seedVariants(copyFrom).map((v) => (v.is_primary ? { ...v, name: `${v.name || variantDisplay(v)} (copy)`, lead: 'name' as const } : v))
      : seedVariants(src),
  )
  const name = variantsToDisplayName(variants)
  const [emojiText, setEmojiText] = useState(() => formatEmojiInput(src?.emojis ?? []))
  const { emojis, error: emojiError } = useEmojiField(emojiText, 'alliance')
  const [description, setDescription] = useState(src?.description ?? '')
  const [status, setStatus] = useState<AllianceStatus>(src?.status ?? 'ACTIVE')
  const [gangIds, setGangIds] = useState<string[]>(() => src?.gang_ids ?? (src?.gang_id ? [src.gang_id] : []))
  const [founder, setFounder] = useState<{ id: string; name: string } | null>(() =>
    src?.founder_id ? { id: src.founder_id, name: src.founder_display_name ?? 'Founder' } : null,
  )
  const [foundedAt, setFoundedAt] = useState<FuzzyDateValue | null>(src?.founded_at ?? null)
  const [territoryIds, setTerritoryIds] = useState<string[]>(src?.territory_ids ?? [])
  const [error, setError] = useState<string | null>(null)

  const places = useMemo(() => {
    const all = munisData?.items ?? []
    const byId = new Map(all.map((m) => [m.id, m]))
    // A sub-area reads with its city, so two "Downtown"s stay apart.
    return all
      .map((m) => ({ id: m.id, label: m.parent_id && byId.get(m.parent_id) ? `${m.name}, ${byId.get(m.parent_id)!.name}` : m.name, top: !m.parent_id }))
      .sort((a, b) => Number(b.top) - Number(a.top) || a.label.localeCompare(b.label))
  }, [munisData])

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const named = cleanVariants(variants)
    if ('error' in named) {
      setError(named.error)
      return
    }
    if (emojiError) {
      setError(emojiError)
      return
    }
    // The universe travels in the query string on an edit: the PATCH refuses
    // fields it does not know.
    const fields = {
      name: named.name,
      name_variants: named.variants,
      emojis: emojis.length ? emojis : null,
      description: description || null,
      status,
      gang_ids: gangIds,
      founder_id: founder?.id ?? null,
      founded_at: foundedAt,
      territory_ids: territoryIds,
    }
    try {
      if (isEdit) {
        const updated = await update.mutateAsync(fields)
        onSaved?.(updated)
        toast.success(`Updated "${named.name}"`)
      } else {
        const created = await create.mutateAsync({ universe_id: universeId, ...fields })
        onSaved?.(created)
        toast.success(`Created "${named.name}"`)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} alliance`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Alliance' : copyFrom ? 'Duplicate Alliance' : 'Add Alliance'}
        description={isEdit ? `Update ${name || 'this alliance'}` : 'Create a new gang alliance'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <NameVariantsEditor variants={variants} onChange={setVariants} radioName="alliance-variant-primary" noun="alliance" />
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as AllianceStatus)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="DORMANT">Dormant</SelectItem>
                <SelectItem value="EXTINCT">Extinct</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Gangs</Label>
            <RankedPicker value={gangIds} onChange={setGangIds} options={gangsData?.items ?? []} noun="gang" />
          </div>
          <div className="space-y-1.5">
            <Label>Founder</Label>
            <MemberPicker universeId={universeId} value={founder} onChange={setFounder} />
          </div>
          <FuzzyDateInput value={foundedAt} onChange={setFoundedAt} label="Founded" idPrefix="alliance-founded" />
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Cities and areas</Label>
              <span className="text-xs tabular-nums text-zinc-400">{territoryIds.length} selected</span>
            </div>
            <PlaceChecklist places={places} value={territoryIds} onChange={setTerritoryIds} />
          </div>
          <EmojiField id="alliance-emojis" value={emojiText} onChange={setEmojiText} noun="alliance" />
          <div className="space-y-1.5">
            <Label htmlFor="a-desc">Description</Label>
            <Textarea id="a-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What the bloc is, how it formed…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Alliance'}
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

/** Search the universe's members by name and pick one; the chosen one shows as a chip. */
function MemberPicker({ universeId, value, onChange }: {
  universeId: string
  value: { id: string; name: string } | null
  onChange: (v: { id: string; name: string } | null) => void
}) {
  const [q, setQ] = useState('')
  const { data: results = [], isFetching } = useMemberSearch(universeId, q.trim())
  if (value) {
    return (
      <div className="flex items-center gap-2">
        <span className="rounded-md border border-zinc-700 bg-zinc-800/60 px-2 py-1 text-sm text-zinc-100">{value.name}</span>
        <button type="button" onClick={() => onChange(null)} className="text-xs text-zinc-400 hover:text-red-400">Remove</button>
      </div>
    )
  }
  return (
    <div className="rounded-md border border-zinc-800">
      <Command shouldFilter={false}>
        <CommandInput value={q} onValueChange={setQ} placeholder="Search members…" />
        {q.trim().length >= 2 && (
          <CommandList className="max-h-48">
            {!isFetching && results.length === 0 && <CommandEmpty>No member matches.</CommandEmpty>}
            {results.map((m) => (
              <CommandItem key={m.id} value={m.id} onSelect={() => { onChange({ id: m.id, name: m.display_name }); setQ('') }}>
                <span>{m.display_name}</span>
                {m.primary_set_name && <span className="ml-auto text-xs text-zinc-500">{m.primary_set_name}</span>}
              </CommandItem>
            ))}
          </CommandList>
        )}
      </Command>
    </div>
  )
}

/** Filterable checkbox list of every place in the universe, chosen ones first. */
function PlaceChecklist({ places, value, onChange }: {
  places: { id: string; label: string }[]
  value: string[]
  onChange: (next: string[]) => void
}) {
  const [filter, setFilter] = useState('')
  const chosen = new Set(value)
  const f = filter.trim().toLowerCase()
  const shown = places
    .filter((p) => !f || p.label.toLowerCase().includes(f))
    .sort((a, b) => Number(chosen.has(b.id)) - Number(chosen.has(a.id)))
  const toggle = (id: string) => onChange(chosen.has(id) ? value.filter((x) => x !== id) : [...value, id])
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-950/50">
      <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter places…" className="rounded-b-none border-0 border-b border-zinc-800" />
      <div className="max-h-48 overflow-y-auto">
        {shown.map((p) => (
          <label key={p.id} className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-zinc-900">
            <input type="checkbox" checked={chosen.has(p.id)} onChange={() => toggle(p.id)} className="h-3.5 w-3.5 shrink-0 accent-violet-500" />
            <span className={chosen.has(p.id) ? 'text-white' : 'text-zinc-400'}>{p.label}</span>
          </label>
        ))}
        {shown.length === 0 && <p className="px-3 py-2 text-xs text-zinc-500">No place matches.</p>}
      </div>
    </div>
  )
}
