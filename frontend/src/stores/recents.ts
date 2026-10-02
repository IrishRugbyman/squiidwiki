import { useEffect, useMemo } from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useUniverseStore } from '@/stores/universe'

export type RecentEntityType = 'member' | 'set' | 'alliance' | 'incident' | 'source' | 'municipality' | 'research'

export interface RecentEntity {
  type: RecentEntityType
  /** Slug of the universe it was visited in: slugs and ids mean nothing outside it. */
  universe: string
  id: string
  slug: string | null
  label: string
  visitedAt: number
}

interface RecentsState {
  entries: RecentEntity[]
  record: (entry: Omit<RecentEntity, 'visitedAt'>) => void
  clear: () => void
}

const MAX_ENTRIES = 8

export const useRecentsStore = create<RecentsState>()(
  persist(
    (set) => ({
      entries: [],
      record: (entry) =>
        set((state) => {
          // Entries from before the universe was recorded cannot be linked, so
          // they are dropped the first time anything is recorded.
          const filtered = state.entries.filter(
            (e) => !!e.universe && !(e.type === entry.type && e.id === entry.id),
          )
          return {
            entries: [{ ...entry, visitedAt: Date.now() }, ...filtered].slice(0, MAX_ENTRIES),
          }
        }),
      clear: () => set({ entries: [] }),
    }),
    { name: 'squiidwiki-recents' },
  ),
)

/** The recent entries of the universe being viewed, newest first. */
export function useUniverseRecents(): RecentEntity[] {
  const entries = useRecentsStore((s) => s.entries)
  const universe = useUniverseStore((s) => s.activeUniverse?.slug)
  return useMemo(() => entries.filter((e) => e.universe === universe), [entries, universe])
}

export function useRecordRecent(
  entry: Omit<RecentEntity, 'visitedAt' | 'universe'> | null | undefined,
) {
  const record = useRecentsStore((s) => s.record)
  const universe = useUniverseStore((s) => s.activeUniverse?.slug)
  // Keyed on the fields, not the object: callers build `entry` inline, so it
  // is a new object every render and would re-record on each one.
  const type = entry?.type
  const id = entry?.id
  const slug = entry?.slug ?? null
  const label = entry?.label
  useEffect(() => {
    if (!type || !id || !universe || label === undefined) return
    record({ type, universe, id, slug, label })
  }, [type, universe, id, slug, label, record])
}
