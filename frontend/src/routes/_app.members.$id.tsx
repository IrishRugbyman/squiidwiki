import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import {
  ArrowLeft, CheckCircle2, ExternalLink, Heart,
  Pencil, Skull, Trash2,
} from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { MemberIdentity } from '@/components/MemberIdentity'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  useMember, useMemberStats, useSets, useAlliances,
  useDeleteMember, useMemberIncidents,
} from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { MemberFormSheet, familyDictToEntries, ROLE_LABEL } from './_app.members.index'
import type { FamilyRole } from './_app.members.index'

export const Route = createFileRoute('/_app/members/$id')({
  component: MemberDetailPage,
})

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatPill({ label, value, accent = 'text-white' }: { label: string; value: number; accent?: string }) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <span className={`text-2xl font-bold tabular-nums ${accent}`}>{value}</span>
      <span className="mt-0.5 text-[11px] text-zinc-500">{label}</span>
    </div>
  )
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-4 border-b border-zinc-800/50 py-2.5 last:border-0">
      <span className="w-32 shrink-0 text-xs text-zinc-500">{label}</span>
      <span className="text-sm text-zinc-200">{children}</span>
    </div>
  )
}

// ─── Family member inline link ─────────────────────────────────────────────────

function FamilyMemberLink({ memberId, universeId }: { memberId: string; universeId: string }) {
  const { data: m } = useMember(memberId, universeId)
  if (!m) {
    return <span className="text-xs text-zinc-600 font-mono">{memberId.slice(0, 8)}…</span>
  }
  return (
    <Link
      to="/members/$id"
      params={{ id: m.slug ?? m.id }}
      className="group inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2 transition-colors hover:border-zinc-700 hover:bg-zinc-900"
    >
      {m.photo_url ? (
        <img src={m.photo_url} alt={m.display_name} className="h-6 w-6 rounded-full object-cover ring-1 ring-zinc-700" />
      ) : (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-800 text-[9px] font-bold text-zinc-400">
          {m.display_name.slice(0, 2).toUpperCase()}
        </div>
      )}
      <span className="text-sm text-zinc-300 group-hover:text-white">{m.display_name}</span>
      <MemberStatusBadge status={m.status} />
    </Link>
  )
}

// ─── Family tab content ────────────────────────────────────────────────────────

const ROLE_COLOR: Record<FamilyRole, string> = {
  father: 'text-amber-400',
  son: 'text-sky-400',
  brother: 'text-violet-400',
  cousin: 'text-emerald-400',
  uncle: 'text-orange-400',
  nephew: 'text-pink-400',
}

function FamilyTab({ family, universeId }: { family: Record<string, unknown> | null; universeId: string }) {
  const entries = familyDictToEntries(family)
  const grouped = (['father', 'son', 'brother', 'cousin', 'uncle', 'nephew'] as FamilyRole[])
    .map((role) => ({ role, ids: entries.filter((e) => e.role === role).map((e) => e.memberId) }))
    .filter((g) => g.ids.length > 0)

  if (grouped.length === 0) {
    return <p className="py-6 text-sm text-zinc-600">No family links recorded.</p>
  }

  return (
    <div className="space-y-5">
      {grouped.map(({ role, ids }) => (
        <div key={role}>
          <div className="mb-2 flex items-center gap-2">
            <Heart className={`h-3 w-3 ${ROLE_COLOR[role]}`} />
            <span className={`text-xs font-semibold uppercase tracking-wider ${ROLE_COLOR[role]}`}>
              {ROLE_LABEL[role]}{ids.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {ids.map((id) => (
              <FamilyMemberLink key={id} memberId={id} universeId={universeId} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function MemberDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: member, isLoading, isError, refetch } = useMember(id, universe?.id ?? null)
  const { data: stats } = useMemberStats(id, universe?.id ?? null)
  const { data: allSets } = useSets(universe?.id ?? null)
  const { data: allAlliances } = useAlliances(universe?.id ?? null)
  const { data: incidents } = useMemberIncidents(id, universe?.id ?? null)

  const deleteMember = useDeleteMember(universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const setName = (sid: string) => allSets?.items.find((s) => s.id === sid)?.name ?? sid
  const setSlug = (sid: string) => allSets?.items.find((s) => s.id === sid)?.slug ?? sid
  const allianceName = (aid: string) => allAlliances?.items.find((a) => a.id === aid)?.name ?? aid

  async function handleDelete() {
    if (!member) return
    try {
      await deleteMember.mutateAsync(member.id)
      navigate({ to: '/members' })
    } catch {
      setDeleting(false)
    }
  }

  const familyCount = member?.family ? familyDictToEntries(member.family as Record<string, unknown>).length : 0

  if (isError) return <ErrorState title="Member not found" onRetry={() => refetch()} />

  return (
    <div className="space-y-5">
      <Link to="/members" className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Members
      </Link>

      {isLoading ? (
        <div className="space-y-3">
          <div className="flex items-start gap-4">
            <Skeleton className="h-20 w-20 rounded-xl" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-7 w-40" />
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          </div>
        </div>
      ) : member ? (
        <>
          {/* Hero header */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="shrink-0">
                {member.photo_url ? (
                  <img
                    src={member.photo_url}
                    alt={member.display_name}
                    className="h-20 w-20 rounded-xl object-cover ring-2 ring-zinc-700"
                  />
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-zinc-800 text-2xl font-bold text-zinc-400">
                    {member.display_name.slice(0, 2).toUpperCase()}
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <MemberIdentity member={member} showLegalName className="text-2xl font-bold" secondaryClassName="text-base mt-0.5" />
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <MemberStatusBadge status={member.status} />
                  {member.aliases && member.aliases.length > 0 && (
                    <span className="text-xs text-zinc-500">a.k.a. {member.aliases.join(', ')}</span>
                  )}
                </div>
                {(member.set_id || member.alliance_id) && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {member.set_id && (
                      <Link
                        to="/sets/$id"
                        params={{ id: setSlug(member.set_id) }}
                        className="rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-violet-400 transition-colors"
                      >
                        {setName(member.set_id)}
                      </Link>
                    )}
                    {member.alliance_id && (
                      <Link
                        to="/alliances/$id"
                        params={{ id: member.alliance_id }}
                        className="rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-blue-400 transition-colors"
                      >
                        {allianceName(member.alliance_id)}
                      </Link>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
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

          {/* Stats row */}
          {stats && (
            <div className="grid grid-cols-4 gap-2">
              <StatPill label="Shootings" value={stats.shootings} accent="text-amber-400" />
              <StatPill label="Assists" value={stats.assists} accent="text-violet-400" />
              <StatPill label="Kills" value={stats.kills} accent="text-rose-400" />
              <StatPill label="Survived" value={stats.times_shot_survived} accent="text-emerald-400" />
            </div>
          )}

          {/* Tabs */}
          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="biography">Bio</TabsTrigger>
              <TabsTrigger value="family">
                Family
                {familyCount > 0 && (
                  <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-xs">{familyCount}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="incidents">
                Incidents
                {incidents && incidents.items.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-xs">{incidents.items.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            {/* Overview */}
            <TabsContent value="overview" className="mt-4 space-y-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-1">
                <DetailRow label="Date of Birth">
                  {member.dob ? <FuzzyDate value={member.dob} /> : <span className="text-zinc-600">Unknown</span>}
                </DetailRow>
                {member.status === 'DEAD' && (
                  <DetailRow label="Date of Death">
                    <span className="flex items-center gap-2">
                      <Skull className="h-3 w-3 text-zinc-500" />
                      {member.date_of_death ? <FuzzyDate value={member.date_of_death} /> : <span className="text-zinc-600">Unknown</span>}
                    </span>
                  </DetailRow>
                )}
                {member.status === 'LOCKED' && member.release_date && (
                  <DetailRow label="Release Date">
                    <FuzzyDate value={member.release_date} />
                  </DetailRow>
                )}
                <DetailRow label="Set">
                  {member.set_id ? (
                    <Link to="/sets/$id" params={{ id: setSlug(member.set_id) }} className="text-violet-400 hover:underline">
                      {setName(member.set_id)}
                    </Link>
                  ) : <span className="text-zinc-600">—</span>}
                </DetailRow>
                <DetailRow label="Alliance">
                  {member.alliance_id ? (
                    <Link to="/alliances/$id" params={{ id: member.alliance_id }} className="text-blue-400 hover:underline">
                      {allianceName(member.alliance_id)}
                    </Link>
                  ) : <span className="text-zinc-600">—</span>}
                </DetailRow>
              </div>

              {/* Social media */}
              {member.social_media && Object.keys(member.social_media).length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 px-4 py-2">
                  {Object.entries(member.social_media).map(([platform, handle]) => (
                    <DetailRow key={platform} label={platform}>
                      {String(handle).startsWith('http') ? (
                        <a href={String(handle)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sky-400 hover:underline">
                          {String(handle)}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="text-zinc-300">{String(handle)}</span>
                      )}
                    </DetailRow>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Biography */}
            <TabsContent value="biography" className="mt-4">
              {member.biography ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
                  <p className="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap">{member.biography}</p>
                </div>
              ) : (
                <p className="py-6 text-sm text-zinc-600">No biography recorded.</p>
              )}
            </TabsContent>

            {/* Family */}
            <TabsContent value="family" className="mt-4">
              {universe && (
                <FamilyTab family={member.family as Record<string, unknown> | null} universeId={universe.id} />
              )}
            </TabsContent>

            {/* Incidents */}
            <TabsContent value="incidents" className="mt-4">
              {!incidents || incidents.items.length === 0 ? (
                <p className="py-6 text-sm text-zinc-600">No incidents recorded.</p>
              ) : (
                <div className="overflow-hidden rounded-xl border border-zinc-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/50">
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Date</th>
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Type</th>
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Victims</th>
                        <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Verified</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {incidents.items.map((inc) => (
                        <tr key={inc.id} className="hover:bg-zinc-900/50 transition-colors">
                          <td className="p-0">
                            <Link to="/incidents/$id" params={{ id: inc.id }} className="block px-4 py-3 text-zinc-300 hover:text-violet-400">
                              {inc.date ? <FuzzyDate value={inc.date} /> : '—'}
                            </Link>
                          </td>
                          <td className="px-4 py-3">
                            <Badge
                              variant="outline"
                              className={`text-xs ${inc.type === 'MURDER' ? 'border-rose-800 text-rose-400' : 'border-amber-800 text-amber-400'}`}
                            >
                              {inc.type}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-xs text-zinc-500">
                            {inc.victim_names.length > 0 ? inc.victim_names.join(', ') : '—'}
                          </td>
                          <td className="px-4 py-3">
                            {inc.verified
                              ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                              : <span className="text-zinc-600 text-xs">—</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>
          </Tabs>

          {universe && (
            <MemberFormSheet universeId={universe.id} open={editing} onClose={() => setEditing(false)} initial={member} />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Member"
            description={`Permanently delete "${member.display_name}"? This cannot be undone.`}
            confirmLabel="Delete"
            destructive
            pending={deleteMember.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
