import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { CheckCircle2, MapPin, Pencil, Plus, Trash2, User } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { ErrorState } from '@/components/ErrorState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { CopyButton } from '@/components/CopyButton'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useIncident, useAllMembers, useDeleteIncident, useMunicipality } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { IncidentFormSheet } from './_app.incidents.index'
import { MemberFormSheet } from './_app.members.index'
import { AddParticipantToIncidentDialog } from '@/components/AddParticipantToIncidentDialog'
import { INCIDENT_TYPE_CHIP, ROLE_CHIP, OUTCOME_CHIP, OUTCOME_LABEL, ROLE_LABEL } from '@/lib/incidentColors'
import { useRecordRecent } from '@/stores/recents'
import { useEditShortcut } from '@/hooks/useKeymap'

export const Route = createFileRoute('/_app/incidents/$id')({
  component: IncidentDetailPage,
})

function IncidentDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const { data: incident, isLoading, isError, refetch } = useIncident(id, universe?.id ?? null)
  const { data: allMembers } = useAllMembers(universe?.id ?? null)
  const { data: municipality } = useMunicipality(
    incident?.municipality_id ?? '',
    incident?.municipality_id ? (universe?.id ?? null) : null,
  )
  const deleteIncident = useDeleteIncident(universe?.id ?? '')

  useRecordRecent(
    incident
      ? {
          type: 'incident',
          id: incident.id,
          slug: null,
          label: `${incident.type}${incident.date?.year ? ` · ${incident.date.year}` : ''}`,
        }
      : null,
  )

  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [addingParticipant, setAddingParticipant] = useState(false)
  const [creatingMember, setCreatingMember] = useState(false)

  useEditShortcut(() => incident && setEditing(true))

  const memberMap = Object.fromEntries((allMembers?.items ?? []).map((m) => [m.id, m]))
  const memberName = (mid: string) => memberMap[mid]?.display_name ?? null
  const memberSlug = (mid: string) => memberMap[mid]?.slug ?? mid

  // Pick the most common set among current participants for the "Create new" prefill.
  const defaultSetIdForNewMember = (() => {
    if (!incident) return undefined
    const counts: Record<string, number> = {}
    for (const p of incident.participants) {
      const sid = memberMap[p.member_id]?.set_id
      if (sid) counts[sid] = (counts[sid] ?? 0) + 1
    }
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]
    return top?.[0]
  })()

  async function handleDelete() {
    if (!incident) return
    try {
      await deleteIncident.mutateAsync(incident.id)
      navigate({ to: '/incidents' })
    } catch {
      setDeleting(false)
    }
  }

  if (isError) return <ErrorState title="Incident not found" onRetry={() => refetch()} />

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Incidents', to: '/incidents' },
          { label: incident ? incident.type : 'Incident' },
        ]}
      />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : incident ? (
        <>
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Badge className={`border ${INCIDENT_TYPE_CHIP[incident.type]} text-sm font-semibold px-2.5 py-0.5`}>
                  {incident.type}
                </Badge>
                {incident.verified && (
                  <Badge className="border border-emerald-800/70 bg-emerald-950/30 text-emerald-300">
                    <CheckCircle2 className="mr-1 h-3 w-3" /> Verified
                  </Badge>
                )}
                <CopyButton value={window.location.href} label="Copy link to this incident" className="opacity-60 hover:opacity-100" />
              </div>
              <p className="mt-2 text-sm text-zinc-400">
                <FuzzyDate value={incident.date} fallback="Date unknown" />
                {municipality && (
                  <>
                    {' · '}
                    <Link
                      to="/municipalities/$id"
                      params={{ id: municipality.id }}
                      className="inline-flex items-center gap-1 text-zinc-300 hover:text-violet-400 transition-colors"
                    >
                      <MapPin className="h-3 w-3" />
                      {municipality.name}
                    </Link>
                  </>
                )}
                {incident.location_text && !municipality && <> · {incident.location_text}</>}
              </p>
              {incident.location_text && municipality && (
                <p className="mt-1 text-xs text-zinc-500">{incident.location_text}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
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

          <Tabs defaultValue="participants">
            <TabsList>
              <TabsTrigger value="participants">
                Participants
                {incident.participants.length > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0">{incident.participants.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="narrative">Narrative</TabsTrigger>
            </TabsList>

            <TabsContent value="participants">
              <div className="mb-3 flex justify-end">
                <Button size="sm" variant="outline" onClick={() => setAddingParticipant(true)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />Add Participant
                </Button>
              </div>
              {incident.participants.length === 0 ? (
                <p className="text-sm text-zinc-600">No participants recorded.</p>
              ) : (
                <div className="space-y-2">
                  {incident.participants.map((p) => {
                    const name = memberName(p.member_id)
                    return (
                      <div
                        key={p.member_id}
                        className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3"
                      >
                        {name ? (
                          <Link
                            to="/members/$id"
                            params={{ id: memberSlug(p.member_id) }}
                            className="inline-flex items-center gap-2 text-sm font-medium text-white hover:text-violet-400 transition-colors"
                          >
                            <User className="h-3.5 w-3.5 text-zinc-500" />
                            {name}
                          </Link>
                        ) : (
                          <span className="inline-flex items-center gap-2 text-sm font-medium text-zinc-500">
                            <User className="h-3.5 w-3.5" />
                            Unknown member
                            <span className="font-mono text-xs text-zinc-600">({p.member_id.slice(0, 8)}…)</span>
                          </span>
                        )}
                        <div className="flex items-center gap-2">
                          <Badge className={`border ${ROLE_CHIP[p.role]}`}>{ROLE_LABEL[p.role]}</Badge>
                          <Badge className={`border ${OUTCOME_CHIP[p.outcome]}`}>{OUTCOME_LABEL[p.outcome]}</Badge>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </TabsContent>

            <TabsContent value="narrative">
              {incident.narrative ? (
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                  <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{incident.narrative}</p>
                </div>
              ) : (
                <p className="py-6 text-sm text-zinc-600">No narrative recorded.</p>
              )}
            </TabsContent>
          </Tabs>

          {universe && (
            <IncidentFormSheet
              universeId={universe.id}
              open={editing}
              onClose={() => setEditing(false)}
              initial={incident}
            />
          )}

          {universe && (
            <AddParticipantToIncidentDialog
              incident={incident}
              universeId={universe.id}
              open={addingParticipant}
              onClose={() => setAddingParticipant(false)}
              onCreateNew={() => { setAddingParticipant(false); setCreatingMember(true) }}
            />
          )}

          {universe && (
            <MemberFormSheet
              universeId={universe.id}
              open={creatingMember}
              onClose={() => setCreatingMember(false)}
              defaultSetId={defaultSetIdForNewMember}
            />
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete Incident"
            description={`Permanently delete this ${incident.type.toLowerCase()} incident? This cannot be undone.`}
            impact={incident.participants.length > 0 ? (
              <span>
                <strong>{incident.participants.length}</strong> participant{incident.participants.length === 1 ? '' : 's'} will lose this incident from their timeline.
              </span>
            ) : null}
            confirmLabel="Delete"
            destructive
            pending={deleteIncident.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
