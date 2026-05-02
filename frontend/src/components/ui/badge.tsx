import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-violet-600 text-white',
        secondary: 'border-transparent bg-zinc-800 text-zinc-300',
        destructive: 'border-transparent bg-red-600 text-white',
        outline: 'border-zinc-700 text-zinc-300',
        success: 'border-transparent bg-emerald-700 text-white',
        warning: 'border-transparent bg-amber-700 text-white',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
