import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({ title = 'Something went wrong', message, onRetry, className }: ErrorStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      <AlertCircle className="mb-4 h-10 w-10 text-destructive/60" />
      <p className="text-sm font-medium">{title}</p>
      {message && <p className="mt-1 text-xs text-muted-foreground">{message}</p>}
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw className="mr-2 h-3 w-3" />
          Try again
        </Button>
      )}
    </div>
  )
}
