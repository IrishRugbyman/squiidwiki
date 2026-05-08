import { createFileRoute, Link } from '@tanstack/react-router'
import { Download, Pencil, Plus, Search, UserPlus, Users, X } from 'lucide-react'
import { FacebookIcon, InstagramIcon, TwitterIcon } from '@/components/icons/SocialIcons'
import { useMemo, useRef, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { toast } from 'sonner'
import { NoUniverse } from '@/components/NoUniverse'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { FuzzyDateInput } from '@/components/FuzzyDateInput'
import {
  useCreateMember, useMembers, useMemberSearch, useUpdateMember,
  useSets, useAlliances, useBulkMemberStatus, useGangs, useMember, useAllMembers,
  useMdocLookup, useMdocImportPhoto,
} from '@/lib/queries'
import { api } from '@/lib/api'
import { useUniverseStore } from '@/stores/universe'
import { downloadCsv } from '@/lib/download'
import { useDebounce } from '@/hooks/useDebounce'
import { MemberRowSkeleton } from '@/components/skeletons'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { UrlPasteBanner, useUrlPasteBanner } from '@/components/UrlPasteBanner'
import { SourceFormSheet } from './_app.sources.index'
import type { MemberListItem, MemberRead, MemberStatus, SetRank } from '@/lib/types'
import type { FuzzyDateValue } from '@/components/FuzzyDate'

export const Route = createFileRoute('/_app/members/')({
  component: MembersPage,
})

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

const STATUS_CHIP_ACTIVE: Record<MemberStatus, string> = {
  FREE: 'bg-emerald-900/60 text-emerald-300 border-emerald-700',
  LOCKED: 'bg-orange-900/60 text-orange-300 border-orange-700',
  DEAD: 'bg-zinc-800 text-zinc-400 border-zinc-600',
  UNKNOWN: 'bg-zinc-800 text-zinc-400 border-zinc-600',
  ESCAPEE: 'bg-amber-900/60 text-amber-300 border-amber-700',
  ABSCONDER: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
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
  const { data: allMembersData } = useAllMembers(universeId)
  const allMembers = (allMembersData?.items ?? []).filter((m) => m.id !== excludeMemberId)

  const [newRole, setNewRole] = useState<FamilyRole>('brother')
  const [newMemberId, setNewMemberId] = useState('')
  const [memberSearch, setMemberSearch] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)

  const filteredMembers = useMemo(() => {
    if (!memberSearch.trim()) return allMembers.slice(0, 8)
    const q = memberSearch.toLowerCase()
    return allMembers.filter((m) => m.display_name.toLowerCase().includes(q)).slice(0, 8)
  }, [allMembers, memberSearch])

  const selectedMember = allMembers.find((m) => m.id === newMemberId)

  function addEntry() {
    if (!newMemberId) return
    // father is unique — replace
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

  const memberName = (id: string) => allMembers.find((m) => m.id === id)?.display_name ?? id.slice(0, 8) + '…'

  const groupedEntries = FAMILY_ROLES.map((role) => ({
    role,
    entries: entries.filter((e) => e.role === role),
  })).filter((g) => g.entries.length > 0)

  return (
    <div className="space-y-2">
      {/* Current entries — or a placeholder when empty */}
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

      {/* Add new entry */}
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
              placeholder={selectedMember ? selectedMember.display_name : 'Search member by name…'}
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

  const [nickname, setNickname] = useState(initial?.nickname ?? copyFrom?.nickname ?? '')
  const [legalName, setLegalName] = useState(initial?.legal_name ?? copyFrom?.legal_name ?? '')
  const [nicknameUnknown, setNicknameUnknown] = useState(initial?.nickname_unknown ?? copyFrom?.nickname_unknown ?? false)
  const [status, setStatus] = useState<MemberStatus>(initial?.status ?? copyFrom?.status ?? 'UNKNOWN')
  const [setId, setSetId] = useState<string>(initial?.set_id ?? copyFrom?.set_id ?? defaultSetId ?? '')
  const [setRank, setSetRank] = useState<SetRank | ''>(initial?.set_rank ?? copyFrom?.set_rank ?? '')
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
  // Note: family is intentionally NOT copied — entries are bilateral and would create
  // duplicated reverse links on save. User can re-add family on the new record.
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
      set_id: setId || null,
      set_rank: setId && setRank ? setRank : null,
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
    setSetId(defaultSetId ?? '')
    setSetRank('')
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
  }

  const isPending = isEdit ? update.isPending : create.isPending

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        width="2xl"
        title={isEdit ? 'Edit Member' : 'Add Member'}
        description={isEdit ? 'Update this member' : 'Create a new member profile'}
      >
        <form onSubmit={handleSubmit} className="divide-y divide-zinc-800/60">
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
            <p className="text-xs text-zinc-500">
              Will display as:{' '}
              {identityValid
                ? <span className="font-medium text-zinc-200">{displayPreview}</span>
                : <span className="italic text-zinc-600">— need a nickname or legal name —</span>}
            </p>
            <div className="space-y-1.5">
              <Label htmlFor="m-aliases">Aliases <span className="text-zinc-600">(comma-separated)</span></Label>
              <Input id="m-aliases" value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="e.g. Big L, Lucky" />
              <p className="text-xs text-zinc-500">Photos are managed in the member's Photos tab after creation.</p>
            </div>
          </FormSection>

          <FormSection title="Status & Affiliation">
            <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
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
                <Label>Set</Label>
                <Select value={setId || 'none'} onValueChange={(v) => { const next = v === 'none' ? '' : v; setSetId(next); if (!next) setSetRank('') }}>
                  <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">— None —</SelectItem>
                    {(sets?.items ?? []).map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Set rank</Label>
                <Select
                  value={setRank || 'none'}
                  onValueChange={(v) => setSetRank(v === 'none' ? '' : (v as SetRank))}
                  disabled={!setId}
                >
                  <SelectTrigger><SelectValue placeholder={setId ? 'None' : 'Pick a set first'} /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">— None —</SelectItem>
                    <SelectItem value="CEO">CEO</SelectItem>
                    <SelectItem value="CO_CEO">Co-CEO</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Alliance</Label>
                <Select value={allianceId || 'none'} onValueChange={(v) => setAllianceId(v === 'none' ? '' : v)}>
                  <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">— None —</SelectItem>
                    {(alliances?.items ?? []).map((a) => <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Gang</Label>
                <Select value={gangId || 'none'} onValueChange={(v) => setGangId(v === 'none' ? '' : v)}>
                  <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">— None —</SelectItem>
                    {(gangs?.items ?? []).map((g) => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
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
            {status === 'LOCKED' && (
              <p className="text-xs text-zinc-500">
                Add release dates (earliest / max discharge / life sentence) on the
                member detail page after saving — they live on the incarceration spell.
              </p>
            )}
          </FormSection>

          <FormSection title="Dates">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
              <FuzzyDateInput value={dob} onChange={setDob} label="Date of birth" idPrefix="dob" />
            </div>
          </FormSection>

          <FormSection title="Social media" hint="handle or URL">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex items-center gap-2">
                <FacebookIcon className="h-4 w-4 shrink-0 text-zinc-500" />
                <Input value={facebook} onChange={(e) => setFacebook(e.target.value)} placeholder="Facebook" aria-label="Facebook" />
              </div>
              <div className="flex items-center gap-2">
                <InstagramIcon className="h-4 w-4 shrink-0 text-zinc-500" />
                <Input value={instagram} onChange={(e) => setInstagram(e.target.value)} placeholder="Instagram" aria-label="Instagram" />
              </div>
              <div className="flex items-center gap-2">
                <TwitterIcon className="h-4 w-4 shrink-0 text-zinc-500" />
                <Input value={twitter} onChange={(e) => setTwitter(e.target.value)} placeholder="Twitter / X" aria-label="Twitter / X" />
              </div>
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

          {error && <p className="pt-4 text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-5">
            <Button
              type="submit"
              disabled={isPending || !identityValid}
              title={!identityValid ? 'Provide a nickname or legal name' : undefined}
              className="flex-1"
            >
              {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Member'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </SheetClose>
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

function EditMemberSheet({ memberId, universeId, onClose }: { memberId: string; universeId: string; onClose: () => void }) {
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

// ─── Main page ────────────────────────────────────────────────────────────────

function MembersPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)
  const [editingMemberId, setEditingMemberId] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkStatus, setBulkStatus] = useState<MemberStatus>('FREE')
  const [statusFilter, setStatusFilter] = useState<MemberStatus | null>(null)
  const [setFilter, setSetFilter] = useState<string>('')
  const [sortKey, setSortKey] = useState<'display_name' | 'status' | null>('display_name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const bulkUpdate = useBulkMemberStatus(universe?.id ?? '')

  const debouncedQ = useDebounce(q, 250)
  const { data, isLoading } = useMembers(universe?.id ?? null, cursor)
  const { data: searchResults, isLoading: searchLoading } = useMemberSearch(universe?.id ?? null, debouncedQ)
  const { data: setsData } = useSets(universe?.id ?? null)

  const setMap = useMemo(() => {
    const m: Record<string, { name: string; slug: string | null }> = {}
    for (const s of setsData?.items ?? []) m[s.id] = { name: s.name, slug: s.slug }
    return m
  }, [setsData])

  const isSearching = debouncedQ.length >= 2
  const baseItems = isSearching ? (searchResults ?? []) : (data?.items ?? [])

  const statusCounts = useMemo(() => {
    const counts: Partial<Record<MemberStatus, number>> = {}
    for (const m of baseItems) counts[m.status] = (counts[m.status] ?? 0) + 1
    return counts
  }, [baseItems])

  const items: MemberListItem[] = useMemo(() => {
    let list = baseItems
    if (statusFilter) list = list.filter((m) => m.status === statusFilter)
    if (setFilter) list = list.filter((m) => m.set_id === setFilter)
    if (!sortKey) return list
    return [...list].sort((a, b) => {
      const av = String((a as unknown as Record<string, unknown>)[sortKey] ?? '')
      const bv = String((b as unknown as Record<string, unknown>)[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
  }, [baseItems, statusFilter, setFilter, sortKey, sortDir])

  // Virtualize the desktop table tbody when the list grows past 50 rows.
  const tableScrollRef = useRef<HTMLDivElement | null>(null)
  const isVirtualized = items.length > 50
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 56,
    overscan: 8,
  })
  const virtualRows = isVirtualized ? rowVirtualizer.getVirtualItems() : []
  const virtualPaddingTop = virtualRows[0]?.start ?? 0
  const virtualPaddingBottom = isVirtualized
    ? rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)
    : 0

  if (!universe) return <NoUniverse />

  const total = data?.total
  const listLoading = isSearching ? searchLoading : isLoading

  function toggleSort(key: 'display_name' | 'status') {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    setSelected(selected.size === items.length ? new Set() : new Set(items.map((m) => m.id)))
  }

  async function applyBulkStatus() {
    if (selected.size === 0) return
    const count = selected.size
    try {
      await bulkUpdate.mutateAsync({ member_ids: Array.from(selected), status: bulkStatus })
      toast.success(`Updated ${count} member${count === 1 ? '' : 's'} to ${bulkStatus}`)
      setSelected(new Set())
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Bulk update failed')
    }
  }

  const hasFilters = statusFilter || setFilter
  const hasSelection = selected.size > 0
  const universeSlug = universe.slug

  function exportFilename() {
    const date = new Date().toISOString().slice(0, 10)
    return `members-${universeSlug}-${date}.csv`
  }

  return (
    <div className={hasSelection ? 'pb-28' : 'pb-20'}>
      {/* Header */}
      <div className="mb-5 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Members</h1>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500">
            {total != null && <span>{total} total</span>}
            {(statusCounts.FREE ?? 0) > 0 && <span className="text-emerald-500">{statusCounts.FREE} free</span>}
            {(statusCounts.LOCKED ?? 0) > 0 && <span className="text-orange-400">{statusCounts.LOCKED} locked</span>}
            {(statusCounts.DEAD ?? 0) > 0 && <span>{statusCounts.DEAD} dead</span>}
            {(statusCounts.ESCAPEE ?? 0) > 0 && <span className="text-amber-400">{statusCounts.ESCAPEE} escaped</span>}
          </div>
        </div>
        <Button size="sm" onClick={() => setCreating(true)}>
          <Plus className="mr-1.5 h-4 w-4" />Add Member
        </Button>
      </div>

      {/* Status filter chips */}
      {!isLoading && baseItems.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-1.5">
          {ALL_STATUSES.filter((s) => (statusCounts[s] ?? 0) > 0).map((s) => {
            const active = statusFilter === s
            return (
              <button
                key={s}
                onClick={() => setStatusFilter(active ? null : s)}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all ${
                  active ? STATUS_CHIP_ACTIVE[s] : 'border-zinc-800 bg-zinc-900/40 text-zinc-500 hover:border-zinc-700 hover:text-zinc-300'
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[s]}`} />
                {s}
                <span className={active ? 'opacity-70' : 'opacity-50'}>{statusCounts[s]}</span>
              </button>
            )
          })}
          {hasFilters && (
            <button
              onClick={() => { setStatusFilter(null); setSetFilter('') }}
              className="flex items-center gap-1 rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-500 hover:text-white transition-colors"
            >
              <X className="h-3 w-3" /> Clear filters
            </button>
          )}
        </div>
      )}

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8 h-8 text-sm" placeholder="Search members…" value={q} onChange={(e) => { setQ(e.target.value); setCursor(undefined) }} />
        </div>
        <Select value={setFilter || 'all'} onValueChange={(v) => setSetFilter(v === 'all' ? '' : v)}>
          <SelectTrigger className="h-8 w-36 text-xs"><SelectValue placeholder="All sets" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all" className="text-xs">All sets</SelectItem>
            {(setsData?.items ?? []).map((s) => (
              <SelectItem key={s.id} value={s.id} className="text-xs">{s.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline" size="sm" className="h-8" onClick={() => downloadCsv(`/members/?universe_id=${universe.id}&format=csv`, exportFilename())}>
          <Download className="mr-1.5 h-3.5 w-3.5" />Export
        </Button>
      </div>

      {/* Table — hidden on narrow viewports */}
      <div
        ref={tableScrollRef}
        className="hidden rounded-lg border border-zinc-800 sm:block"
        style={isVirtualized
          ? { maxHeight: 'calc(100vh - 18rem)', overflowY: 'auto' }
          : { overflow: 'hidden' }}
      >
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-zinc-800 bg-zinc-900/90 backdrop-blur">
              <th className="w-10 px-3 py-2.5" scope="col">
                <input
                  id="members-select-all"
                  type="checkbox"
                  aria-label="Select all members"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={toggleAll}
                  className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                />
              </th>
              <th className="px-3 py-2.5 w-8" scope="col" aria-label="Avatar" />
              <th className="px-3 py-2.5 text-left" scope="col" aria-sort={sortKey === 'display_name' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <button onClick={() => toggleSort('display_name')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white">
                  Name <span className="text-zinc-600" aria-hidden>{sortKey === 'display_name' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
              <th className="hidden px-3 py-2.5 text-left sm:table-cell" scope="col">
                <span className="text-xs font-medium text-zinc-400">Set</span>
              </th>
              <th className="px-3 py-2.5 text-left" scope="col" aria-sort={sortKey === 'status' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <button onClick={() => toggleSort('status')} className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white">
                  Status <span className="text-zinc-600" aria-hidden>{sortKey === 'status' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
                </button>
              </th>
              <th className="w-8 px-3 py-2.5" scope="col" aria-label="Actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {listLoading
              ? Array.from({ length: 8 }).map((_, i) => <MemberRowSkeleton key={i} />)
              : isVirtualized && virtualPaddingTop > 0
                ? <tr aria-hidden><td colSpan={6} style={{ height: virtualPaddingTop }} /></tr>
                : null}
            {!listLoading && (isVirtualized ? virtualRows.map((vRow) => items[vRow.index]) : items).map((member, idx) => {
                  const linkId = member.slug ?? member.id
                  const setInfo = member.set_id ? setMap[member.set_id] : null
                  const isDead = member.status === 'DEAD'
                  const measureRef = isVirtualized ? rowVirtualizer.measureElement : undefined
                  const dataIndex = isVirtualized ? virtualRows[idx]?.index : undefined
                  return (
                    <tr key={member.id} ref={measureRef} data-index={dataIndex} className={`group transition-colors hover:bg-zinc-900/40 ${selected.has(member.id) ? 'bg-violet-950/20' : ''} ${isDead ? 'opacity-60' : ''}`}>
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          aria-label={`Select ${member.display_name}`}
                          checked={selected.has(member.id)}
                          onChange={() => toggleSelect(member.id)}
                          className="rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                        />
                      </td>
                      <td className="px-3 py-3"><MemberAvatar member={member} /></td>
                      <td className="p-0">
                        <Link to="/members/$id" params={{ id: linkId }} className="block px-3 py-3 transition-colors group-hover:text-violet-400">
                          <span className={`font-medium ${isDead ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'}`}>{member.display_name}</span>
                          {member.aliases && member.aliases.length > 0 && (
                            <span className="mt-0.5 block text-[11px] text-zinc-600 group-hover:text-zinc-500 transition-colors">
                              {member.aliases.slice(0, 3).join(' · ')}
                            </span>
                          )}
                        </Link>
                      </td>
                      <td className="hidden px-3 py-3 sm:table-cell">
                        {setInfo ? (
                          <Link to="/sets/$id" params={{ id: setInfo.slug ?? member.set_id! }} className="inline-flex items-center rounded-full bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors">
                            {setInfo.name}
                          </Link>
                        ) : <span className="text-xs text-zinc-700">—</span>}
                      </td>
                      <td className="px-3 py-3">
                        <MemberStatusBadge status={member.status} />
                      </td>
                      <td className="px-3 py-3">
                        <button
                          type="button"
                          aria-label={`Edit ${member.display_name}`}
                          onClick={(e) => { e.preventDefault(); e.stopPropagation(); setEditingMemberId(member.id) }}
                          className="rounded p-1.5 text-zinc-600 transition-colors hover:bg-zinc-800 hover:text-violet-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
            {!listLoading && isVirtualized && virtualPaddingBottom > 0 && (
              <tr aria-hidden><td colSpan={6} style={{ height: virtualPaddingBottom }} /></tr>
            )}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <div className="flex flex-col items-center py-14 text-center">
                    <Users className="mb-3 h-8 w-8 text-zinc-700" />
                    <p className="text-sm text-zinc-500">
                      {q ? 'No members match your search' : hasFilters ? 'No members match these filters' : 'No members yet'}
                    </p>
                    {!q && !hasFilters && (
                      <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Add the first member →</button>
                    )}
                    {hasFilters && (
                      <button onClick={() => { setStatusFilter(null); setSetFilter('') }} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Clear filters</button>
                    )}
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards — shown below sm */}
      <div className="space-y-2 sm:hidden">
        {listLoading ? (
          Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-lg" />)
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center rounded-lg border border-zinc-800 py-12 text-center">
            <Users className="mb-3 h-8 w-8 text-zinc-700" />
            <p className="text-sm text-zinc-500">
              {q ? 'No members match your search' : hasFilters ? 'No members match these filters' : 'No members yet'}
            </p>
            {!q && !hasFilters && (
              <button onClick={() => setCreating(true)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Add the first member →</button>
            )}
            {hasFilters && (
              <button onClick={() => { setStatusFilter(null); setSetFilter('') }} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">Clear filters</button>
            )}
          </div>
        ) : (
          items.map((member) => {
            const linkId = member.slug ?? member.id
            const setInfo = member.set_id ? setMap[member.set_id] : null
            const isDead = member.status === 'DEAD'
            const isSelected = selected.has(member.id)
            return (
              <div
                key={member.id}
                className={`relative rounded-lg border bg-zinc-900/30 p-3 ${
                  isSelected ? 'border-violet-700 bg-violet-950/20' : 'border-zinc-800'
                } ${isDead ? 'opacity-60' : ''}`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    aria-label={`Select ${member.display_name}`}
                    checked={isSelected}
                    onChange={() => toggleSelect(member.id)}
                    className="mt-1 rounded border-zinc-700 bg-zinc-900 accent-violet-600"
                  />
                  <MemberAvatar member={member} />
                  <div className="min-w-0 flex-1">
                    <Link
                      to="/members/$id"
                      params={{ id: linkId }}
                      className="block"
                    >
                      <span className={`font-medium ${isDead ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'}`}>
                        {member.display_name}
                      </span>
                      {member.aliases && member.aliases.length > 0 && (
                        <span className="mt-0.5 block text-[11px] text-zinc-600">
                          {member.aliases.slice(0, 3).join(' · ')}
                        </span>
                      )}
                    </Link>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <MemberStatusBadge status={member.status} />
                      {setInfo && (
                        <Link
                          to="/sets/$id"
                          params={{ id: setInfo.slug ?? member.set_id! }}
                          className="inline-flex items-center rounded-full bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors"
                        >
                          {setInfo.name}
                        </Link>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    aria-label={`Edit ${member.display_name}`}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); setEditingMemberId(member.id) }}
                    className="rounded p-1.5 text-zinc-600 transition-colors hover:bg-zinc-800 hover:text-violet-400"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Load more */}
      {!q && data?.next_cursor && (
        <div className="mt-4 flex items-center justify-between text-xs text-zinc-500">
          {total != null && items.length > 0 && <span>Showing {items.length} of {total}</span>}
          <Button variant="outline" size="sm" onClick={() => setCursor(data.next_cursor ?? undefined)}>Load more</Button>
        </div>
      )}

      {/* Bulk action bar */}
      {selected.size > 0 && (
        <div
          className="fixed left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-2.5 shadow-2xl shadow-black/50"
          style={{ bottom: 'max(1.5rem, env(safe-area-inset-bottom))' }}
          role="region"
          aria-label="Bulk actions for selected members"
        >
          <span className="text-sm font-medium text-white">{selected.size} selected</span>
          <div className="h-4 w-px bg-zinc-700" />
          <span className="text-xs text-zinc-500">Set status:</span>
          <Select value={bulkStatus} onValueChange={(v) => setBulkStatus(v as MemberStatus)}>
            <SelectTrigger className="h-7 w-28 text-xs border-zinc-700 bg-zinc-800"><SelectValue /></SelectTrigger>
            <SelectContent>
              {ALL_STATUSES.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button size="sm" className="h-7 text-xs" onClick={applyBulkStatus} disabled={bulkUpdate.isPending}>
            {bulkUpdate.isPending ? 'Applying…' : 'Apply'}
          </Button>
          <button onClick={() => setSelected(new Set())} className="text-zinc-500 hover:text-white transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <MemberFormSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
      {editingMemberId && (
        <EditMemberSheet memberId={editingMemberId} universeId={universe.id} onClose={() => setEditingMemberId(null)} />
      )}
    </div>
  )
}
