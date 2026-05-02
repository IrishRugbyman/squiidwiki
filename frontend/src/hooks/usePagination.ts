import { useState, useCallback, useMemo } from 'react'

interface UsePaginationOptions {
  pageSize?: number
  initialOffset?: number
}

export function usePagination({ pageSize = 50, initialOffset = 0 }: UsePaginationOptions = {}) {
  const [offset, setOffset] = useState(initialOffset)

  const next = useCallback(() => setOffset((o) => o + pageSize), [pageSize])
  const prev = useCallback(() => setOffset((o) => Math.max(0, o - pageSize)), [pageSize])
  const reset = useCallback(() => setOffset(0), [])

  return useMemo(
    () => ({ offset, pageSize, setOffset, next, prev, reset }),
    [offset, pageSize, next, prev, reset],
  )
}
