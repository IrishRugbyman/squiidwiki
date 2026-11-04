import { Link } from '@tanstack/react-router'
import { X } from 'lucide-react'
import { PIN_ICON, PIN_KIND_LABEL } from '@/lib/notePins'
import { paramsIn } from '@/lib/universeRoutes'
import { cn } from '@/lib/utils'
import type { NotePin, PinKind } from '@/lib/types'

const PIN_ROUTE = {
  member: '/$universe/members/$id',
  set: '/$universe/sets/$id',
  incident: '/$universe/incidents/$id',
  alliance: '/$universe/alliances/$id',
} as const satisfies Record<PinKind, string>

const chipCls =
  'inline-flex max-w-[16rem] items-center gap-1 rounded-full border border-zinc-800 bg-zinc-900/60 py-0.5 pl-1.5 text-[11px] text-zinc-300'

/**
 * One pinned entity as a small chip that opens the entity's page. With
 * `onRemove` it grows a remove button (the note page's pin editor); without,
 * it is just the link.
 */
export function PinChip({ pin, onRemove }: { pin: NotePin; onRemove?: () => void }) {
  const Icon = PIN_ICON[pin.kind]
  return (
    <span className={cn(chipCls, onRemove ? 'pr-0.5' : 'pr-2')}>
      <Icon className="h-3 w-3 shrink-0 text-zinc-500" aria-hidden />
      <Link
        from="/$universe"
        to={PIN_ROUTE[pin.kind]}
        params={paramsIn(null, pin.slug ?? pin.id)}
        title={`${PIN_KIND_LABEL[pin.kind]}: ${pin.name}`}
        className="truncate transition-colors hover:text-violet-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
      >
        {pin.name}
      </Link>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Unpin ${pin.name}`}
          className="rounded-full p-0.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  )
}

/** A wrapped row of chips; renders nothing for a note with no pins. */
export function PinChips({ pins, className }: { pins: NotePin[]; className?: string }) {
  if (pins.length === 0) return null
  return (
    <div className={cn('flex flex-wrap gap-1.5', className)}>
      {pins.map((p) => (
        <PinChip key={`${p.kind}-${p.id}`} pin={p} />
      ))}
    </div>
  )
}
