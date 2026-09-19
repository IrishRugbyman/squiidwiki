import { useEffect, useRef, useState } from 'react'

/**
 * Measures a container's width via ResizeObserver and returns [ref, width].
 * Recharts' ResponsiveContainer initialises its size to -1 and warns
 * ("width(-1) and height(-1) of chart should be greater than 0") on the first
 * paint before its own observer fires. Feeding it a measured numeric width
 * instead - and only rendering once width > 0 - avoids that first-paint warning
 * while staying fully responsive on resize.
 */
export function useMeasuredWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? 0
      if (w > 0) setWidth(w)
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return [ref, width] as const
}
