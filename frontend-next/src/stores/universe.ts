import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Universe {
  id: number
  name: string
  slug: string
}

interface UniverseState {
  active: Universe | null
  setActive: (universe: Universe) => void
  clear: () => void
}

export const useUniverseStore = create<UniverseState>()(
  persist(
    (set) => ({
      active: null,
      setActive: (universe) => set({ active: universe }),
      clear: () => set({ active: null }),
    }),
    { name: 'squiidwiki-universe' },
  ),
)
