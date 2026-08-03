import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        // transition-colors deliberately excludes box-shadow, so the focus ring
        // lands instantly while the hover border tint eases.
        'flex h-9 w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1 text-sm text-white shadow-sm transition-colors ' +
          'placeholder:text-zinc-400 hover:border-zinc-600 ' +
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 ' +
          // Pair with aria-invalid on the field so the error state is carried by
          // the accessibility tree, not by colour alone.
          'aria-[invalid=true]:border-red-800 aria-[invalid=true]:focus-visible:ring-red-500 ' +
          'disabled:cursor-not-allowed disabled:opacity-50 disabled:saturate-50',
        className,
      )}
      ref={ref}
      {...props}
    />
  )
})
Input.displayName = 'Input'

export { Input }
