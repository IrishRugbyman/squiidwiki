/**
 * Brand accent, as literal hex.
 *
 * Everywhere that can use a Tailwind class should use `violet-*` instead — that
 * ramp is redefined to the brand purple in `index.css` and is the canonical
 * definition. This module exists only for the surfaces that cannot take a CSS
 * class and demand a colour literal at runtime:
 *
 *   - maplibre paint properties (`fill-color`, `line-color`, …)
 *   - recharts `stroke` / `fill` props
 *   - inline `style={{ backgroundColor }}` on data-driven swatches
 *
 * These values are the computed output of the `--color-violet-*` ramp. If the
 * accent moves in `index.css`, recompute and update here — a drifted copy is
 * exactly how the app ended up with two purples in the first place.
 */
export const BRAND = {
  /** violet-400 — hsl(279 60% 68%). Light accent: chart strokes, map highlights. */
  light: '#BC7CDE',
  /** violet-500 — hsl(279 58% 56%). Mid accent: focus rings, active markers. */
  base: '#A24ED0',
  /** violet-600 — hsl(279 60% 46%). Primary accent: fills, solid buttons. */
  strong: '#8A2FBC',
  /** violet-700 — hsl(279 64% 38%). Pressed / deep fills. */
  deep: '#74239F',
} as const

/** Neutral used for "no data" / inactive geometry alongside the accent. */
export const BRAND_INACTIVE = '#52525B'
