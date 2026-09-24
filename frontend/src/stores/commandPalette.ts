import { create } from 'zustand'

/**
 * Open state of the global command palette.
 *
 * It used to be local state in `_app.tsx`, reachable only through Ctrl+K and the
 * sidebar's universe switcher. Pages now open it too (the dashboard's search
 * field, the mobile top bar), so the flag lives here. Not persisted: a palette
 * that reopened itself on reload would be a bug.
 */
interface CommandPaletteState {
  open: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
}

export const useCommandPalette = create<CommandPaletteState>()((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
  toggle: () => set((s) => ({ open: !s.open })),
}))
