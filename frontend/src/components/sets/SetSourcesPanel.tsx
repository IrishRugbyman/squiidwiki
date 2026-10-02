import { Link } from '@tanstack/react-router'
import { ExternalLink, Plus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { AttachSourcesDialog } from '@/components/AttachSourcesDialog'
import { PanelHeading } from '@/components/detail/DetailParts'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { useUpdateSet } from '@/lib/queries'
import type { MunicipalitySourceBrief, UUID } from '@/lib/types'
import { SourceFormSheet } from '@/routes/_app.$universe.sources.index'

/**
 * Citations for the set itself (`set_source`): where its ground, its gang and its
 * history come from, as opposed to the sources on each member.
 */
export function SetSourcesPanel({
  setId,
  universeId,
  sources,
}: {
  setId: UUID
  universeId: UUID
  sources: MunicipalitySourceBrief[]
}) {
  const [attaching, setAttaching] = useState(false)
  const [creating, setCreating] = useState(false)
  const updateSet = useUpdateSet(setId)

  return (
    <section>
      <PanelHeading action={
        <button type="button" onClick={() => setAttaching(true)} className="inline-flex items-center gap-1 text-xs text-zinc-400 transition-colors hover:text-violet-400">
          <Plus className="h-3 w-3" />Cite
        </button>
      }>Sources{sources.length > 0 ? ` (${sources.length})` : ''}</PanelHeading>
      {sources.length === 0 ? (
        <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 text-xs text-zinc-400">No sources cited.</p>
      ) : (
        <ul className="divide-y divide-zinc-800/70 rounded-lg border border-zinc-800 bg-zinc-900/30">
          {sources.map((src) => (
            <li key={src.id} className="flex items-center gap-3 px-3 py-2.5">
              <Link from="/$universe" to="/$universe/sources/$id" params={{ id: src.id }} className="group min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-white transition-colors group-hover:text-violet-300">{src.title}</span>
                {src.publication && <span className="block truncate text-[11px] text-zinc-500">{src.publication}</span>}
              </Link>
              <ReliabilityBadge reliability={src.reliability} />
              <a href={src.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${src.title} in a new tab`}
                className="rounded p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-violet-300">
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </li>
          ))}
        </ul>
      )}

      {attaching && (
        <AttachSourcesDialog
          universeId={universeId}
          existingIds={sources.map((src) => src.id)}
          open
          onClose={() => setAttaching(false)}
          onCreateNew={() => { setAttaching(false); setCreating(true) }}
          onAttach={(source_ids) =>
            updateSet.mutateAsync({ universe_id: universeId, source_ids }).catch((e: Error) => {
              toast.error(e.message || 'Could not cite the source')
              throw e
            })
          }
          attaching={updateSet.isPending}
        />
      )}
      {creating && <SourceFormSheet universeId={universeId} open onClose={() => setCreating(false)} />}
    </section>
  )
}
