import { createFileRoute } from '@tanstack/react-router'

export const TAB_KEYS = ['overview', 'members', 'incidents', 'relationships', 'media', 'activity'] as const
export type TabKey = typeof TAB_KEYS[number]

export interface SetSearch {
  tab?: TabKey
}

// The page is in _app.$universe.sets.$id.lazy.tsx, its own chunk: at ~1,400 lines it was
// the largest route riding in the main bundle.
export const Route = createFileRoute('/_app/$universe/sets/$id')({
  validateSearch: (s: Record<string, unknown>): SetSearch => ({
    tab: typeof s.tab === 'string' && (TAB_KEYS as readonly string[]).includes(s.tab) ? (s.tab as TabKey) : undefined,
  }),
})
