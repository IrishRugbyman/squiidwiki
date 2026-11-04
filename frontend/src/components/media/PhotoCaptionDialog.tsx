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
import type { MediaWithUrls, UUID } from '@/lib/types'
import { CAPTION_MAX_LENGTH, normalizeCaption } from './caption'
import { draftsFrom, isOrdered, peoplePayload, samePeople, type PersonDraft } from './people'
import { PhotoPeopleEditor } from './PhotoPeopleEditor'

/** What a save changes: a field left out is untouched. */
export interface PhotoEdits {
  caption?: string | null
  people?: { member_id: UUID; position: number | null }[]
}

interface PhotoCaptionDialogProps {
  /** The photo being captioned; null while the dialog is closed. */
  media: MediaWithUrls | null
  universeId: UUID
  open: boolean
  pending: boolean
  onSave: (edits: PhotoEdits) => void
  onCancel: () => void
}

export function PhotoCaptionDialog({ media, universeId, open, pending, onSave, onCancel }: PhotoCaptionDialogProps) {
  return (
    <Dialog open={open && media !== null} onOpenChange={(v) => !v && !pending && onCancel()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        {media && (
          // Keyed by photo so re-opening on another tile re-seeds the draft
          // instead of carrying the previous photo's text across.
          <CaptionForm
            key={media.id}
            media={media}
            universeId={universeId}
            pending={pending}
            onSave={onSave}
            onCancel={onCancel}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

interface CaptionFormProps {
  media: MediaWithUrls
  universeId: UUID
  pending: boolean
  onSave: (edits: PhotoEdits) => void
  onCancel: () => void
}

function CaptionForm({ media, universeId, pending, onSave, onCancel }: CaptionFormProps) {
  const fieldId = useId()
  const [draft, setDraft] = useState(media.caption ?? '')
  const current = media.caption ?? null
  const next = normalizeCaption(draft)
  const thumbSrc = media.thumb_url ?? media.url

  // A photo nobody is tagged in starts ordered, so the first tags read left to right.
  const initialDrafts = draftsFrom(media.people)
  const initialOrdered = media.people.length === 0 ? true : isOrdered(media.people)
  const [people, setPeople] = useState<PersonDraft[]>(initialDrafts)
  const [ordered, setOrdered] = useState(initialOrdered)
  const [photoSetIds] = useState<ReadonlySet<UUID>>(() => new Set(media.set_id ? [media.set_id] : []))

  const captionChanged = next !== current
  const peopleChanged = !samePeople(people, ordered, initialDrafts, initialOrdered)
  const unchanged = !captionChanged && !peopleChanged

  /** Only what changed, so a caption-only edit sends no people and the reverse. */
  const edits = (): PhotoEdits => ({
    ...(captionChanged ? { caption: next } : {}),
    ...(peopleChanged ? { people: peoplePayload(people, ordered) } : {}),
  })

  const submit = (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (unchanged || pending) return
    onSave(edits())
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter alone inserts a newline; Cmd/Ctrl-Enter saves, matching the
    // convention in the rest of the app's text fields.
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      if (!unchanged && !pending) onSave(edits())
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <DialogHeader>
        <DialogTitle>{current ? 'Edit caption' : 'Add caption'}</DialogTitle>
        <DialogDescription>
          Shown under the photo in the gallery and the viewer. It is also the image's alt text. Tagged people link to
          their pages and show this photo on them.
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

      <PhotoPeopleEditor
        universeId={universeId}
        drafts={people}
        ordered={ordered}
        ownerMemberId={media.member_id}
        photoSetIds={photoSetIds}
        disabled={pending}
        onDraftsChange={setPeople}
        onOrderedChange={setOrdered}
      />

      <div className="flex items-center justify-between gap-2 pt-1">
        <div>
          {current && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-red-300 hover:text-red-200"
              disabled={pending}
              onClick={() => onSave({ caption: null })}
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
