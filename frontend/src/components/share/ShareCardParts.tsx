import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { SHARE_BG } from '@/lib/shareImage'

// Building blocks of the share cards: fixed-width layouts made to be read as an
// image in a chat, not as a page. Nothing here is interactive, and nothing names
// or links the wiki itself (see ~/squiidape/CLAUDE.md, "Public and private").

export const CARD_WIDTH = 1080

export function CardShell({ children, universeName }: { children: ReactNode; universeName: string | null }) {
  const asOf = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return (
    <div
      style={{ width: CARD_WIDTH, background: SHARE_BG }}
      className="flex flex-col gap-7 p-12 font-sans text-zinc-100 antialiased"
    >
      {children}
      <div className="flex items-center justify-between border-t border-zinc-800 pt-4 text-sm text-zinc-500">
        <span>{universeName ?? ''}</span>
        <span>As of {asOf}</span>
      </div>
    </div>
  )
}

/** A photo the capture step loads through the same-origin proxy (lib/shareImage.ts).
 *  It has no `src` until then, so it never paints a cross-origin image. */
export function ShareImg({ src, className, fallback }: { src: string | null | undefined; className?: string; fallback: string }) {
  if (!src) {
    return (
      <div className={cn('flex items-center justify-center bg-zinc-800 font-bold text-zinc-400', className)}>
        {fallback.slice(0, 2).toUpperCase()}
      </div>
    )
  }
  return <img data-share-src={src} alt="" className={cn('bg-zinc-800 object-cover', className)} />
}

export function Section({ title, count, children, className }: {
  title: string
  count?: number
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cn('min-w-0', className)}>
      <h2 className="mb-3 flex items-center gap-2 text-[13px] font-semibold uppercase tracking-[0.14em] text-zinc-400">
        {title}
        {count !== undefined && (
          <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-medium tracking-normal text-zinc-300">{count}</span>
        )}
      </h2>
      {children}
    </section>
  )
}

export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('rounded-xl border border-zinc-800 bg-zinc-900/50', className)}>{children}</div>
}

export function Chip({ children, className, style }: { children: ReactNode; className?: string; style?: React.CSSProperties }) {
  return (
    <span style={style} className={cn('inline-flex items-center gap-1.5 rounded-full bg-zinc-800 px-3 py-1 text-sm font-medium text-zinc-200', className)}>
      {children}
    </span>
  )
}

export interface StatCell { label: string; value: number | string; accent: string }

/** A row of counts; zeros are dimmed so the eye lands on what exists. */
export function StatGrid({ cells }: { cells: StatCell[] }) {
  return (
    <Panel>
      <div className="grid divide-x divide-zinc-800" style={{ gridTemplateColumns: `repeat(${cells.length}, minmax(0, 1fr))` }}>
        {cells.map((c) => {
          const empty = c.value === 0 || c.value === '0'
          return (
            <div key={c.label} className="flex flex-col items-center gap-1 px-2 py-4">
              <span className={cn('text-3xl font-bold tabular-nums leading-none', empty ? 'text-zinc-600' : c.accent)}>{c.value}</span>
              <span className={cn('text-xs font-medium uppercase tracking-wider', empty ? 'text-zinc-600' : 'text-zinc-400')}>{c.label}</span>
            </div>
          )
        })}
      </div>
    </Panel>
  )
}

/** Label beside value, one fact per row. Rows with no value are dropped by the caller. */
export function Facts({ rows }: { rows: [string, ReactNode][] }) {
  if (rows.length === 0) return null
  return (
    <Panel className="px-5 py-2">
      <dl className="divide-y divide-zinc-800/70">
        {rows.map(([label, value]) => (
          <div key={label} className="grid grid-cols-[8.5rem_minmax(0,1fr)] items-baseline gap-4 py-2.5">
            <dt className="text-sm text-zinc-400">{label}</dt>
            <dd className="min-w-0 text-[15px] leading-snug text-zinc-100">{value}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  )
}

export function Prose({ text }: { text: string }) {
  return (
    <Panel className="px-6 py-5">
      <p className="whitespace-pre-wrap text-[17px] leading-relaxed text-zinc-200">{text}</p>
    </Panel>
  )
}

/** Every photo, as a grid of squares. */
export function PhotoGrid({ urls, label }: { urls: string[]; label: string }) {
  if (urls.length === 0) return null
  const cols = urls.length >= 12 ? 6 : urls.length >= 5 ? 5 : 4
  return (
    <Section title="Photos" count={urls.length}>
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
        {urls.map((u, i) => (
          <ShareImg key={`${u}-${i}`} src={u} fallback={label} className="aspect-square w-full rounded-lg" />
        ))}
      </div>
    </Section>
  )
}

export function Dash() {
  return <span className="text-zinc-600">-</span>
}
