import { useEffect } from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type RecentEntityType = 'member' | 'set' | 'alliance' | 'incident' | 'source' | 'municipality' | 'research'

export interface RecentEntity {
  type: RecentEntityType
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
          const filtered = state.entries.filter(
            (e) => !(e.type === entry.type && e.id === entry.id),
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

export function useRecordRecent(
  entry: Omit<RecentEntity, 'visitedAt'> | null | undefined,
) {
  const record = useRecentsStore((s) => s.record)
  // Keyed on the fields, not the object: callers build `entry` inline, so it
  // is a new object every render and would re-record on each one.
  const type = entry?.type
  const id = entry?.id
  const slug = entry?.slug ?? null
  const label = entry?.label
  useEffect(() => {
    if (!type || !id || label === undefined) return
    record({ type, id, slug, label })
  }, [type, id, slug, label, record])
}
