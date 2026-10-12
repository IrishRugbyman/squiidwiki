import { createFileRoute } from '@tanstack/react-router'

export const ALLIANCE_TAB_KEYS = ['overview', 'sets', 'members', 'incidents', 'relationships', 'media', 'activity'] as const
export type AllianceTabKey = typeof ALLIANCE_TAB_KEYS[number]

export interface AllianceSearch {
  tab?: AllianceTabKey
}

// The page is in _app.$universe.alliances.$id.lazy.tsx, its own chunk.
export const Route = createFileRoute('/_app/$universe/alliances/$id')({
  validateSearch: (s: Record<string, unknown>): AllianceSearch => ({
    tab: typeof s.tab === 'string' && (ALLIANCE_TAB_KEYS as readonly string[]).includes(s.tab) ? (s.tab as AllianceTabKey) : undefined,
  }),
})
