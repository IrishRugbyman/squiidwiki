import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useDebounce } from './useDebounce'
import { usePagination } from './usePagination'

describe('usePagination', () => {
  it('starts at zero by default', () => {
    const { result } = renderHook(() => usePagination())
    expect(result.current.offset).toBe(0)
    expect(result.current.pageSize).toBe(50)
  })

  it('honours an initial offset, so a deep-linked page does not reset', () => {
    const { result } = renderHook(() => usePagination({ pageSize: 20, initialOffset: 60 }))
    expect(result.current.offset).toBe(60)
  })

  it('advances by exactly one page', () => {
    const { result } = renderHook(() => usePagination({ pageSize: 25 }))
    act(() => result.current.next())
    expect(result.current.offset).toBe(25)
    act(() => result.current.next())
    expect(result.current.offset).toBe(50)
  })

  it('clamps prev at zero rather than requesting a negative offset', () => {
    // A negative offset is a 422 from the API, not an empty page.
    const { result } = renderHook(() => usePagination({ pageSize: 25, initialOffset: 10 }))
    act(() => result.current.prev())
    expect(result.current.offset).toBe(0)
    act(() => result.current.prev())
    expect(result.current.offset).toBe(0)
  })

  it('resets to the first page', () => {
    const { result } = renderHook(() => usePagination({ pageSize: 10, initialOffset: 90 }))
    act(() => result.current.reset())
    expect(result.current.offset).toBe(0)
  })

  it('keeps a stable object identity while the offset is unchanged', () => {
    // The returned object is a dependency of the list queries; a new identity
    // on every render refetches the page on every keystroke elsewhere.
    const { result, rerender } = renderHook(() => usePagination({ pageSize: 10 }))
    const first = result.current
    rerender()
    expect(result.current).toBe(first)
  })

  it('produces a new identity once the offset moves', () => {
    const { result } = renderHook(() => usePagination({ pageSize: 10 }))
    const first = result.current
    act(() => result.current.next())
    expect(result.current).not.toBe(first)
  })
})

describe('useDebounce', () => {
  afterEach(() => vi.useRealTimers())

  it('returns the initial value immediately, so nothing renders empty on mount', () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useDebounce('abc', 250))
    expect(result.current).toBe('abc')
  })

  it('holds the old value until the delay has fully elapsed', () => {
    vi.useFakeTimers()
    const { result, rerender } = renderHook(({ v }) => useDebounce(v, 250), {
      initialProps: { v: 'a' },
    })
    rerender({ v: 'ab' })
    act(() => void vi.advanceTimersByTime(249))
    expect(result.current).toBe('a')
    act(() => void vi.advanceTimersByTime(1))
    expect(result.current).toBe('ab')
  })

  it('restarts the timer on each change, so only the last value lands', () => {
    // This is the point of the hook: typing "abc" must issue one search, not three.
    vi.useFakeTimers()
    const { result, rerender } = renderHook(({ v }) => useDebounce(v, 250), {
      initialProps: { v: '' },
    })
    rerender({ v: 'a' })
    act(() => void vi.advanceTimersByTime(200))
    rerender({ v: 'ab' })
    act(() => void vi.advanceTimersByTime(200))
    rerender({ v: 'abc' })
    act(() => void vi.advanceTimersByTime(200))
    expect(result.current).toBe('')

    act(() => void vi.advanceTimersByTime(50))
    expect(result.current).toBe('abc')
  })

  it('does not emit a value after unmount', () => {
    vi.useFakeTimers()
    const { rerender, unmount, result } = renderHook(({ v }) => useDebounce(v, 250), {
      initialProps: { v: 'a' },
    })
    rerender({ v: 'b' })
    unmount()
    act(() => void vi.advanceTimersByTime(500))
    expect(result.current).toBe('a')
  })
})
