import { Link2, X } from 'lucide-react'
import { useState } from 'react'
import type React from 'react'
import { Button } from '@/components/ui/button'

const URL_RE = /^https?:\/\/\S+$/

export function useUrlPasteBanner() {
  const [pastedUrl, setPastedUrl] = useState<string | null>(null)

  function onPaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const text = e.clipboardData.getData('text/plain').trim()
    if (URL_RE.test(text)) setPastedUrl(text)
  }

  function dismiss() {
    setPastedUrl(null)
  }

  return { pastedUrl, onPaste, dismiss }
}

interface UrlPasteBannerProps {
  url: string | null
  onSaveAsSource: () => void
  onDismiss: () => void
}

export function UrlPasteBanner({ url, onSaveAsSource, onDismiss }: UrlPasteBannerProps) {
  if (!url) return null
  return (
    <div className="mt-1 flex items-center gap-2 rounded-md border border-violet-700/60 bg-violet-950/30 px-3 py-2 text-xs">
      <Link2 className="h-3.5 w-3.5 shrink-0 text-violet-400" />
      <span className="flex-1 truncate text-zinc-300">
        URL detected: <span className="text-zinc-500">{url}</span>
      </span>
      <Button
        type="button"
        size="sm"
        variant="outline"
        onClick={onSaveAsSource}
        className="h-7 px-2.5 text-xs shrink-0"
      >
        Save as source
      </Button>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss URL detection"
        className="text-zinc-500 hover:text-zinc-300"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
