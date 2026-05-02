import { useState } from 'react'
import { Star, Trash2, Loader2 } from 'lucide-react'
import { useMedia, useUpdateMedia, useDeleteMedia } from '@/lib/queries'
import type { MediaEntityType, MediaWithUrls, UUID } from '@/lib/types'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { EmptyState } from '@/components/EmptyState'
import { PhotoUploadDropzone } from './PhotoUploadDropzone'
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

  const photos = items ?? []
  const confirmTarget = photos.find((m) => m.id === confirmDeleteId)

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
              onDelete={() => setConfirmDeleteId(m.id)}
              setPrimaryPending={
                updateMedia.isPending && updateMedia.variables?.id === m.id
              }
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
  onDelete: () => void
  setPrimaryPending: boolean
  deletePending: boolean
}

function PhotoTile({ media, onClick, onSetPrimary, onDelete, setPrimaryPending, deletePending }: PhotoTileProps) {
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
          <div className="flex h-full w-full items-center justify-center text-xs text-zinc-600">no thumbnail</div>
        )}
      </button>

      {media.is_primary && (
        <div className="pointer-events-none absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-violet-600/90 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white shadow">
          <Star className="h-3 w-3 fill-current" />
          Primary
        </div>
      )}

      <div className="absolute inset-x-0 bottom-0 flex items-center justify-end gap-1 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-2 opacity-0 transition-opacity group-hover:opacity-100">
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
            onDelete()
          }}
          disabled={deletePending}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-zinc-800/90 text-red-300 ring-1 ring-zinc-700 hover:bg-red-900/60 hover:text-red-200 disabled:opacity-50"
          title="Delete photo"
        >
          {deletePending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
        </button>
      </div>

      {media.caption && (
        <div className="pointer-events-none absolute inset-x-0 top-0 truncate bg-gradient-to-b from-black/70 to-transparent px-2 py-1 text-[11px] text-zinc-200 opacity-0 transition-opacity group-hover:opacity-100">
          {media.caption}
        </div>
      )}
    </div>
  )
}
