import { useId, useState } from 'react'
import type React from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import type { MediaWithUrls } from '@/lib/types'
import { CAPTION_MAX_LENGTH, normalizeCaption } from './caption'

interface PhotoCaptionDialogProps {
  /** The photo being captioned; null while the dialog is closed. */
  media: MediaWithUrls | null
  open: boolean
  pending: boolean
  onSave: (caption: string | null) => void
  onCancel: () => void
}

export function PhotoCaptionDialog({ media, open, pending, onSave, onCancel }: PhotoCaptionDialogProps) {
  return (
    <Dialog open={open && media !== null} onOpenChange={(v) => !v && !pending && onCancel()}>
      <DialogContent>
        {media && (
          // Keyed by photo so re-opening on another tile re-seeds the draft
          // instead of carrying the previous photo's text across.
          <CaptionForm key={media.id} media={media} pending={pending} onSave={onSave} onCancel={onCancel} />
        )}
      </DialogContent>
    </Dialog>
  )
}

interface CaptionFormProps {
  media: MediaWithUrls
  pending: boolean
  onSave: (caption: string | null) => void
  onCancel: () => void
}

function CaptionForm({ media, pending, onSave, onCancel }: CaptionFormProps) {
  const fieldId = useId()
  const [draft, setDraft] = useState(media.caption ?? '')
  const current = media.caption ?? null
  const next = normalizeCaption(draft)
  const unchanged = next === current
  const thumbSrc = media.thumb_url ?? media.url

  const submit = (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (unchanged || pending) return
    onSave(next)
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter alone inserts a newline; Cmd/Ctrl-Enter saves, matching the
    // convention in the rest of the app's text fields.
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      if (!unchanged && !pending) onSave(next)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <DialogHeader>
        <DialogTitle>{current ? 'Edit caption' : 'Add caption'}</DialogTitle>
        <DialogDescription>
          Shown under the photo in the gallery and the viewer. It is also the image's alt text.
        </DialogDescription>
      </DialogHeader>

      <div className="flex gap-4">
        {thumbSrc && (
          <img
            src={thumbSrc}
            alt=""
            className="h-24 w-24 shrink-0 rounded-md object-cover ring-1 ring-zinc-800"
          />
        )}
        <div className="min-w-0 flex-1 space-y-1.5">
          <Label htmlFor={fieldId}>Caption</Label>
          <Textarea
            id={fieldId}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            maxLength={CAPTION_MAX_LENGTH}
            rows={3}
            autoFocus
            disabled={pending}
            placeholder="Where, when, or who is in the photo"
            className="min-h-[72px] resize-y"
          />
          <div className="flex justify-end text-[11px] tabular-nums text-zinc-500">
            {draft.length} / {CAPTION_MAX_LENGTH}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2 pt-1">
        <div>
          {current && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-red-300 hover:text-red-200"
              disabled={pending}
              onClick={() => onSave(null)}
            >
              Remove caption
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={onCancel} disabled={pending}>
            Cancel
          </Button>
          <Button type="submit" disabled={unchanged || pending}>
            {pending ? 'Saving…' : 'Save'}
          </Button>
        </div>
      </div>
    </form>
  )
}
