import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface CopyButtonProps {
  value: string
  label?: string
  className?: string
  size?: 'sm' | 'md'
  silent?: boolean
}

export function CopyButton({ value, label = 'Copy', className, size = 'sm', silent = false }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  async function handleClick(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      if (!silent) toast.success(`${label === 'Copy' ? 'Copied' : `${label} copied`}`)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      toast.error('Could not copy to clipboard')
    }
  }

  const dim = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={handleClick}
            aria-label={label}
            className={cn(
              'inline-flex items-center justify-center rounded text-zinc-400 transition-colors hover:text-zinc-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50',
              size === 'sm' ? 'p-1' : 'p-1.5',
              className,
            )}
          >
            {copied ? <Check className={cn(dim, 'text-emerald-400')} /> : <Copy className={dim} />}
          </button>
        </TooltipTrigger>
        <TooltipContent side="top">{copied ? 'Copied!' : label}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
