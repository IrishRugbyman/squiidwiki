import { useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'

type Handler = (e: KeyboardEvent) => void

function isTypingContext(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable
}

export function useGlobalKey(key: string, handler: Handler, deps: unknown[] = []) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key !== key) return
      if (isTypingContext(e.target)) return
      handler(e)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}

export interface GoToShortcut {
  keys: string
  to: string
  label: string
}

export const GO_TO_SHORTCUTS: GoToShortcut[] = [
  { keys: 'g d', to: '/', label: 'Dashboard' },
  { keys: 'g s', to: '/sets', label: 'Sets' },
  { keys: 'g a', to: '/alliances', label: 'Alliances' },
  { keys: 'g m', to: '/members', label: 'Members' },
  { keys: 'g i', to: '/incidents', label: 'Incidents' },
  { keys: 'g r', to: '/sources', label: 'Sources' },
  { keys: 'g p', to: '/municipalities', label: 'Municipalities' },
  { keys: 'g c', to: '/calendar', label: 'Calendar' },
]

export function useGoToNavigation() {
  const navigate = useNavigate()

  useEffect(() => {
    let lastG = 0
    function onKey(e: KeyboardEvent) {
      if (isTypingContext(e.target)) return
      if (e.metaKey || e.ctrlKey || e.altKey) return

      if (e.key === 'g') {
        lastG = Date.now()
        return
      }
      if (Date.now() - lastG > 800) return

      const target = GO_TO_SHORTCUTS.find((s) => s.keys === `g ${e.key}`)
      if (target) {
        e.preventDefault()
        navigate({ to: target.to })
        lastG = 0
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [navigate])
}
