import { gangSwatchStyle } from '@/lib/gangs'
import { cn } from '@/lib/utils'

const SIZES = { xs: 'h-3 w-3 rounded', sm: 'h-4 w-4 rounded-md', md: 'h-6 w-6 rounded-md', lg: 'h-10 w-10 rounded-lg' }

/** A card's colours as a small split square. */
export function GangSwatch({
  color,
  secondary,
  size = 'sm',
  className,
}: {
  color: string | null
  secondary: string | null
  size?: keyof typeof SIZES
  className?: string
}) {
  return (
    <span
      aria-hidden
      className={cn('inline-block shrink-0 ring-1 ring-zinc-700', SIZES[size], className)}
      style={gangSwatchStyle(color, secondary)}
    />
  )
}
