import { useEffect, useMemo, useState } from 'react'
import { UserPlus, X } from 'lucide-react'
import { toast } from 'sonner'
import { FacebookIcon, InstagramIcon, TwitterIcon } from '@/components/icons/SocialIcons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import {
  useCreateMember, useUpdateMember,
  useSets, useAlliances, useGangs, useMember, useMemberSearch,
  useMdocLookup, useMdocImportPhoto,
  useCreateSet, useCreateAlliance, useCreateGang,
} from '@/lib/queries'
import { useDebounce } from '@/hooks/useDebounce'
import { api } from '@/lib/api'
import { UrlPasteBanner, useUrlPasteBanner } from '@/components/UrlPasteBanner'
import { SourceFormSheet } from '@/routes/_app.sources.index'
import type { MemberListItem, MemberRead, MemberStatus, SetRank } from '@/lib/types'
import type { FuzzyDateValue } from '@/components/FuzzyDate'
import { AffiliationCombobox, type ComboboxItem } from './pickers/AffiliationCombobox'
import { PhotoSection, flushPhotoQueue } from './sections/PhotoSection'
import { MemberStatusBadge } from '@/components/StatusBadge'

// ─── Status styling ───────────────────────────────────────────────────────────

const STATUS_AVATAR: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-900 text-emerald-300',
  LOCKED: 'bg-orange-900 text-orange-300',
  DEAD: 'bg-zinc-800 text-zinc-500',
  UNKNOWN: 'bg-zinc-800 text-zinc-500',
  ESCAPEE: 'bg-amber-900 text-amber-300',
  ABSCONDER: 'bg-yellow-900 text-yellow-300',
}

const STATUS_DOT: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-400',
  LOCKED: 'bg-orange-400',
  DEAD: 'bg-zinc-600',
  UNKNOWN: 'bg-zinc-600',
  ESCAPEE: 'bg-amber-400',
  ABSCONDER: 'bg-yellow-400',
}

const ALL_STATUSES: MemberStatus[] = ['FREE', 'LOCKED', 'ESCAPEE', 'ABSCONDER', 'DEAD', 'UNKNOWN']

// ─── Family types ─────────────────────────────────────────────────────────────

export type FamilyRole = 'father' | 'son' | 'brother' | 'cousin' | 'uncle' | 'nephew'

export const FAMILY_ROLES: FamilyRole[] = ['father', 'son', 'brother', 'cousin', 'uncle', 'nephew']

export const ROLE_LABEL: Record<FamilyRole, string> = {
  father: 'Father',
  son: 'Son',
  brother: 'Brother',
  cousin: 'Cousin',
  uncle: 'Uncle',
  nephew: 'Nephew',
}

export interface FamilyEntry { role: FamilyRole; memberId: string }

export function familyDictToEntries(family: Record<string, unknown> | null | undefined): FamilyEntry[] {
  if (!family) return []
  const entries: FamilyEntry[] = []
  for (const [role, val] of Object.entries(family)) {
    const ids = Array.isArray(val) ? (val as string[]) : [val as string]
    for (const id of ids) if (id) entries.push({ role: role as FamilyRole, memberId: id })
  }
  return entries
}

export function familyEntriesToDict(entries: FamilyEntry[]): Record<string, unknown> | null {
  if (!entries.length) return null
  const result: Record<string, string | string[]> = {}
  for (const { role, memberId } of entries) {
    if (role === 'father') {
      result.father = memberId
    } else {
      if (!Array.isArray(result[role])) result[role] = []
      ;(result[role] as string[]).push(memberId)
    }
  }
  return result
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

// ─── Form section ─────────────────────────────────────────────────────────────

function FormSection({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2 py-3 first:pt-0 last:pb-0">
      <div className="flex items-baseline justify-between">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{title}</h3>
        {hint && <span className="text-[11px] text-zinc-600">{hint}</span>}
      </div>
      <div className="space-y-2">{children}</div>
    </section>
  )
}

// ─── Avatar ───────────────────────────────────────────────────────────────────

export function MemberAvatar({ member }: { member: MemberListItem }) {
  const [imgError, setImgError] = useState(false)
  if (member.primary_photo_thumb_url && !imgError) {
    return (
      <img
        src={member.primary_photo_thumb_url}
        alt={member.display_name}
        loading="lazy"
        decoding="async"
        className="h-7 w-7 rounded-full object-cover ring-1 ring-zinc-700"
        onError={() => setImgError(true)}
      />
    )
  }
  return (
    <div className={`flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-bold ${STATUS_AVATAR[member.status]}`}>
      {initials(member.display_name)}
    </div>
  )
}

// ─── Family editor ────────────────────────────────────────────────────────────

function FamilyEditor({
  entries,
  onChange,
  universeId,
  excludeMemberId,
}: {
  entries: FamilyEntry[]
  onChange: (entries: FamilyEntry[]) => void
  universeId: string
  excludeMemberId?: string
}) {
  const [newRole, setNewRole] = useState<FamilyRole>('brother')
  const [newMemberId, setNewMemberId] = useState('')
  const [memberSearch, setMemberSearch] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  // Accumulates display_name by member id as search results arrive and members are picked.
  const [nameCache, setNameCache] = useState<Record<string, string>>({})

  const debouncedSearch = useDebounce(memberSearch, 300)
  const { data: searchResults } = useMemberSearch(universeId, debouncedSearch)

  useEffect(() => {
    const results = searchResults ?? []
    if (!results.length) return
    setNameCache((prev) => {
      const next = { ...prev }
      for (const m of results) next[m.id] = m.display_name
      return next
    })
  }, [searchResults])

  const filteredMembers = useMemo(
    () => (searchResults ?? []).filter((m) => m.id !== excludeMemberId).slice(0, 8),
    [searchResults, excludeMemberId],
  )

  const selectedName = newMemberId ? (nameCache[newMemberId] ?? undefined) : undefined

  function addEntry() {
    if (!newMemberId) return
    if (newRole === 'father') {
      onChange([...entries.filter((e) => e.role !== 'father'), { role: newRole, memberId: newMemberId }])
    } else {
      if (entries.some((e) => e.role === newRole && e.memberId === newMemberId)) return
      onChange([...entries, { role: newRole, memberId: newMemberId }])
    }
    setNewMemberId('')
    setMemberSearch('')
  }

  function removeEntry(idx: number) {
    onChange(entries.filter((_, i) => i !== idx))
  }

  const memberName = (id: string) => nameCache[id] ?? id.slice(0, 8) + '…'

  const groupedEntries = FAMILY_ROLES.map((role) => ({
    role,
    entries: entries.filter((e) => e.role === role),
  })).filter((g) => g.entries.length > 0)

  return (
    <div className="space-y-2">
      {groupedEntries.length > 0 ? (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-3 space-y-2">
          {groupedEntries.map(({ role, entries: grp }) => (
            <div key={role} className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-medium uppercase tracking-wider text-zinc-500 w-14 shrink-0">
                {ROLE_LABEL[role]}
              </span>
              {grp.map((entry, gi) => {
                const idx = entries.findIndex((e) => e === entry)
                return (
                  <span key={gi} className="inline-flex items-center gap-1 rounded-full bg-zinc-800 pl-2 pr-1 py-0.5 text-xs text-zinc-300">
                    {memberName(entry.memberId)}
                    <button
                      type="button"
                      onClick={() => removeEntry(idx)}
                      className="rounded-full p-0.5 text-zinc-500 hover:bg-zinc-700 hover:text-white"
                    >
                      <X className="h-2.5 w-2.5" />
                    </button>
                  </span>
                )
              })}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs italic text-zinc-600">No family members added yet.</p>
      )}

      <div>
        <p className="mb-1 text-[11px] text-zinc-500">Add family member</p>
        <div className="flex gap-1.5">
          <Select value={newRole} onValueChange={(v) => setNewRole(v as FamilyRole)}>
            <SelectTrigger className="h-9 w-28 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {FAMILY_ROLES.map((r) => (
                <SelectItem key={r} value={r} className="text-xs">{ROLE_LABEL[r]}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="relative flex-1">
            <Input
              className="h-9 text-xs"
              placeholder={selectedName ?? 'Search member by name…'}
              value={memberSearch}
              onChange={(e) => {
                setMemberSearch(e.target.value)
                setNewMemberId('')
                setShowDropdown(true)
              }}
              onFocus={() => setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
            />
            {showDropdown && filteredMembers.length > 0 && (
              <div className="absolute left-0 right-0 top-full z-50 mt-1 rounded-md border border-zinc-700 bg-zinc-900 shadow-xl">
                {filteredMembers.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs hover:bg-zinc-800"
                    onMouseDown={() => {
                      setNameCache((prev) => ({ ...prev, [m.id]: m.display_name }))
                      setNewMemberId(m.id)
                      setMemberSearch(m.display_name)
                      setShowDropdown(false)
                    }}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[m.status]}`} />
                    <span className="text-zinc-200">{m.display_name}</span>
                    <span className="ml-auto text-zinc-600 text-[10px]">{m.status}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <Button type="button" size="sm" className="h-9" onClick={addEntry} disabled={!newMemberId}>
            <UserPlus className="mr-1 h-3.5 w-3.5" />
            Add
          </Button>
        </div>
      </div>
    </div>
  )
}

// ─── Social helpers ───────────────────────────────────────────────────────────

const SOCIAL_HOSTS: Record<'facebook' | 'instagram' | 'twitter', RegExp> = {
  facebook: /^(?:https?:\/\/)?(?:www\.|m\.)?facebook\.com\//i,
  instagram: /^(?:https?:\/\/)?(?:www\.)?instagram\.com\//i,
  twitter: /^(?:https?:\/\/)?(?:www\.)?(?:twitter|x)\.com\//i,
}

const SOCIAL_BASE: Record<'facebook' | 'instagram' | 'twitter', string> = {
  facebook: 'https://facebook.com/',
  instagram: 'https://instagram.com/',
  twitter: 'https://x.com/',
}

/** Strip protocol/host/@ to a bare handle. Empty input → empty output. */
function normalizeHandle(platform: 'facebook' | 'instagram' | 'twitter', raw: string): string {
  const trimmed = raw.trim()
  if (!trimmed) return ''
  const stripped = trimmed
    .replace(SOCIAL_HOSTS[platform], '')
    .replace(/^@/, '')
    .replace(/[/?#].*$/, '')
  return stripped
}

function SocialInput({
  platform, value, onChange, Icon, label,
}: {
  platform: 'facebook' | 'instagram' | 'twitter'
  value: string
  onChange: (v: string) => void
  Icon: React.ComponentType<{ className?: string }>
  label: string
}) {
  const handle = normalizeHandle(platform, value)
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 shrink-0 text-zinc-500" />
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={() => {
            const cleaned = normalizeHandle(platform, value)
            if (cleaned !== value) onChange(cleaned)
          }}
          placeholder={label}
          aria-label={label}
        />
      </div>
      {handle && (
        <a
          href={SOCIAL_BASE[platform] + handle}
          target="_blank"
          rel="noreferrer noopener"
          className="ml-6 block truncate text-[11px] text-zinc-600 hover:text-violet-400"
          title={SOCIAL_BASE[platform] + handle}
        >
          {SOCIAL_BASE[platform]}{handle}
        </a>
      )}
    </div>
  )
}

// ─── Form sheet ───────────────────────────────────────────────────────────────

interface MemberFormProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: MemberRead
  defaultSetId?: string
  defaultAllianceId?: string
  copyFrom?: MemberRead
}

export function MemberFormSheet({ universeId, open, onClose, initial, defaultSetId, defaultAllianceId, copyFrom }: MemberFormProps) {
  const create = useCreateMember()
  const update = useUpdateMember(initial?.id ?? '', universeId)
  const isEdit = !!initial

  const { data: sets } = useSets(universeId)
  const { data: alliances } = useAlliances(universeId)
  const { data: gangs } = useGangs(universeId)
  const createSet = useCreateSet()
  const createAlliance = useCreateAlliance()
  const createGang = useCreateGang(universeId)

  const setItems: ComboboxItem[] = useMemo(
    () => (sets?.items ?? []).map((s) => ({
      id: s.id,
      name: s.name,
      hint: s.status === 'EXTINCT' ? 'extinct' : undefined,
      dotClass: s.status === 'EXTINCT' ? 'bg-zinc-600' : 'bg-emerald-400',
    })),
    [sets],
  )
  const allianceItems: ComboboxItem[] = useMemo(
    () => (alliances?.items ?? []).map((a) => ({
      id: a.id,
      name: a.name,
      hint: a.status === 'ACTIVE' ? undefined : a.status.toLowerCase(),
      dotClass:
        a.status === 'ACTIVE' ? 'bg-emerald-400'
        : a.status === 'DORMANT' ? 'bg-amber-400'
        : 'bg-zinc-600',
    })),
    [alliances],
  )
  const gangItems: ComboboxItem[] = useMemo(
    () => (gangs?.items ?? []).map((g) => ({
      id: g.id,
      name: g.name,
      dotClass: 'bg-violet-400',
    })),
    [gangs],
  )

  async function handleCreateSet(name: string) {
    try {
      const created = await createSet.mutateAsync({
        universe_id: universeId,
        name,
        status: 'ACTIVE',
        territory_ids: [],
      })
      const isPrimary = affiliations.length === 0
      setAffiliations((prev) => [...prev, { set_id: created.id, rank: '', is_primary: isPrimary || prev.every((a) => !a.is_primary) }])
      toast.success(`Created set "${name}"`)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : `Couldn't create set "${name}"`)
    }
  }
  async function handleCreateAlliance(name: string) {
    try {
      const created = await createAlliance.mutateAsync({
        universe_id: universeId,
        name,
        status: 'ACTIVE',
      })
      setAllianceId(created.id)
      toast.success(`Created alliance "${name}"`)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : `Couldn't create alliance "${name}"`)
    }
  }
  async function handleCreateGang(name: string) {
    try {
      const created = await createGang.mutateAsync({ name })
      setGangId(created.id)
      toast.success(`Created gang "${name}"`)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : `Couldn't create gang "${name}"`)
    }
  }

  const [nickname, setNickname] = useState(initial?.nickname ?? copyFrom?.nickname ?? '')
  const [legalName, setLegalName] = useState(initial?.legal_name ?? copyFrom?.legal_name ?? '')
  const [nicknameUnknown, setNicknameUnknown] = useState(initial?.nickname_unknown ?? copyFrom?.nickname_unknown ?? false)
  const [status, setStatus] = useState<MemberStatus>(initial?.status ?? copyFrom?.status ?? 'UNKNOWN')
  type AffRow = { set_id: string; rank: SetRank | ''; is_primary: boolean }
  const seedAffiliations = (): AffRow[] => {
    const src = initial ?? copyFrom
    if (src?.affiliations && src.affiliations.length > 0) {
      return src.affiliations.map((a) => ({ set_id: a.set_id, rank: a.rank ?? '', is_primary: a.is_primary }))
    }
    if (defaultSetId) return [{ set_id: defaultSetId, rank: '', is_primary: true }]
    return []
  }
  const [affiliations, setAffiliations] = useState<AffRow[]>(seedAffiliations)
  const [allianceId, setAllianceId] = useState<string>(initial?.alliance_id ?? copyFrom?.alliance_id ?? defaultAllianceId ?? '')
  const [gangId, setGangId] = useState<string>(initial?.gang_id ?? copyFrom?.gang_id ?? '')
  const [biography, setBiography] = useState(initial?.biography ?? copyFrom?.biography ?? '')
  const [aliases, setAliases] = useState(initial?.aliases?.join(', ') ?? copyFrom?.aliases?.join(', ') ?? '')
  const seedSocial = (key: 'facebook' | 'instagram' | 'twitter'): string => {
    const sm = (initial?.social_media ?? copyFrom?.social_media) as Record<string, string> | null | undefined
    return sm?.[key] ?? ''
  }
  const [facebook, setFacebook] = useState<string>(seedSocial('facebook'))
  const [instagram, setInstagram] = useState<string>(seedSocial('instagram'))
  const [twitter, setTwitter] = useState<string>(seedSocial('twitter'))
  const [dob, setDob] = useState<FuzzyDateValue | null>(initial?.dob ?? copyFrom?.dob ?? null)
  const [dateOfDeath, setDateOfDeath] = useState<FuzzyDateValue | null>(initial?.date_of_death ?? copyFrom?.date_of_death ?? null)
  const [familyEntries, setFamilyEntries] = useState<FamilyEntry[]>(
    () => familyDictToEntries(initial?.family as Record<string, unknown> | null)
  )
  const [error, setError] = useState<string | null>(null)
  const mdocLookup = useMdocLookup()
  const mdocImportPhoto = useMdocImportPhoto()
  const [mdocUrl, setMdocUrl] = useState('')
  const [mdocPending, setMdocPending] = useState<{
    earliest_release_date: FuzzyDateValue | null
    max_discharge_date: FuzzyDateValue | null
    facility: string | null
    photo_url: string | null
  } | null>(null)
  const urlPaste = useUrlPasteBanner()
  const [creatingSourceFromUrl, setCreatingSourceFromUrl] = useState<string | null>(null)

  // Inline incarceration (create-only). Edit mode still routes users to the
  // detail page so they don't accidentally clobber an active spell from here.
  const [incFromDate, setIncFromDate] = useState<FuzzyDateValue | null>(null)
  const [incMaxDate, setIncMaxDate] = useState<FuzzyDateValue | null>(null)
  const [incLife, setIncLife] = useState(false)
  const [incFacility, setIncFacility] = useState('')
  const [incCaseId, setIncCaseId] = useState('')
  const [incNotes, setIncNotes] = useState('')
  const [photoQueue, setPhotoQueue] = useState<File[]>([])

  const displayPreview = (nicknameUnknown || !nickname.trim()) ? legalName.trim() : nickname.trim()
  const identityValid = displayPreview.length > 0

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    if (!identityValid) {
      setError(nicknameUnknown
        ? 'Provide a legal name (nickname is marked unknown).'
        : 'Provide a nickname or legal name.')
      return
    }
    const aliasList = aliases.split(',').map((s) => s.trim()).filter(Boolean)
    const social: Record<string, string> = {}
    if (facebook.trim()) social.facebook = facebook.trim()
    if (instagram.trim()) social.instagram = instagram.trim()
    if (twitter.trim()) social.twitter = twitter.trim()
    const body: Record<string, unknown> = {
      universe_id: universeId,
      nickname: nickname || null,
      legal_name: legalName || null,
      nickname_unknown: nicknameUnknown,
      status,
      affiliations: affiliations.filter((a) => a.set_id).map((a) => ({
        set_id: a.set_id,
        rank: a.rank || null,
        is_primary: a.is_primary,
      })),
      alliance_id: allianceId || null,
      gang_id: gangId || null,
      biography,
      aliases: aliasList.length > 0 ? aliasList : null,
      dob: dob ?? null,
      date_of_death: status === 'DEAD' ? dateOfDeath : null,
      family: familyEntriesToDict(familyEntries),
      social_media: Object.keys(social).length > 0 ? social : null,
    }
    const label = nickname || legalName || 'member'
    try {
      if (isEdit) {
        await update.mutateAsync(body)
        toast.success(`Updated ${label}`)
      } else {
        const created = await create.mutateAsync(body)
        toast.success(`Created ${label}`)
        if (photoQueue.length > 0) {
          await flushPhotoQueue({
            files: photoQueue,
            memberId: created.id,
            universeId,
            api,
          })
        }
        // Inline incarceration spell (create flow). Only fires if status=LOCKED and the user
        // entered something — otherwise we silently skip to avoid creating empty rows.
        if (status === 'LOCKED' && (incFromDate || incMaxDate || incLife || incFacility.trim() || incCaseId.trim() || incNotes.trim())) {
          try {
            await api.post(`/members/${created.id}/incarcerations?universe_id=${universeId}`, {
              from_date: incFromDate,
              earliest_release_date: null,
              max_discharge_date: incLife ? null : incMaxDate,
              life_sentence: incLife,
              facility: incFacility.trim() || null,
              case_id: incCaseId.trim() || null,
              notes: incNotes.trim() || null,
            })
            toast.success('Saved incarceration spell')
          } catch (e) {
            toast.error(e instanceof Error ? `Couldn't save incarceration: ${e.message}` : "Couldn't save incarceration")
          }
        }
        if (mdocPending && (mdocPending.earliest_release_date || mdocPending.max_discharge_date || mdocPending.facility)) {
          try {
            await api.post(`/members/${created.id}/incarcerations?universe_id=${universeId}`, {
              from_date: null,
              earliest_release_date: mdocPending.earliest_release_date,
              max_discharge_date: mdocPending.max_discharge_date,
              facility: mdocPending.facility,
              case_id: null,
              notes: null,
            })
            toast.success('Imported MDOC incarceration record')
          } catch (e) {
            toast.error(e instanceof Error ? `Couldn't save MDOC incarceration: ${e.message}` : "Couldn't save MDOC incarceration")
          }
        }
        if (mdocPending?.photo_url) {
          // Use the existing server-side fetch endpoint (avoids CORS on the MDOC URL).
          // Photo lands in the media table; primary-photo selection is handled by the
          // backend (first photo wins) so this still becomes primary if the queue was empty.
          try {
            await mdocImportPhoto.mutateAsync({
              photo_url: mdocPending.photo_url,
              member_id: created.id,
              universe_id: universeId,
            })
            toast.success('Imported MDOC photo')
          } catch (e) {
            toast.error(e instanceof Error ? `Couldn't import MDOC photo: ${e.message}` : "Couldn't import MDOC photo")
          }
        }
        resetForm()
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEdit ? 'update' : 'create'} member`)
    }
  }

  async function handleMdocImport() {
    if (!mdocUrl.trim()) return
    try {
      const profile = await mdocLookup.mutateAsync(mdocUrl.trim())
      if (profile.legal_name) setLegalName(profile.legal_name)
      if (profile.dob) setDob(profile.dob)
      setMdocPending({
        earliest_release_date: profile.earliest_release_date,
        max_discharge_date: profile.max_discharge_date,
        facility: profile.facility,
        photo_url: profile.photo_url,
      })
      if (status === 'UNKNOWN') setStatus('LOCKED')
      toast.success('Imported from MDOC — review and save')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'MDOC import failed'
      toast.error(msg)
    }
  }

  function resetForm() {
    setNickname('')
    setLegalName('')
    setNicknameUnknown(false)
    setStatus('UNKNOWN')
    setAffiliations(defaultSetId ? [{ set_id: defaultSetId, rank: '', is_primary: true }] : [])
    setAllianceId(defaultAllianceId ?? '')
    setGangId('')
    setBiography('')
    setAliases('')
    setFacebook('')
    setInstagram('')
    setTwitter('')
    setDob(null)
    setDateOfDeath(null)
    setFamilyEntries([])
    setError(null)
    setMdocUrl('')
    setMdocPending(null)
    setIncFromDate(null)
    setIncMaxDate(null)
    setIncLife(false)
    setIncFacility('')
    setIncCaseId('')
    setIncNotes('')
    setPhotoQueue([])
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        width="2xl"
        title={isEdit ? 'Edit Member' : 'Add Member'}
        description={isEdit ? 'Update this member' : 'Create a new member profile'}
      >
        <form
          onSubmit={handleSubmit}
          onKeyDown={(e) => {
            // Cmd/Ctrl+Enter submits from anywhere in the form.
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
              e.preventDefault()
              ;(e.currentTarget as HTMLFormElement).requestSubmit()
            }
          }}
          className="-mx-6 -my-4 flex min-h-full flex-col divide-y divide-zinc-800/60"
        >
          <div className="sticky top-0 z-10 -mb-px flex items-center gap-3 border-b border-zinc-800 bg-zinc-950/95 px-6 py-3 backdrop-blur">
            <span className="text-xs uppercase tracking-wider text-zinc-500">Display:</span>
            {identityValid
              ? <span className="truncate text-sm font-medium text-white">{displayPreview}</span>
              : <span className="text-sm italic text-zinc-600">— need a nickname or legal name —</span>}
            <span className="ml-auto"><MemberStatusBadge status={status} /></span>
          </div>
          <div className="flex-1 divide-y divide-zinc-800/60 px-6 pt-4">
          {!isEdit && (
            <FormSection title="Import from MDOC">
              <p className="text-xs text-zinc-500">
                Paste an MDOC OTIS profile URL to prefill legal name, date of birth, and create an incarceration record with the facility and release dates.
              </p>
              <div className="flex gap-2">
                <Input
                  value={mdocUrl}
                  onChange={(e) => setMdocUrl(e.target.value)}
                  placeholder="https://mdocweb.state.mi.us/OTIS2/..."
                  className="flex-1"
                />
                <Button type="button" onClick={handleMdocImport} disabled={!mdocUrl.trim() || mdocLookup.isPending}>
                  {mdocLookup.isPending ? 'Importing…' : 'Import'}
                </Button>
              </div>
              {mdocPending && (
                <p className="text-xs text-emerald-400">
                  Will save on submit:{' '}
                  {mdocPending.facility ?? 'unknown facility'}
                  {mdocPending.earliest_release_date && ' · earliest release set'}
                  {mdocPending.max_discharge_date && ' · max discharge set'}
                  {mdocPending.photo_url && ' · photo'}
                </p>
              )}
            </FormSection>
          )}
          <FormSection title="Identity">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="m-nickname">Nickname</Label>
                  <label htmlFor="m-nku" className="flex cursor-pointer items-center gap-1.5 text-[11px] text-zinc-500 hover:text-zinc-300">
                    <input
                      id="m-nku"
                      type="checkbox"
                      checked={nicknameUnknown}
                      onChange={(e) => setNicknameUnknown(e.target.checked)}
                      className="h-3.5 w-3.5 rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                    />
                    unknown
                  </label>
                </div>
                <Input id="m-nickname" value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="Street name" disabled={nicknameUnknown} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="m-legal">Legal Name</Label>
                <Input id="m-legal" value={legalName} onChange={(e) => setLegalName(e.target.value)} placeholder="Full legal name" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="m-aliases">Aliases <span className="text-zinc-600">(comma-separated)</span></Label>
              <Input id="m-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. Big L, Lucky" />
            </div>
          </FormSection>

          <FormSection title="Photos" hint={isEdit ? 'uploads immediately' : 'queued — first becomes primary'}>
            <PhotoSection
              mode={isEdit ? 'edit' : 'create'}
              universeId={universeId}
              memberId={initial?.id}
              queuedFiles={photoQueue}
              onQueuedFilesChange={setPhotoQueue}
            />
          </FormSection>

          <FormSection title="Status & Affiliation">
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label>Status</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as MemberStatus)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ALL_STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="m-alliance">Alliance</Label>
                <AffiliationCombobox
                  label="Alliance"
                  value={allianceId}
                  onChange={setAllianceId}
                  items={allianceItems}
                  onCreateRequest={handleCreateAlliance}
                  creating={createAlliance.isPending}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="m-gang">Gang</Label>
                <AffiliationCombobox
                  label="Gang"
                  value={gangId}
                  onChange={setGangId}
                  items={gangItems}
                  onCreateRequest={handleCreateGang}
                  creating={createGang.isPending}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label>Sets</Label>
                <button
                  type="button"
                  onClick={() => setAffiliations((prev) => {
                    const isFirst = prev.length === 0
                    return [...prev, { set_id: '', rank: '', is_primary: isFirst }]
                  })}
                  className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
                >
                  + Add
                </button>
              </div>
              {affiliations.length === 0 && (
                <p className="text-xs text-zinc-600 italic">No set affiliation</p>
              )}
              {affiliations.map((aff, idx) => {
                const usedSetIds = new Set(affiliations.filter((_, i) => i !== idx).map((a) => a.set_id).filter(Boolean))
                const availableItems = setItems.filter((s) => !usedSetIds.has(s.id))
                return (
                  <div key={idx} className="flex items-center gap-2">
                    <div className="flex-1">
                      <AffiliationCombobox
                        label="Set"
                        value={aff.set_id}
                        onChange={(v) => setAffiliations((prev) => prev.map((a, i) => i === idx ? { ...a, set_id: v } : a))}
                        items={availableItems}
                        onCreateRequest={handleCreateSet}
                        creating={createSet.isPending}
                      />
                    </div>
                    <Select
                      value={aff.rank || 'none'}
                      onValueChange={(v) => setAffiliations((prev) => prev.map((a, i) => i === idx ? { ...a, rank: v === 'none' ? '' : v as SetRank } : a))}
                      disabled={!aff.set_id}
                    >
                      <SelectTrigger className="w-32 shrink-0 whitespace-nowrap"><SelectValue placeholder="Rank" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="CEO">CEO</SelectItem>
                        <SelectItem value="CO_CEO">Co-CEO</SelectItem>
                      </SelectContent>
                    </Select>
                    <button
                      type="button"
                      title={aff.is_primary ? 'Primary set' : 'Make primary'}
                      onClick={() => setAffiliations((prev) => prev.map((a, i) => ({ ...a, is_primary: i === idx })))}
                      className={`shrink-0 rounded p-1 text-xs transition-colors ${aff.is_primary ? 'text-violet-400' : 'text-zinc-600 hover:text-violet-400'}`}
                    >
                      ★
                    </button>
                    <button
                      type="button"
                      aria-label="Remove affiliation"
                      onClick={() => setAffiliations((prev) => {
                        const next = prev.filter((_, i) => i !== idx)
                        if (aff.is_primary && next.length > 0) next[0].is_primary = true
                        return next
                      })}
                      className="shrink-0 rounded p-1 text-zinc-600 hover:text-red-400 transition-colors"
                    >
                      <X size={12} />
                    </button>
                  </div>
                )
              })}
            </div>
            {status === 'DEAD' && (
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
                <FuzzyDateInput value={dateOfDeath} onChange={setDateOfDeath} label="Date of death" idPrefix="dod" />
                {initial?.death_incident_id && (
                  <p className="mt-2 text-[11px] text-rose-400">
                    Linked to a killing incident — manage the link from the incident page.
                  </p>
                )}
              </div>
            )}
            {status === 'LOCKED' && !isEdit && (
              <div className="space-y-2 rounded-lg border border-orange-900/50 bg-orange-950/10 p-3">
                <div className="flex items-baseline justify-between">
                  <h4 className="text-[11px] font-semibold uppercase tracking-wider text-orange-400">Incarceration spell</h4>
                  <span className="text-[11px] text-zinc-500">created with the member</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <FuzzyDateInput value={incFromDate} onChange={setIncFromDate} label="Lockup date" idPrefix="inc-from" />
                  <FuzzyDateInput value={incMaxDate} onChange={setIncMaxDate} label="Max discharge" idPrefix="inc-max" />
                </div>
                <label htmlFor="inc-life" className="flex cursor-pointer items-center gap-2 text-xs text-zinc-400">
                  <input
                    id="inc-life"
                    type="checkbox"
                    checked={incLife}
                    onChange={(e) => { setIncLife(e.target.checked); if (e.target.checked) setIncMaxDate(null) }}
                    className="h-3.5 w-3.5 rounded border-zinc-700 bg-zinc-900 accent-orange-600"
                  />
                  Life sentence (no max discharge)
                </label>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="inc-facility" className="text-xs">Facility</Label>
                    <Input id="inc-facility" value={incFacility} onChange={(e) => setIncFacility(e.target.value)} placeholder="e.g. MDOC Macomb" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="inc-case" className="text-xs">Case ID</Label>
                    <Input id="inc-case" value={incCaseId} onChange={(e) => setIncCaseId(e.target.value)} placeholder="optional" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="inc-notes" className="text-xs">Notes</Label>
                  <Textarea id="inc-notes" rows={2} value={incNotes} onChange={(e) => setIncNotes(e.target.value)} placeholder="optional" />
                </div>
                <p className="text-[11px] text-zinc-600">
                  Federal sentences typically have only a max discharge — leave the lockup date blank if unknown.
                </p>
              </div>
            )}
            {status === 'LOCKED' && isEdit && (
              <p className="text-xs text-zinc-500">
                Manage the active incarceration spell (release dates, facility) on the
                member's detail page — editing here would risk clobbering an existing record.
              </p>
            )}
          </FormSection>

          <FormSection title="Dates">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
              <FuzzyDateInput value={dob} onChange={setDob} label="Date of birth" idPrefix="dob" />
            </div>
          </FormSection>

          <FormSection title="Social media" hint="handle or URL — normalized on blur">
            <div className="grid gap-3 sm:grid-cols-3">
              <SocialInput
                platform="facebook"
                value={facebook}
                onChange={setFacebook}
                Icon={FacebookIcon}
                label="Facebook"
              />
              <SocialInput
                platform="instagram"
                value={instagram}
                onChange={setInstagram}
                Icon={InstagramIcon}
                label="Instagram"
              />
              <SocialInput
                platform="twitter"
                value={twitter}
                onChange={setTwitter}
                Icon={TwitterIcon}
                label="Twitter / X"
              />
            </div>
          </FormSection>

          <FormSection title="Family" hint="bilateral — inverse links auto-saved">
            <FamilyEditor
              entries={familyEntries}
              onChange={setFamilyEntries}
              universeId={universeId}
              excludeMemberId={initial?.id}
            />
          </FormSection>

          <FormSection title="Biography">
            <div className="space-y-1.5">
              <Label htmlFor="m-bio" className="sr-only">Biography</Label>
              <Textarea
                id="m-bio"
                rows={4}
                value={biography}
                onChange={(e) => setBiography(e.target.value)}
                onPaste={urlPaste.onPaste}
                placeholder="Background notes…"
              />
              <UrlPasteBanner
                url={urlPaste.pastedUrl}
                onSaveAsSource={() => {
                  if (urlPaste.pastedUrl) setCreatingSourceFromUrl(urlPaste.pastedUrl)
                  urlPaste.dismiss()
                }}
                onDismiss={urlPaste.dismiss}
              />
            </div>
          </FormSection>

          </div>
          <div className="sticky bottom-0 z-10 border-t border-zinc-800 bg-zinc-950/95 px-6 py-3 backdrop-blur">
            {error && <p className="mb-2 text-sm text-red-400">{error}</p>}
            {!identityValid && !error && (
              <p className="mb-2 text-xs text-amber-400" aria-live="polite">
                Provide a nickname or legal name to enable saving.
              </p>
            )}
            <div className="flex items-center gap-2">
              <SheetClose asChild>
                <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
              </SheetClose>
              <span className="ml-auto hidden text-[11px] text-zinc-600 sm:inline">⌘/Ctrl + Enter to save</span>
              <Button
                type="submit"
                disabled={isPending || !identityValid}
                title={!identityValid ? 'Provide a nickname or legal name' : undefined}
              >
                {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Member'}
              </Button>
            </div>
          </div>
        </form>
      </SheetContent>
      {creatingSourceFromUrl && (
        <SourceFormSheet
          universeId={universeId}
          open
          onClose={() => setCreatingSourceFromUrl(null)}
          defaultUrl={creatingSourceFromUrl}
        />
      )}
    </Sheet>
  )
}

// ─── Quick-edit sheet ─────────────────────────────────────────────────────────

export function EditMemberSheet({ memberId, universeId, onClose }: { memberId: string; universeId: string; onClose: () => void }) {
  const { data: member, isLoading } = useMember(memberId, universeId)

  if (isLoading) {
    return (
      <Sheet open onOpenChange={(v) => !v && onClose()}>
        <SheetContent title="Edit Member" description="Loading…">
          <div className="space-y-3 pt-2">
            {Array.from({ length: 7 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full rounded-md" />
            ))}
          </div>
        </SheetContent>
      </Sheet>
    )
  }

  if (!member) return null
  return <MemberFormSheet universeId={universeId} open onClose={onClose} initial={member} />
}
