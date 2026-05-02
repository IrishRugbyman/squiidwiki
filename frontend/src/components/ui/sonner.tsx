import { Toaster as Sonner } from 'sonner'

export function Toaster() {
  return (
    <Sonner
      theme="dark"
      position="bottom-right"
      toastOptions={{
        classNames: {
          toast: 'bg-zinc-900 border-zinc-800 text-zinc-100 shadow-xl',
          description: 'text-zinc-400',
          actionButton: 'bg-violet-600 text-white',
          cancelButton: 'bg-zinc-800 text-zinc-400',
          error: '!bg-red-950 !border-red-800 !text-red-200',
          success: '!bg-emerald-950 !border-emerald-800 !text-emerald-200',
        },
      }}
    />
  )
}
