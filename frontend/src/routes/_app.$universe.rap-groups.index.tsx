import { createFileRoute } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { X } from 'lucide-react'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { NameVariantsEditor } from '@/components/names/NameVariantsEditor'
import { cleanVariants, seedVariants } from '@/lib/nameVariants'
import { variantDisplay, variantsToDisplayName } from '@/lib/setDisplay'
import { useCreateRapGroup, useMemberSearch, useMunicipalities, useRapGroups, useUpdateRapGroup } from '@/lib/queries'
import type {
  NameVariant, RapGroupKind, RapGroupListItem, RapGroupMemberInput, RapGroupReadDetail, RapGroupRole, RapGroupStatus,
} from '@/lib/types'
import { textParam } from '@/lib/searchParams'

export type RapGroupSortKey = 'name' | 'status' | 'member_count'

export interface RapGroupsSearch {
  q?: string
  kind?: RapGroupKind
  status?: RapGroupStatus
  sort?: RapGroupSortKey
  order?: 'asc' | 'desc'
}

const SORT_KEYS: RapGroupSortKey[] = ['name', 'status', 'member_count']

export const RAP_KIND_LABEL: Record<RapGroupKind, string> = { GROUP: 'Group', LABEL: 'Label' }
export const RAP_STATUS_LABEL: Record<RapGroupStatus, string> = { ACTIVE: 'Active', DISBANDED: 'Disbanded' }
export const RAP_ROLE_LABEL: Record<RapGroupRole, string> = {
  FOUNDER: 'Founder', MEMBER: 'Member', SIGNED: 'Signed', AFFILIATE: 'Affiliate',
}
const ROLES: RapGroupRole[] = ['FOUNDER', 'MEMBER', 'SIGNED', 'AFFILIATE']

// The page is in _app.$universe.rap-groups.index.lazy.tsx, its own chunk; this file keeps
// the URL schema and the form sheet, which the detail page imports.
export const Route = createFileRoute('/_app/$universe/rap-groups/')({
  validateSearch: (s: Record<string, unknown>): RapGroupsSearch => ({
    q: textParam(s.q),
    kind: s.kind === 'GROUP' || s.kind === 'LABEL' ? s.kind : undefined,
    status: s.status === 'ACTIVE' || s.status === 'DISBANDED' ? s.status : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as RapGroupSortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
  }),
})

interface RosterRow extends RapGroupMemberInput {
  name: string
}

interface RapGroupFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  /** Edit mode. */
  initial?: RapGroupReadDetail
  /** Duplicate mode: create, seeded from this group. */
  copyFrom?: RapGroupReadDetail
  /** Create mode: the kind the form opens on. */
  defaultKind?: RapGroupKind
  onSaved?: (data: RapGroupReadDetail) => void
}

/**
 * Seeded from props at mount and never resynced, so the sheet is keyed on its
 * target (see AllianceFormSheet for the full note).
 */
export function RapGroupFormSheet(props: RapGroupFormProps) {
  return <RapGroupFormSheetInner key={props.initial?.id ?? (props.copyFrom ? `dup-${props.copyFrom.id}` : 'new')} {...props} />
}

function RapGroupFormSheetInner({ universeId, open, onClose, initial, copyFrom, defaultKind, onSaved }: RapGroupFormProps) {
  const create = useCreateRapGroup()
  const update = useUpdateRapGroup(initial?.id ?? '', universeId)
  const { data: munisData } = useMunicipalities(universeId)
  const { data: groupsData } = useRapGroups(universeId)
  const isEdit = !!initial
  const src = initial ?? copyFrom

  const [variants, setVariants] = useState<NameVariant[]>(() =>
    copyFrom && !initial
      ? seedVariants(copyFrom).map((v) => (v.is_primary ? { ...v, name: `${v.name || variantDisplay(v)} (copy)`, lead: 'name' as const } : v))
      : seedVariants(src),
  )
  const name = variantsToDisplayName(variants)
  const [kind, setKind] = useState<RapGroupKind>(src?.kind ?? defaultKind ?? 'GROUP')
  const [status, setStatus] = useState<RapGroupStatus>(src?.status ?? 'ACTIVE')
  const [activeFrom, setActiveFrom] = useState<FuzzyDateValue | null>(src?.active_from ?? null)
  const [activeTo, setActiveTo] = useState<FuzzyDateValue | null>(src?.active_to ?? null)
  const [municipalityId, setMunicipalityId] = useState<string>(src?.municipality?.id ?? 'none')
  const [bio, setBio] = useState(src?.bio ?? '')
  const [roster, setRoster] = useState<RosterRow[]>(() =>
    (src?.members ?? []).map((m) => ({ member_id: m.member_id, name: m.display_name, role: m.role, since: m.since, until: m.until })),
  )
  const [friendIds, setFriendIds] = useState<string[]>(() => (src?.relationships ?? []).filter((r) => r.type === 'FRIEND').map((r) => r.rap_group_id))
  const [enemyIds, setEnemyIds] = useState<string[]>(() => (src?.relationships ?? []).filter((r) => r.type === 'ENEMY').map((r) => r.rap_group_id))
  const [error, setError] = useState<string | null>(null)

  const places = useMemo(() => {
    const all = munisData?.items ?? []
    const byId = new Map(all.map((m) => [m.id, m]))
    // A sub-area reads with its city, so two "Downtown"s stay apart.
    return all
      .map((m) => ({ id: m.id, label: m.parent_id && byId.get(m.parent_id) ? `${m.name}, ${byId.get(m.parent_id)!.name}` : m.name, top: !m.parent_id }))
      .sort((a, b) => Number(b.top) - Number(a.top) || a.label.localeCompare(b.label))
  }, [munisData])

  const others = useMemo(
    () => (groupsData?.items ?? []).filter((g) => g.id !== initial?.id).sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })),
    [groupsData, initial],
  )

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const named = cleanVariants(variants)
    if ('error' in named) {
      setError(named.error)
      return
    }
    // The universe travels in the query string on an edit: the PATCH refuses
    // fields it does not know. Members and relationships are complete lists.
    const fields = {
      name: named.name,
      name_variants: named.variants,
      kind,
      status,
      active_from: activeFrom,
      active_to: activeTo,
      municipality_id: municipalityId === 'none' ? null : municipalityId,
      bio: bio || null,
      members: roster.map((r): RapGroupMemberInput => ({ member_id: r.member_id, role: r.role, since: r.since, until: r.until })),
      friend_ids: friendIds,
      enemy_ids: enemyIds.filter((id) => !friendIds.includes(id)),
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
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'}`)
    }
  }

  const isPending = isEdit ? update.isPending : create.isPending
  const noun = kind === 'LABEL' ? 'label' : 'rap group'

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={isEdit ? `Edit ${RAP_KIND_LABEL[kind]}` : copyFrom ? `Duplicate ${RAP_KIND_LABEL[kind]}` : `Add ${kind === 'LABEL' ? 'Label' : 'Rap Group'}`}
        description={isEdit ? `Update ${name || `this ${noun}`}` : `Create a new ${noun}`}
        width="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Kind</Label>
              <Select value={kind} onValueChange={(v) => setKind(v as RapGroupKind)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="GROUP">Group</SelectItem>
                  <SelectItem value="LABEL">Label</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Status</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as RapGroupStatus)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="DISBANDED">Disbanded</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <NameVariantsEditor variants={variants} onChange={setVariants} radioName="rap-group-variant-primary" noun={noun} />
          <div className="grid gap-3 sm:grid-cols-2">
            <FuzzyDateInput value={activeFrom} onChange={setActiveFrom} label="Active from" idPrefix="rap-group-from" />
            <FuzzyDateInput value={activeTo} onChange={setActiveTo} label="Active to" idPrefix="rap-group-to" />
          </div>
          <div className="space-y-1.5">
            <Label>Home area</Label>
            <Select value={municipalityId} onValueChange={setMunicipalityId}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent className="max-h-72">
                <SelectItem value="none">None</SelectItem>
                {places.map((p) => <SelectItem key={p.id} value={p.id}>{p.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>{kind === 'LABEL' ? 'Artists' : 'Members'}</Label>
            <RosterEditor universeId={universeId} value={roster} onChange={setRoster} />
          </div>
          <div className="space-y-1.5">
            <Label>Allies</Label>
            <GroupChecklist groups={others} value={friendIds} onChange={setFriendIds} exclude={enemyIds} />
          </div>
          <div className="space-y-1.5">
            <Label>Enemies</Label>
            <GroupChecklist groups={others} value={enemyIds} onChange={setEnemyIds} exclude={friendIds} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="rg-bio">Bio</Label>
            <Textarea id="rg-bio" value={bio} onChange={(e) => setBio(e.target.value)} placeholder="What it is, how it formed…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : `Create ${kind === 'LABEL' ? 'Label' : 'Rap Group'}`}
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

/** The member list a group is saved with: search to add, a role per row, dates when known. */
function RosterEditor({ universeId, value, onChange }: {
  universeId: string
  value: RosterRow[]
  onChange: (next: RosterRow[]) => void
}) {
  const [q, setQ] = useState('')
  const { data: results = [], isFetching } = useMemberSearch(universeId, q.trim())
  const have = new Set(value.map((r) => r.member_id))
  const patchRow = (id: string, next: Partial<RosterRow>) => onChange(value.map((r) => (r.member_id === id ? { ...r, ...next } : r)))
  return (
    <div className="space-y-2">
      {value.length > 0 && (
        <ul className="divide-y divide-zinc-800 rounded-md border border-zinc-800 bg-zinc-950/50">
          {value.map((r) => (
            <li key={r.member_id} className="px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="min-w-0 flex-1 truncate text-sm text-zinc-100">{r.name}</span>
                <Select value={r.role} onValueChange={(v) => patchRow(r.member_id, { role: v as RapGroupRole })}>
                  <SelectTrigger className="h-8 w-32 text-xs" aria-label={`Role of ${r.name}`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ROLES.map((role) => <SelectItem key={role} value={role}>{RAP_ROLE_LABEL[role]}</SelectItem>)}
                  </SelectContent>
                </Select>
                <button type="button" onClick={() => onChange(value.filter((x) => x.member_id !== r.member_id))} aria-label={`Remove ${r.name}`}
                  className="rounded p-1 text-zinc-500 hover:bg-red-950/40 hover:text-red-400">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
              <details className="mt-1.5">
                <summary className="cursor-pointer text-[11px] text-zinc-400 hover:text-zinc-200">Dates</summary>
                <div className="mt-2 grid gap-3 sm:grid-cols-2">
                  <FuzzyDateInput value={r.since} onChange={(v) => patchRow(r.member_id, { since: v })} label="Since" idPrefix={`rg-since-${r.member_id}`} />
                  <FuzzyDateInput value={r.until} onChange={(v) => patchRow(r.member_id, { until: v })} label="Until" idPrefix={`rg-until-${r.member_id}`} />
                </div>
              </details>
            </li>
          ))}
        </ul>
      )}
      <div className="rounded-md border border-zinc-800">
        <Command shouldFilter={false}>
          <CommandInput value={q} onValueChange={setQ} placeholder="Search members to add…" />
          {q.trim().length >= 2 && (
            <CommandList className="max-h-48">
              {!isFetching && results.length === 0 && <CommandEmpty>No member matches.</CommandEmpty>}
              {results.filter((m) => !have.has(m.id)).map((m) => (
                <CommandItem key={m.id} value={m.id} onSelect={() => {
                  onChange([...value, { member_id: m.id, name: m.display_name, role: 'MEMBER', since: null, until: null }])
                  setQ('')
                }}>
                  <span>{m.display_name}</span>
                  {m.primary_set_name && <span className="ml-auto text-xs text-zinc-500">{m.primary_set_name}</span>}
                </CommandItem>
              ))}
            </CommandList>
          )}
        </Command>
      </div>
    </div>
  )
}

/** Checkbox list of the universe's other groups and labels, chosen ones first. */
function GroupChecklist({ groups, value, onChange, exclude }: {
  groups: RapGroupListItem[]
  value: string[]
  onChange: (next: string[]) => void
  /** Ids on the opposite side: a group is not both ally and enemy. */
  exclude: string[]
}) {
  const chosen = new Set(value)
  const blocked = new Set(exclude)
  const shown = groups
    .filter((g) => !blocked.has(g.id))
    .sort((a, b) => Number(chosen.has(b.id)) - Number(chosen.has(a.id)))
  const toggle = (id: string) => onChange(chosen.has(id) ? value.filter((x) => x !== id) : [...value, id])
  if (shown.length === 0) return <p className="text-xs text-zinc-500">No other group or label to pick.</p>
  return (
    <div className="max-h-40 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950/50">
      {shown.map((g) => (
        <label key={g.id} className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-zinc-900">
          <input type="checkbox" checked={chosen.has(g.id)} onChange={() => toggle(g.id)} className="h-3.5 w-3.5 shrink-0 accent-fuchsia-500" />
          <span className={chosen.has(g.id) ? 'text-white' : 'text-zinc-400'}>{g.name}</span>
          <span className="ml-auto text-[10px] text-zinc-500">{RAP_KIND_LABEL[g.kind]}</span>
        </label>
      ))}
    </div>
  )
}
