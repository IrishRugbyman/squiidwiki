import { createFileRoute } from '@tanstack/react-router'
import { Sheet, SheetContent } from '@/components/Sheet'
import { SourceForm } from '@/components/sources/SourceForm'
import type { SourceKind, SourceRead, SourceReliability } from '@/lib/types'
import { textParam } from '@/lib/searchParams'

export type SourceSortKey = 'added' | 'title' | 'published' | 'cited' | 'reliability'

export interface SourcesSearch {
  q?: string
  kind?: SourceKind
  reliability?: SourceReliability
  /** A publication name, or '__none__' for sources without one. */
  publication?: string
  uncited?: boolean
  sort?: SourceSortKey
  order?: 'asc' | 'desc'
  page?: number
}

const SORT_KEYS: SourceSortKey[] = ['added', 'title', 'published', 'cited', 'reliability']
const RELIABILITY_KEYS: SourceReliability[] = ['HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED']
const KIND_KEYS: SourceKind[] = ['COURT', 'PRESS', 'CUSTODY', 'SOCIAL', 'VIDEO', 'WIKI', 'MAP', 'INTERNAL', 'OTHER']

// The page is in _app.$universe.sources.index.lazy.tsx, its own chunk; this file keeps
// the URL schema and the form sheet, which other screens import.
export const Route = createFileRoute('/_app/$universe/sources/')({
  validateSearch: (s: Record<string, unknown>): SourcesSearch => ({
    q: textParam(s.q),
    kind: typeof s.kind === 'string' && (KIND_KEYS as string[]).includes(s.kind) ? (s.kind as SourceKind) : undefined,
    reliability: typeof s.reliability === 'string' && (RELIABILITY_KEYS as string[]).includes(s.reliability) ? (s.reliability as SourceReliability) : undefined,
    publication: textParam(s.publication),
    uncited: s.uncited === true || s.uncited === 'true' ? true : undefined,
    sort: typeof s.sort === 'string' && (SORT_KEYS as string[]).includes(s.sort) ? (s.sort as SourceSortKey) : undefined,
    order: s.order === 'desc' ? 'desc' : s.order === 'asc' ? 'asc' : undefined,
    page: typeof s.page === 'number' && s.page > 1 ? Math.floor(s.page) : undefined,
  }),
})

interface SourceFormSheetProps {
  universeId: string
  open: boolean
  onClose: () => void
  initial?: SourceRead
  defaultUrl?: string
  /** The saved source, for a caller that goes on to cite it. */
  onSaved?: (source: SourceRead) => void
}

/**
 * Keyed on the target: the form seeds from props once, so a sheet reused for
 * a second source must be a fresh instance or it keeps the first's values.
 */
export function SourceFormSheet(props: SourceFormSheetProps) {
  const { universeId, open, onClose, initial, defaultUrl, onSaved } = props
  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        title={initial ? 'Edit source' : 'Add source'}
        description={initial ? 'Update this source' : 'A document, page or record the research cites'}
      >
        <SourceForm
          key={initial?.id ?? 'new'}
          universeId={universeId}
          initial={initial}
          defaultUrl={defaultUrl}
          onSaved={(s) => { onSaved?.(s); onClose() }}
          onCancel={onClose}
        />
      </SheetContent>
    </Sheet>
  )
}
