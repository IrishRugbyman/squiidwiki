import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Universe {
  id: string
  name: string
  slug: string
}

interface UniverseState {
  activeUniverse: Universe | null
  setActiveUniverse: (universe: Universe | null) => void
}

export const useUniverseStore = create<UniverseState>()(
  persist(
    (set) => ({
      activeUniverse: null,
      setActiveUniverse: (universe) => set({ activeUniverse: universe }),
    }),
    { name: 'squiidwiki-universe' },
  ),
)
