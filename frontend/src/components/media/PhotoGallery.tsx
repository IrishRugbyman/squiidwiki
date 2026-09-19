import { useState } from 'react'
import { Captions, Star, Trash2, Loader2 } from 'lucide-react'
import { useMedia, useUpdateMedia, useDeleteMedia } from '@/lib/queries'
import type { MediaEntityType, MediaWithUrls, UUID } from '@/lib/types'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { PhotoUploadDropzone } from './PhotoUploadDropzone'
import { PhotoCaptionDialog } from './PhotoCaptionDialog'
import { PhotoLightbox } from './PhotoLightbox'

interface PhotoGalleryProps {
  entityType: MediaEntityType
  entityId: UUID
  universeId: UUID
  /** Hide the upload dropzone (e.g. when the parent already has its own uploader). */
  hideUpload?: boolean
}

export function PhotoGallery({ entityType, entityId, universeId, hideUpload }: PhotoGalleryProps) {
  const { data: items, isLoading } = useMedia(entityType, entityId, universeId)
  const updateMedia = useUpdateMedia(entityType, entityId, universeId)
  const deleteMedia = useDeleteMedia(entityType, entityId, universeId)

  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<UUID | null>(null)
  const [captionTargetId, setCaptionTargetId] = useState<UUID | null>(null)

  const photos = items ?? []
  const confirmTarget = photos.find((m) => m.id === confirmDeleteId)
  const captionTarget = photos.find((m) => m.id === captionTargetId) ?? null

  // One mutation hook serves both the primary toggle and the caption editor,
  // so each control's spinner is gated on the payload that control sends.
  const pendingVars = updateMedia.isPending ? updateMedia.variables : undefined
  const captionPendingId = pendingVars?.caption !== undefined ? pendingVars.id : null
  const primaryPendingId = pendingVars?.is_primary !== undefined ? pendingVars.id : null

  return (
    <div className="space-y-4">
      {!hideUpload && (
        <PhotoUploadDropzone entityType={entityType} entityId={entityId} universeId={universeId} />
      )}

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="aspect-square animate-pulse rounded-lg bg-zinc-900/60" />
          ))}
        </div>
      ) : photos.length === 0 ? (
        <EmptyState
          title="No photos yet"
          description={hideUpload ? 'Upload an image to start the gallery.' : 'Drop, click, or paste an image above to start the gallery.'}
        />
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {photos.map((m, i) => (
            <PhotoTile
              key={m.id}
              media={m}
              onClick={() => setLightboxIndex(i)}
              onSetPrimary={() => updateMedia.mutate({ id: m.id, is_primary: true })}
              onEditCaption={() => setCaptionTargetId(m.id)}
              onDelete={() => setConfirmDeleteId(m.id)}
              setPrimaryPending={primaryPendingId === m.id}
              captionPending={captionPendingId === m.id}
              deletePending={deleteMedia.isPending && deleteMedia.variables === m.id}
            />
          ))}
        </div>
      )}

      <PhotoLightbox
        items={photos}
        index={lightboxIndex ?? 0}
        open={lightboxIndex !== null}
        onClose={() => setLightboxIndex(null)}
      />

      <PhotoCaptionDialog
        media={captionTarget}
        open={captionTargetId !== null}
        pending={captionPendingId !== null}
        onSave={(caption) => {
          if (!captionTarget) return
          updateMedia.mutate(
            { id: captionTarget.id, caption },
            // On error the global mutation handler toasts and the dialog stays
            // open with the draft intact, so nothing typed is lost.
            { onSuccess: () => setCaptionTargetId(null) },
          )
        }}
        onCancel={() => setCaptionTargetId(null)}
      />

      <ConfirmDialog
        open={confirmDeleteId !== null}
        title="Delete photo?"
        description={
          confirmTarget?.is_primary
            ? 'This is the primary photo. The next-most-recent photo will become primary.'
            : 'The image will be removed from the gallery.'
        }
        confirmLabel="Delete"
        destructive
        pending={deleteMedia.isPending}
        onConfirm={() => {
          if (confirmDeleteId) {
            deleteMedia.mutate(confirmDeleteId, {
              onSettled: () => setConfirmDeleteId(null),
            })
          }
        }}
        onCancel={() => setConfirmDeleteId(null)}
      />
    </div>
  )
}

interface PhotoTileProps {
  media: MediaWithUrls
  onClick: () => void
  onSetPrimary: () => void
  onEditCaption: () => void
  onDelete: () => void
  setPrimaryPending: boolean
  captionPending: boolean
  deletePending: boolean
}

function PhotoTile({
  media,
  onClick,
  onSetPrimary,
  onEditCaption,
  onDelete,
  setPrimaryPending,
  captionPending,
  deletePending,
}: PhotoTileProps) {
  const thumbSrc = media.thumb_url ?? media.url
  return (
    <div className="group relative aspect-square overflow-hidden rounded-lg bg-zinc-900 ring-1 ring-zinc-800">
      <button
        type="button"
        onClick={onClick}
        aria-label={media.caption ?? 'View photo'}
        className="absolute inset-0 h-full w-full"
      >
        {thumbSrc ? (
          <img
            src={thumbSrc}
            alt={media.caption ?? media.original_filename ?? 'photo'}
            loading="lazy"
            decoding="async"
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs text-zinc-400">no thumbnail</div>
        )}
      </button>

      {media.is_primary && (
        <div className="pointer-events-none absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-violet-600/90 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white shadow">
          <Star className="h-3 w-3 fill-current" />
          Primary
        </div>
      )}

      {/* The caption strip and the action bar share the bottom edge: the strip
          is what a resting tile shows, and hovering (or tabbing into) the tile
          swaps it for the controls. The full caption is in the lightbox. */}
      {media.caption && (
        <div className="pointer-events-none absolute inset-x-0 bottom-0 truncate bg-gradient-to-t from-black/80 via-black/50 to-transparent px-2 pb-1.5 pt-4 text-[11px] leading-tight text-zinc-100 transition-opacity group-hover:opacity-0 group-focus-within:opacity-0">
          {media.caption}
        </div>
      )}

      <div className="absolute inset-x-0 bottom-0 flex items-center justify-end gap-1 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-2 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        {!media.is_primary && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onSetPrimary()
            }}
            disabled={setPrimaryPending}
            className="inline-flex h-7 items-center gap-1 rounded-md bg-zinc-800/90 px-2 text-[11px] text-zinc-100 ring-1 ring-zinc-700 hover:bg-zinc-700 disabled:opacity-50"
            title="Set as primary photo"
          >
            {setPrimaryPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Star className="h-3 w-3" />}
            Primary
          </button>
        )}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onEditCaption()
          }}
          disabled={captionPending}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-zinc-800/90 text-zinc-100 ring-1 ring-zinc-700 hover:bg-zinc-700 disabled:opacity-50"
          title={media.caption ? 'Edit caption' : 'Add caption'}
          aria-label={media.caption ? 'Edit caption' : 'Add caption'}
        >
          {captionPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Captions className="h-3.5 w-3.5" />}
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          disabled={deletePending}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-zinc-800/90 text-red-300 ring-1 ring-zinc-700 hover:bg-red-900/60 hover:text-red-200 disabled:opacity-50"
          title="Delete photo"
        >
          {deletePending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  )
}
