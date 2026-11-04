import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { RELIABILITY_DESCRIPTION, RELIABILITY_DOT, RELIABILITY_LABEL } from '@/lib/statusColors'
import type { SourceReliability } from '@/lib/types'
import { cn } from '@/lib/utils'

/** A source's reliability as a dot, its meaning on hover. */
export function ReliabilityDot({ reliability, className }: { reliability: SourceReliability; className?: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          role="img"
          aria-label={`${RELIABILITY_LABEL[reliability]} reliability`}
          className={cn('inline-block h-2 w-2 shrink-0 rounded-full', RELIABILITY_DOT[reliability], className)}
        />
      </TooltipTrigger>
      <TooltipContent>
        <span className="font-medium">{RELIABILITY_LABEL[reliability]}</span>: {RELIABILITY_DESCRIPTION[reliability]}
      </TooltipContent>
    </Tooltip>
  )
}
