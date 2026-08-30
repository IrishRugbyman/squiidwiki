import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'
import { server } from './msw'

// Radix drives its primitives through pointer events, ResizeObserver and
// matchMedia, none of which jsdom implements. Without these the first render of
// any Select, Dialog or Tooltip throws, so they are stubbed once here rather
// than per-suite.
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.IntersectionObserver ??= class {
    root = null
    rootMargin = ''
    thresholds: readonly number[] = []
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return []
    }
  } as unknown as typeof IntersectionObserver

  if (!window.matchMedia) {
    window.matchMedia = (query: string) =>
      ({
        matches: false,
        media: query,
        onchange: null,
        addListener() {},
        removeListener() {},
        addEventListener() {},
        removeEventListener() {},
        dispatchEvent: () => false,
      }) as MediaQueryList
  }

  Element.prototype.hasPointerCapture ??= () => false
  Element.prototype.setPointerCapture ??= () => {}
  Element.prototype.releasePointerCapture ??= () => {}
  Element.prototype.scrollIntoView ??= () => {}

  server.listen({ onUnhandledRequest: 'error' })
})

// `error` above is the point: an unmocked request is a test that was about to
// assert against whatever the network happened to do. It fails loudly instead.

afterEach(() => {
  cleanup()
  server.resetHandlers()
  localStorage.clear()
  vi.restoreAllMocks()
})

afterAll(() => server.close())
