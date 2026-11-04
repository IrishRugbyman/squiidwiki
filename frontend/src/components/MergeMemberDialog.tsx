import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { ArrowLeftRight, GitMerge } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { useDebounce } from '@/hooks/useDebounce'
import { useMemberSearch, useMergeMembers, useSimilarMembers } from '@/lib/queries'
import type { MemberMergeReport, MemberRead, UUID } from '@/lib/types'

const FIELD_LABEL: Record<string, string> = {
  nickname: 'Nickname',
  legal_name: 'Legal name',
  nickname_unknown: 'Nickname unknown',
  biography: 'Biography',
  status: 'Status',
  dob: 'Date of birth',
  date_of_death: 'Date of death',
  death_incident_id: 'Death incident',
  mdoc_number: 'MDOC number',
  bop_register_number: 'BOP register number',
  alliance_id: 'Alliance',
  gang_id: 'Gang',
}

const MOVED_LABEL: Record<string, string> = {
  incident_participations: 'incident participations',
  set_spells: 'set spells',
  citations: 'source citations',
  businesses: 'business links',
  rap_groups: 'rap group memberships',
  note_pins: 'research note pins',
  court_cases: 'court case defendant rows',
  photo_tags: 'photo tags',
  aliases: 'alias records',
  incarcerations: 'incarceration records',
  custody_ids: 'custody numbers',
  photos: 'photos',
  sets_founded: 'sets founded',
  alliances_founded: 'alliances founded',
  family_links_repointed: "relatives' family links",
}

function isFuzzy(v: unknown): v is FuzzyDateValue {
  return !!v && typeof v === 'object' && 'precision' in (v as object)
}

function Val({ v }: { v: unknown }) {
  if (v === null || v === undefined || v === '') return <span className="text-zinc-500">—</span>
  if (isFuzzy(v)) return <FuzzyDate value={v} fallback="unknown" />
  if (typeof v === 'boolean') return <span>{v ? 'yes' : 'no'}</span>
  const s = String(v)
  if (/^[0-9a-f-]{36}$/.test(s)) return <span className="font-mono text-zinc-400">{s.slice(0, 8)}…</span>
  return <span className="line-clamp-3 break-words">{s}</span>
}

interface Props {
  member: MemberRead
  universeId: UUID
  universeSlug: string
  open: boolean
  onClose: () => void
}

/**
 * Fold a duplicate record into this one, or this one into it. Every change of
 * pick, direction or column preference re-runs the merge as a dry run, so what
 * the preview shows is what the server will do, not a client-side guess.
 */
export function MergeMemberDialog({ member, universeId, universeSlug, open, onClose }: Props) {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const dq = useDebounce(search, 200)
  const { data: results } = useMemberSearch(universeId, dq)
  const { data: similar } = useSimilarMembers(open ? universeId : null, member.display_name, member.id)
  const [other, setOther] = useState<{ id: UUID; name: string } | null>(null)
  const [keepThis, setKeepThis] = useState(true)
  const [prefer, setPrefer] = useState<string[]>([])
  const preview = useMergeMembers(universeId)
  const commit = useMergeMembers(universeId)
  const keepId = other ? (keepThis ? member.id : other.id) : null
  const dropId = other ? (keepThis ? other.id : member.id) : null
  const preferKey = prefer.join(',')

  // The dry run, re-run whenever the pick, direction or preferences change.
  const { mutate: runPreview } = preview
  useEffect(() => {
    if (keepId && dropId) runPreview({ keepId, dropId, prefer: preferKey ? preferKey.split(',') : [], dryRun: true })
  }, [keepId, dropId, preferKey, runPreview])

  // Show a preview only while it still describes the current choice; a stale one
  // from before a swap or a new pick would be read as the plan.
  const last: MemberMergeReport | undefined = preview.data
  const lastPrefer = preview.variables?.prefer.join(',') ?? ''
  const report =
    last && last.keep.id === keepId && last.drop.id === dropId && lastPrefer === preferKey ? last : null

  function reset() {
    setSearch(''); setOther(null); setKeepThis(true); setPrefer([]); preview.reset()
  }
  function close() { reset(); onClose() }

  function pick(id: UUID, name: string) {
    if (id === member.id) return
    setOther({ id, name }); setPrefer([]); setSearch('')
  }

  function togglePrefer(field: string) {
    setPrefer((p) => (p.includes(field) ? p.filter((f) => f !== field) : [...p, field]))
  }

  async function handleMerge() {
    if (!keepId || !dropId) return
    const r = await commit.mutateAsync({ keepId, dropId, prefer, dryRun: false })
    toast.success(`Merged ${r.drop.display_name} into ${r.keep.display_name}`)
    close()
    navigate({ href: `/${universeSlug}/members/${r.keep.slug ?? r.keep.id}` })
  }

  const moved = report ? Object.entries(report.moved).filter(([, n]) => n > 0) : []
  const suggestions = (similar ?? []).slice(0, 4)

  return (
    <Dialog open={open} onOpenChange={(v) => !v && close()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitMerge className="h-4 w-4 text-violet-400" />
            Merge duplicate
          </DialogTitle>
          <DialogDescription>
            Everything on the other record moves to the one you keep, then the other is deleted.
            The preview below is a dry run of the real merge.
          </DialogDescription>
        </DialogHeader>

        {!other ? (
          <div className="space-y-3">
            {suggestions.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-wider text-zinc-400">Likely duplicates</p>
                {suggestions.map(({ member: m, score }) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => pick(m.id, m.display_name)}
                    className="flex w-full items-center justify-between rounded border border-zinc-800 px-3 py-1.5 text-left text-sm text-zinc-200 hover:bg-zinc-800"
                  >
                    <span className="truncate">{m.display_name}{m.primary_set_name && <span className="ml-2 text-xs text-zinc-500">{m.primary_set_name}</span>}</span>
                    <span className="shrink-0 text-[10px] text-zinc-500">{Math.round(score * 100)}%</span>
                  </button>
                ))}
              </div>
            )}
            <Input placeholder="Search for the other record…" value={search} onChange={(e) => setSearch(e.target.value)} autoFocus />
            {dq.length >= 2 && results && (
              <div className="max-h-48 overflow-y-auto rounded border border-zinc-800 bg-zinc-950">
                {results.filter((m) => m.id !== member.id).length === 0 ? (
                  <div className="px-3 py-2 text-sm text-zinc-400">No matching members.</div>
                ) : (
                  results.filter((m) => m.id !== member.id).map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => pick(m.id, m.display_name)}
                      className="flex w-full flex-col px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800"
                    >
                      <span className="truncate">{m.display_name}</span>
                      {m.primary_set_name && <span className="truncate text-[10px] text-zinc-500">{m.primary_set_name}</span>}
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-2 rounded border border-zinc-800 p-3 text-sm">
              <div className="min-w-0 flex-1">
                <p className="text-[10px] uppercase tracking-wider text-emerald-400">Keep</p>
                <p className="truncate text-zinc-100">{keepThis ? member.display_name : other.name}</p>
              </div>
              <Button type="button" size="sm" variant="ghost" onClick={() => { setKeepThis((k) => !k); setPrefer([]) }} aria-label="Swap which record is kept">
                <ArrowLeftRight className="h-4 w-4" />
              </Button>
              <div className="min-w-0 flex-1 text-right">
                <p className="text-[10px] uppercase tracking-wider text-rose-400">Merge in and delete</p>
                <p className="truncate text-zinc-100">{keepThis ? other.name : member.display_name}</p>
              </div>
            </div>

            {!report ? (
              <p className="text-sm text-zinc-400">{preview.isPending ? 'Working out the merge…' : 'Could not preview this merge.'}</p>
            ) : (
              <>
                {report.fields.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs uppercase tracking-wider text-zinc-400">Fields that differ</p>
                    <p className="text-[11px] text-zinc-500">The kept record's value stands unless it was empty. Click a row to take the other value instead.</p>
                    <div className="divide-y divide-zinc-800 rounded border border-zinc-800">
                      {report.fields.map((f) => {
                        const preferred = prefer.includes(f.field)
                        return (
                          <button
                            key={f.field}
                            type="button"
                            onClick={() => togglePrefer(f.field)}
                            className="grid w-full grid-cols-[7rem_1fr_1fr] gap-2 px-3 py-1.5 text-left text-xs hover:bg-zinc-900"
                          >
                            <span className="text-zinc-400">{FIELD_LABEL[f.field] ?? f.field}{preferred && <span className="ml-1 text-violet-400">•</span>}</span>
                            <span className="text-emerald-300"><Val v={f.kept} /></span>
                            <span className="text-zinc-500 line-through decoration-zinc-600"><Val v={f.discarded} /></span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                <div className="space-y-1 text-sm">
                  <p className="text-xs uppercase tracking-wider text-zinc-400">Moves to {report.keep.display_name}</p>
                  {moved.length === 0
                    ? <p className="text-zinc-500">Nothing else to move.</p>
                    : <p className="text-zinc-300">{moved.map(([k, n]) => `${n} ${MOVED_LABEL[k] ?? k}`).join(' · ')}</p>}
                </div>

                {report.conflicts.length > 0 && (
                  <div className="space-y-1 rounded border border-amber-500/30 bg-amber-500/5 p-3">
                    <p className="text-xs font-medium text-amber-300">{report.conflicts.length} clash{report.conflicts.length === 1 ? '' : 'es'}</p>
                    <ul className="list-disc space-y-0.5 pl-4 text-xs text-zinc-300">
                      {report.conflicts.map((c, i) => <li key={i}>{c.message}</li>)}
                    </ul>
                  </div>
                )}
              </>
            )}

            <div className="flex justify-between gap-2 pt-2">
              <Button type="button" variant="ghost" onClick={() => { setOther(null); preview.reset() }}>Pick another</Button>
              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={close}>Cancel</Button>
                <Button type="button" variant="destructive" disabled={!report || commit.isPending} onClick={handleMerge}>
                  {commit.isPending ? 'Merging…' : `Merge and delete ${report?.drop.display_name ?? ''}`}
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
