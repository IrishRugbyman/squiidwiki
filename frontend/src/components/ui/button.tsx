import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  // The transition list is explicit rather than `transition-colors` or
  // `transition-all` for two reasons: transform must be included so the
  // :active press reads, and box-shadow must be EXCLUDED so the focus ring
  // appears instantly. A ring that fades in is a ring a keyboard user has
  // already tabbed past.
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ' +
    'transition-[color,background-color,border-color,transform] duration-150 ' +
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 ' +
    'active:scale-[0.98] ' +
    'disabled:pointer-events-none disabled:opacity-50 disabled:saturate-50',
  {
    variants: {
      variant: {
        default: 'bg-violet-600 text-white hover:bg-violet-500 active:bg-violet-700',
        destructive: 'bg-red-600 text-white hover:bg-red-500 active:bg-red-700',
        outline:
          'border border-zinc-700 bg-transparent text-foreground hover:bg-zinc-800 active:bg-zinc-700',
        secondary: 'bg-zinc-800 text-zinc-100 hover:bg-zinc-700 active:bg-zinc-600',
        ghost: 'hover:bg-zinc-800 hover:text-white active:bg-zinc-700',
        link: 'text-violet-400 underline-offset-4 hover:underline active:text-violet-300',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }
