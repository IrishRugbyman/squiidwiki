import { createFileRoute, Link } from '@tanstack/react-router'
import { HelpCircle, Plus, Shield, User } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { RankedPicker } from '@/components/sets/RankedPicker'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useAlliances, useAllSets, useCreateSet, useGangs, useMunicipalities, useSet, useUpdateSet } from '@/lib/queries'
import { MAX_EMOJIS, formatEmojiInput, isLikelyEmoji, parseEmojiInput } from '@/lib/emoji'
import { gangColorStyle, leadSlots, normalizeLead, setColorStyle, variantDisplay, variantsToDisplayName } from '@/lib/setDisplay'
import type { NameVariant, SetListItem, SetReadDetail, SetStatus } from '@/lib/types'
import { textParam } from '@/lib/searchParams'

function emptyVariant(isPrimary = false): NameVariant {
  return { name: '', initials: '', number: '', is_primary: isPrimary, lead: null }
}

function initialVariants(initial?: SetReadDetail | null, copyFrom?: SetReadDetail | null): NameVariant[] {
  const src = initial?.name_variants ?? copyFrom?.name_variants
  if (src && src.length > 0) {
    return src.map((v) => ({
      name: v.name ?? '',
      initials: v.initials ?? '',
      number: v.number ?? '',
      is_primary: !!v.is_primary,
      lead: v.lead ?? null,
    }))
  }
  const seedName = initial?.name ?? copyFrom?.name ?? ''
  return [{ name: seedName, initials: '', number: '', is_primary: true, lead: null }]
}

// ─── URL search params ────────────────────────────────────────────────────────

export type SortKey = 'name' | 'status' | 'member_count' | 'alliance' | 'municipality' | 'updated_at' | 'created_at'
export type ViewMode = 'table' | 'cards'

export interface SetsSearch {
  q?: string
  status?: SetStatus
  alliance?: string  // UUID, 'none', or undefined
  gang?: string
  muni?: string
  sort?: SortKey
  order?: 'asc' | 'desc'
  view?: ViewMode
}

const SORT_KEYS: SortKey[] = ['name', 'status', 'member_count', 'alliance', 'municipality', 'updated_at', 'created_at']

export const Route = createFileRoute('/_app/$universe/sets/')({
  // `page` and `size` are gone: the whole universe loads at once and the table
  // virtualises. Old links carrying them still open, the keys are just dropped.
  validateSearch: (s: Record<string, unknown>): SetsSearch => ({
    q: textParam(s.q),
    status: s.status === 'ACTIVE' || s.status === 'EXTINCT' ? s.status : undefined,
    alliance: typeof s.alliance === 'string' && s.alliance ? s.alliance : undefined,
    gang: typeof s.gang === 'string' && s.gang ? s.gang : undefined,
    muni: typeof s.muni === 'string' && s.muni ? s.muni : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as SortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
    view: s.view === 'cards' ? 'cards' : s.view === 'table' ? 'table' : undefined,
  }),
  // The page itself is in _app.$universe.sets.index.lazy.tsx, its own chunk. This file
  // stays in the main bundle because other screens import SetFormSheet from it.
})

// ─── Set avatar ───────────────────────────────────────────────────────────────

/** The glyph for a reserved set, as a component so render never picks a component type. */
export function ReservedSetIcon({ name, className }: { name: string; className?: string }) {
  if (name === 'Police') return <Shield className={className} />
  if (name === 'Unknown') return <HelpCircle className={className} />
  return <User className={className} />
}

export function SetAvatar({ name, thumbUrl, size = 'md', isReserved = false, gangColor = null }: { name: string; thumbUrl?: string | null; size?: 'sm' | 'md' | 'xl'; isReserved?: boolean; gangColor?: string | null }) {
  const [imgError, setImgError] = useState(false)
  const sz =
    size === 'sm' ? 'h-7 w-7 text-xs rounded-md' :
    size === 'xl' ? 'h-20 w-20 text-2xl rounded-lg ring-1 ring-zinc-600/80 shadow-lg shadow-black/30' :
    'h-8 w-8 text-sm rounded-md'
  const iconSz = size === 'sm' ? 'h-3.5 w-3.5' : size === 'xl' ? 'h-8 w-8' : 'h-4 w-4'
  if (isReserved) {
    return (
      <div
        className={`${sz} shrink-0 border border-zinc-700 bg-zinc-800/60 flex items-center justify-center`}
        aria-hidden
      >
        <ReservedSetIcon name={name} className={`${iconSz} text-zinc-400`} />
      </div>
    )
  }
  if (thumbUrl && !imgError) {
    return (
      <img
        src={thumbUrl}
        alt={name}
        loading="lazy"
        decoding="async"
        className={`${sz} shrink-0 object-cover ring-1 ring-zinc-700`}
        onError={() => setImgError(true)}
      />
    )
  }
  return (
    <div
      className={`${sz} shrink-0 border flex items-center justify-center font-bold`}
      style={gangColor ? gangColorStyle(gangColor) : setColorStyle(name)}
      aria-hidden
    >
      {name.slice(0, 2).toUpperCase()}
    </div>
  )
}

// ─── Form sheet ───────────────────────────────────────────────────────────────

interface SetFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: SetReadDetail
  onSaved?: (data: SetReadDetail) => void
  defaultAllianceId?: string
  defaultMunicipalityId?: string
  copyFrom?: SetReadDetail
}

const MUNI_NONE = '__none__'

/**
 * Every state slot in the form below is seeded from props at mount and never
 * resynced, so reusing one mounted sheet for a second set kept the first set's
 * values in any field the second leaves empty - and saving wrote them. React
 * keeps the instance alive when only `initial` changes, which is exactly what
 * happens when the target set is already in the query cache.
 *
 * Keying on the target forces a fresh instance per set, so the seeding is
 * always correct. Done here rather than at each call site: one of the seven
 * had the key, six did not, and a new call site would have to remember.
 */
export function SetFormSheet(props: SetFormProps) {
  const target = props.initial?.id ?? props.copyFrom?.id ?? 'new'
  return <SetFormSheetInner key={target} {...props} />
}

function SetFormSheetInner({ universeId, open, onClose, initial, onSaved, defaultAllianceId, defaultMunicipalityId, copyFrom }: SetFormProps) {
  const create = useCreateSet()
  const update = useUpdateSet(initial?.id ?? '')
  const { data: alliancesData } = useAlliances(universeId)
  const { data: munisData } = useMunicipalities(universeId)
  const { data: gangsData } = useGangs(universeId)
  const { data: allSetsData } = useAllSets(universeId)
  const isEdit = !!initial

  const [variants, setVariants] = useState<NameVariant[]>(() => initialVariants(initial, copyFrom))
  const name = variantsToDisplayName(variants)
  const [emojiText, setEmojiText] = useState(() => formatEmojiInput(initial?.emojis ?? copyFrom?.emojis ?? []))
  const emojis = useMemo(() => parseEmojiInput(emojiText), [emojiText])
  const badEmojis = useMemo(() => emojis.filter((e) => !isLikelyEmoji(e)), [emojis])
  const [bio, setBio] = useState(initial?.bio ?? copyFrom?.bio ?? '')
  const [status, setStatus] = useState<SetStatus>(initial?.status ?? copyFrom?.status ?? 'ACTIVE')
  // Every alliance the set is in, in rank order; the first is the primary.
  const [allianceIds, setAllianceIds] = useState<string[]>(() => {
    const src = initial ?? copyFrom
    if (src?.alliance_ids?.length) return src.alliance_ids
    if (src?.alliance_id) return [src.alliance_id]
    return defaultAllianceId ? [defaultAllianceId] : []
  })
  // Every gang the set claims, in rank order; the first is the primary.
  const [gangIds, setGangIds] = useState<string[]>(() => {
    const src = initial ?? copyFrom
    if (src?.gang_ids?.length) return src.gang_ids
    return src?.gang_id ? [src.gang_id] : []
  })
  const [municipalityId, setMunicipalityId] = useState<string>(initial?.municipality_id ?? copyFrom?.municipality_id ?? defaultMunicipalityId ?? MUNI_NONE)
  const [territoryIds, setTerritoryIds] = useState<string[]>(initial?.territory_ids ?? copyFrom?.territory_ids ?? [])
  const [error, setError] = useState<string | null>(null)

  // Top-level municipalities only — these are the choices for the primary anchor.
  const allMunis = useMemo(() => munisData?.items ?? [], [munisData])
  const topLevelMunis = useMemo(
    () => allMunis.filter((m) => !m.parent_id).sort((a, b) => a.name.localeCompare(b.name)),
    [allMunis],
  )
  // Sub-districts available for the chosen municipality.
  const subDistricts = useMemo(
    () => allMunis
      .filter((m) => m.parent_id === municipalityId)
      .sort((a, b) => a.name.localeCompare(b.name)),
    [allMunis, municipalityId],
  )

  // Map from sub-district id → sets that also claim it (excluding this set).
  const coClaimMap = useMemo(() => {
    const out: Record<string, Array<{ id: string; name: string }>> = {}
    for (const s of allSetsData?.items ?? []) {
      if (s.id === initial?.id) continue
      for (const tid of s.territory_ids ?? []) {
        if (!out[tid]) out[tid] = []
        out[tid].push({ id: s.id, name: s.name })
      }
    }
    return out
  }, [allSetsData, initial?.id])

  // When the primary municipality changes, drop any territory selections that
  // are no longer children of the new parent (or all of them, if user picked
  // "no municipality").
  function handleMunicipalityChange(v: string) {
    setMunicipalityId(v)
    setTerritoryIds((prev) => {
      if (v === MUNI_NONE) return []
      const validChildIds = new Set(allMunis.filter((m) => m.parent_id === v).map((m) => m.id))
      return prev.filter((id) => validChildIds.has(id))
    })
  }

  function toggleTerritory(id: string) {
    setTerritoryIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const municipality_id = municipalityId === MUNI_NONE ? null : municipalityId
    const cleanedVariants = variants
      .map((v) => {
        const cleaned = {
          name: (v.name ?? '').trim() || null,
          initials: (v.initials ?? '').trim() || null,
          number: (v.number ?? '').trim() || null,
          is_primary: v.is_primary,
          lead: v.lead ?? null,
        }
        // Slots the lead names but the variant leaves empty are dropped.
        return { ...cleaned, lead: normalizeLead(cleaned) }
      })
      .filter((v) => v.name || v.initials || v.number)
    if (cleanedVariants.length === 0) {
      setError('At least one name variant is required')
      return
    }
    if (!cleanedVariants.some((v) => v.is_primary)) {
      cleanedVariants[0].is_primary = true
    }
    // The backend derives the set's name from the primary variant and refuses
    // one that disagrees, so this is the same computation, not a guess.
    const submitName = variantsToDisplayName(cleanedVariants)
    if (!submitName) {
      setError('The primary variant must have a name, initials, or number')
      return
    }
    if (badEmojis.length) {
      setError(`Not emojis: ${badEmojis.join(' ')}, plain text belongs in a name variant`)
      return
    }
    if (emojis.length > MAX_EMOJIS) {
      setError(`At most ${MAX_EMOJIS} emojis per set (got ${emojis.length})`)
      return
    }
    const payload = {
      universe_id: universeId,
      name: submitName,
      name_variants: cleanedVariants,
      emojis: emojis.length ? emojis : null,
      bio: bio || null,
      status,
      alliance_ids: allianceIds,
      gang_ids: gangIds,
      municipality_id,
      territory_ids: territoryIds,
    }
    try {
      if (isEdit) {
        const updated = await update.mutateAsync(payload)
        onSaved?.(updated as SetReadDetail)
        toast.success(`Updated "${name}"`)
      } else {
        await create.mutateAsync(payload)
        setVariants([emptyVariant(true)]); setEmojiText(''); setBio(''); setStatus('ACTIVE')
        setAllianceIds([]); setGangIds([]); setMunicipalityId(MUNI_NONE); setTerritoryIds([])
        toast.success(`Created "${name}"`)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} set`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending
  const isReserved = !!initial?.is_reserved

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? 'Edit Set' : 'Add Set'}
        description={isEdit ? 'Update this gang set' : 'Create a new gang set in this universe'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {isReserved && (
            <div className="rounded border border-zinc-700 bg-zinc-900/50 px-3 py-2 text-xs text-zinc-400">
              System set. Only the bio is editable. All other fields are locked.
            </div>
          )}
          {isReserved ? (
            <div className="space-y-1.5">
              <Label htmlFor="set-name">Name</Label>
              <Input id="set-name" value={name} readOnly disabled />
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Names *</Label>
                <span className="text-[11px] text-zinc-400">Primary is shown as the set's display name</span>
              </div>
              <div className="space-y-2">
                {variants.map((v, idx) => (
                  <div
                    key={idx}
                    className={`rounded-md border p-2 ${v.is_primary ? 'border-violet-700/60 bg-violet-950/20' : 'border-zinc-800 bg-zinc-950/40'}`}
                  >
                    <div className="grid grid-cols-3 gap-2">
                      <div className="space-y-1">
                        <Label className="text-[11px] text-zinc-400">Name</Label>
                        <Input
                          value={v.name ?? ''}
                          onChange={(e) =>
                            setVariants((prev) => prev.map((x, i) => (i === idx ? { ...x, name: e.target.value } : x)))
                          }
                          placeholder="Across The Ave"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px] text-zinc-400">Initials</Label>
                        <Input
                          value={v.initials ?? ''}
                          onChange={(e) =>
                            setVariants((prev) => prev.map((x, i) => (i === idx ? { ...x, initials: e.target.value } : x)))
                          }
                          placeholder="ATA"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px] text-zinc-400">Number</Label>
                        <Input
                          value={v.number ?? ''}
                          onChange={(e) =>
                            setVariants((prev) => prev.map((x, i) => (i === idx ? { ...x, number: e.target.value } : x)))
                          }
                          placeholder="282"
                        />
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between gap-3">
                      <label className="flex cursor-pointer items-center gap-1.5 text-xs text-zinc-400">
                        <input
                          type="radio"
                          name="set-variant-primary"
                          checked={v.is_primary}
                          onChange={() =>
                            setVariants((prev) => prev.map((x, i) => ({ ...x, is_primary: i === idx })))
                          }
                          className="h-3 w-3 accent-violet-500"
                        />
                        Primary
                      </label>
                      <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-zinc-400">
                        <span title="Pick the parts shown, in the order you click them: Initials then Number shows CFP 2400">Show as</span>
                        {(['name', 'initials', 'number'] as const).map((slot) => {
                          const filled = !!v[slot]?.trim()
                          const shown = leadSlots(v)
                          const position = shown.indexOf(slot)
                          const active = position >= 0
                          return (
                            <button
                              key={slot}
                              type="button"
                              disabled={!filled}
                              aria-pressed={active}
                              onClick={() =>
                                setVariants((prev) =>
                                  prev.map((x, i) => {
                                    if (i !== idx) return x
                                    const current = leadSlots(x)
                                    const next = current.includes(slot)
                                      ? current.filter((s) => s !== slot)
                                      : [...current, slot]
                                    return { ...x, lead: next.length === 0 ? null : next.length === 1 ? next[0] : next }
                                  }),
                                )
                              }
                              className={`rounded px-1.5 py-0.5 capitalize transition-colors ${
                                active && filled
                                  ? 'bg-violet-700/40 text-violet-200 ring-1 ring-violet-600/50'
                                  : filled
                                  ? 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                                  : 'cursor-not-allowed opacity-30'
                              }`}
                            >
                              {active && shown.length > 1 ? `${position + 1}. ` : ''}
                              {slot}
                            </button>
                          )
                        })}
                        {variantDisplay(v) && (
                          <span className="ml-1 text-zinc-300">
                            → <span className="font-medium text-zinc-100">{variantDisplay(v)}</span>
                          </span>
                        )}
                      </div>
                      {variants.length > 1 && (
                        <button
                          type="button"
                          onClick={() =>
                            setVariants((prev) => {
                              const next = prev.filter((_, i) => i !== idx)
                              if (!next.some((x) => x.is_primary) && next.length > 0) next[0].is_primary = true
                              return next
                            })
                          }
                          className="text-xs text-zinc-400 hover:text-red-400"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setVariants((prev) => [...prev, emptyVariant(false)])}
              >
                <Plus className="mr-1 h-3.5 w-3.5" />
                Add variant
              </Button>
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Status</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as SetStatus)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="EXTINCT">Extinct</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Gangs</Label>
              <RankedPicker value={gangIds} onChange={setGangIds} options={gangsData?.items ?? []} noun="gang" />
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Alliances</Label>
              <RankedPicker value={allianceIds} onChange={setAllianceIds} options={alliancesData?.items ?? []} noun="alliance" />
            </div>
          )}
          {!isReserved && (
            <div className="space-y-1.5">
              <Label>Municipality</Label>
              <Select value={municipalityId} onValueChange={handleMunicipalityChange}>
                <SelectTrigger><SelectValue placeholder="No municipality" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={MUNI_NONE}>None</SelectItem>
                  {topLevelMunis.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {municipalityId !== MUNI_NONE && subDistricts.length === 0 && (
                <p className="text-[11px] text-zinc-400">
                  This municipality has no sub-districts.
                </p>
              )}
            </div>
          )}
          {!isReserved && municipalityId !== MUNI_NONE && subDistricts.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label>Sub-districts</Label>
                <span className="text-xs text-zinc-400 tabular-nums">
                  {territoryIds.length} of {subDistricts.length} selected
                </span>
              </div>
              <div className="max-h-48 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950/50">
                {subDistricts.map((m) => {
                  const checked = territoryIds.includes(m.id)
                  const coClaims = coClaimMap[m.id] ?? []
                  return (
                    <label
                      key={m.id}
                      className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-zinc-900"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleTerritory(m.id)}
                        className="h-3.5 w-3.5 shrink-0 accent-violet-500"
                      />
                      <span className={`flex-1 ${checked ? 'text-white' : 'text-zinc-400'}`}>
                        {m.name}
                      </span>
                      {coClaims.length > 0 && (
                        <span className="flex items-center gap-1 shrink-0">
                          {coClaims.slice(0, 2).map((s) => (
                            <span
                              key={s.id}
                              className="rounded bg-amber-950/60 px-1.5 py-0.5 text-[10px] text-amber-300 border border-amber-800/50"
                              title={`Also claimed by ${s.name}`}
                            >
                              {s.name}
                            </span>
                          ))}
                          {coClaims.length > 2 && (
                            <span className="text-[10px] text-zinc-400">+{coClaims.length - 2}</span>
                          )}
                        </span>
                      )}
                    </label>
                  )
                })}
              </div>
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="set-emojis">Emojis</Label>
            <Input
              id="set-emojis"
              value={emojiText}
              onChange={(e) => setEmojiText(e.target.value)}
              onBlur={() => setEmojiText(formatEmojiInput(parseEmojiInput(emojiText)))}
              placeholder="Paste the glyphs this set uses…"
            />
            <p className="text-[11px] text-zinc-500">
              First is the badge shown in lists. The rest are the other glyphs members
              signal the set with, so an emoji in a handle can be traced back here.
            </p>
            {emojis.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                {emojis.map((e, i) => (
                  <span
                    key={`${e}-${i}`}
                    title={
                      !isLikelyEmoji(e)
                        ? 'Not an emoji, this will be rejected on save'
                        : i === 0
                          ? 'Badge'
                          : undefined
                    }
                    className={
                      'rounded px-1.5 py-0.5 text-base leading-none ' +
                      (!isLikelyEmoji(e)
                        ? 'bg-red-950 ring-1 ring-red-700'
                        : i === 0
                          ? 'bg-zinc-800 ring-1 ring-violet-600'
                          : 'bg-zinc-800')
                    }
                  >
                    {e}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="set-bio">Bio</Label>
            <Textarea id="set-bio" value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Background info…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Set'}
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

// ─── Lazy edit sheet (fetches full set on open) ───────────────────────────────

export function EditSetSheet({ setId, universeId, open, onClose }: {
  setId: string; universeId: string; open: boolean; onClose: () => void
}) {
  const { data: set } = useSet(setId, universeId)
  if (!set) {
    return (
      <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
        <SheetContent title="Edit Set" description="Loading…">
          <div className="space-y-3 pt-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        </SheetContent>
      </Sheet>
    )
  }
  return <SetFormSheet universeId={universeId} open={open} onClose={onClose} initial={set} />
}

const GANG_PILL_CLASS =
  'inline-flex max-w-full items-center gap-1 rounded-full bg-emerald-950/50 px-2 py-0.5 text-[11px] font-medium text-emerald-300 ring-1 ring-emerald-800/50'

/** A gang card as a pill; with a slug it links to the gang's page. */
export function GangPill({ name, slug, color }: { name: string; slug?: string | null; color?: string | null }) {
  const body = (
    <>
      {color && <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: color }} aria-hidden />}
      <span className="truncate">{name}</span>
    </>
  )
  if (!slug) return <span title={`Gang: ${name}`} className={GANG_PILL_CLASS}>{body}</span>
  return (
    <Link
      from="/$universe" to="/$universe/gangs/$id"
      params={{ id: slug }}
      title={`Gang: ${name}`}
      className={`${GANG_PILL_CLASS} transition-colors hover:ring-emerald-600`}
      onClick={(e) => e.stopPropagation()}
    >
      {body}
    </Link>
  )
}

// ─── Duplicate sheet (lazy-fetches full set and seeds copyFrom) ───────────────

export function DuplicateSetSheet({ setId, universeId, open, onClose, fallback }: {
  setId: string; universeId: string; open: boolean; onClose: () => void; fallback: SetListItem | null
}) {
  const { data: set } = useSet(setId, universeId)
  if (!set) {
    if (fallback) {
      // Render with a minimal fallback so the sheet shows something instantly.
      return (
        <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
          <SheetContent title="Duplicate Set" description="Loading…">
            <div className="space-y-3 pt-2">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
            </div>
          </SheetContent>
        </Sheet>
      )
    }
    return null
  }
  return <SetFormSheet universeId={universeId} open={open} onClose={onClose} copyFrom={set} />
}
