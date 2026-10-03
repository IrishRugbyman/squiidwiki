import { Link } from '@tanstack/react-router'
import { Gavel, Plus } from 'lucide-react'
import { PanelHeading, UniverseChip } from '@/components/detail/DetailParts'
import { FuzzyDate } from '@/components/FuzzyDate'
import { Badge } from '@/components/ui/badge'
import { CASE_KIND_LABEL, courtAndDocket, DISPOSITION_CHIP, DISPOSITION_LABEL, formatSentence } from '@/lib/courtCases'
import { useCourtCasesFor } from '@/lib/queries'
import type { CourtCaseListItem, UUID } from '@/lib/types'
import { paramsIn } from '@/lib/universeRoutes'

/** One case as a list row: name, court and docket, and on a member's own list
 *  what it did with him. Opens in the case's own universe. */
export function CourtCaseRow({ c }: { c: CourtCaseListItem }) {
  const sentence = formatSentence(c.viewer_sentence_months, c.viewer_life_sentence)
  return (
    <Link
      from="/$universe" to="/$universe/cases/$id" params={paramsIn(c.universe_slug, c.slug ?? c.id)}
      className="flex items-center gap-3 px-3 py-2.5 transition-colors hover:bg-zinc-900/60"
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-zinc-800 text-zinc-300 ring-1 ring-zinc-700">
        <Gavel className="h-4 w-4" aria-hidden />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2 text-sm">
          <span className="truncate font-medium text-zinc-100">{c.name}</span>
          <UniverseChip slug={c.universe_slug} />
        </span>
        <span className="block truncate text-xs text-zinc-400">
          {courtAndDocket(c)}
          {c.kind !== 'CRIMINAL' && <> · {CASE_KIND_LABEL[c.kind]}</>}
          {c.filed_at?.year && <> · filed <FuzzyDate value={c.filed_at} /></>}
        </span>
      </span>
      {c.viewer_disposition && (
        <span className="flex shrink-0 flex-col items-end gap-0.5">
          <Badge className={`border ${DISPOSITION_CHIP[c.viewer_disposition]}`}>{DISPOSITION_LABEL[c.viewer_disposition]}</Badge>
          {sentence && <span className="text-[11px] tabular-nums text-zinc-400">{sentence}</span>}
        </span>
      )}
    </Link>
  )
}

interface CasesPanelProps {
  filter: 'member_id' | 'set_id' | 'incident_id' | 'alliance_id'
  id: UUID | null | undefined
  universeId: UUID | null
  /** Opens the case form, prefilled with this entity; omitted where a case is not made from here. */
  onAdd?: () => void
  /** Show the panel when there is nothing in it, so the Add action is reachable. */
  showEmpty?: boolean
}

/** The court cases a member, set, incident or alliance appears in, across universes. */
export function CasesPanel({ filter, id, universeId, onAdd, showEmpty = false }: CasesPanelProps) {
  const { data: cases = [], isLoading } = useCourtCasesFor(filter, id, universeId)
  if (isLoading || (cases.length === 0 && !showEmpty)) return null
  return (
    <section>
      <PanelHeading action={onAdd && (
        <button type="button" onClick={onAdd} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
          <Plus className="h-3 w-3" />New case
        </button>
      )}>Court cases{cases.length > 0 ? ` (${cases.length})` : ''}</PanelHeading>
      {cases.length === 0 ? (
        <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No court cases recorded.</p>
      ) : (
        <div className="divide-y divide-zinc-800/70 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
          {cases.map((c) => <CourtCaseRow key={c.id} c={c} />)}
        </div>
      )}
    </section>
  )
}
