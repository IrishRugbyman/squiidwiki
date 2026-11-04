import { Link } from '@tanstack/react-router'
import { NotebookText } from 'lucide-react'
import { PanelHeading } from '@/components/detail/DetailParts'
import { firstLine } from '@/lib/notePins'
import { usePinnedNotes } from '@/lib/queries'
import { NOTE_KIND_LABEL, type PinKind, type UUID } from '@/lib/types'

/**
 * The research notes pinned to one record, shown on its detail page. Renders
 * nothing while loading and when there are none, so a page without notes looks
 * exactly as before.
 */
export function PinnedNotesPanel({ universeId, kind, entityId }: { universeId: UUID; kind: PinKind; entityId: UUID }) {
  const { data } = usePinnedNotes(universeId, kind, entityId)
  const notes = data ?? []
  if (notes.length === 0) return null

  return (
    <section>
      <PanelHeading>Research notes</PanelHeading>
      <div className="divide-y divide-zinc-800/70 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
        {notes.map((n) => (
          <Link
            key={n.id}
            from="/$universe"
            to="/$universe/research/$id"
            params={{ id: n.id }}
            search={{ edit: undefined }}
            className="group block px-3 py-2.5 transition-colors hover:bg-zinc-900/60 focus-visible:bg-zinc-900/60 focus-visible:outline-none"
          >
            <div className="flex items-center gap-2">
              <NotebookText className="h-3.5 w-3.5 shrink-0 text-violet-500" aria-hidden />
              <span className="min-w-0 flex-1 truncate text-sm font-medium text-zinc-100 transition-colors group-hover:text-violet-400">
                {n.title || 'Untitled'}
              </span>
              <span className="shrink-0 rounded-full border border-zinc-700 px-2 py-px text-[10px] text-zinc-300">
                {NOTE_KIND_LABEL[n.kind]}
              </span>
            </div>
            {firstLine(n.content) && <p className="mt-0.5 truncate pl-[22px] text-xs text-zinc-400">{firstLine(n.content)}</p>}
          </Link>
        ))}
      </div>
    </section>
  )
}
