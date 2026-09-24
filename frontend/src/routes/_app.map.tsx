import { createFileRoute } from '@tanstack/react-router'
import type { UUID } from '@/lib/types'

// The page is in _app.map.lazy.tsx, its own chunk: it carries the turf
// geometry code, which every other page was downloading with the main bundle.
export const Route = createFileRoute('/_app/map')({
  validateSearch: (s: Record<string, unknown>) => ({
    selected: typeof s.selected === 'string' ? (s.selected as UUID) : undefined,
    edit: s.edit === '1' || s.edit === 1 ? '1' as const : undefined,
    view: s.view === 'alliances' ? 'alliances' as const : 'sets' as const,
  }),
})
