import { useCallback, useEffect, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { ImagePlus, Loader2, Upload, X } from 'lucide-react'
import { toast } from 'sonner'
import { PhotoUploadDropzone } from '@/components/media/PhotoUploadDropzone'
import type { UUID } from '@/lib/types'

const MAX_BYTES = 10 * 1024 * 1024

interface QueuedFile {
  file: File
  preview: string
}

interface PhotoSectionProps {
  /**
   * In edit mode (member exists), uploads happen immediately and become
   * the primary photo if none is set. In create mode, files are queued and
   * uploaded by the parent after the member is created.
   */
  mode: 'create' | 'edit'
  universeId: UUID
  /** Required in edit mode (existing member id) */
  memberId?: UUID
  /** Create mode only: queued files reported up so the parent can flush after POST */
  queuedFiles?: File[]
  onQueuedFilesChange?: (files: File[]) => void
}

export function PhotoSection({ mode, universeId, memberId, queuedFiles = [], onQueuedFilesChange }: PhotoSectionProps) {
  if (mode === 'edit' && memberId) {
    return (
      <PhotoUploadDropzone entityType="member" entityId={memberId} universeId={universeId} />
    )
  }
  return <QueueDropzone files={queuedFiles} onChange={onQueuedFilesChange ?? (() => {})} />
}

function QueueDropzone({ files, onChange }: { files: File[]; onChange: (files: File[]) => void }) {
  const [previews, setPreviews] = useState<QueuedFile[]>([])

  // Sync previews with files whenever the parent's array changes (e.g. reset).
  useEffect(() => {
    setPreviews((prev) => {
      const stillUsed = new Map(prev.map((p) => [p.file, p]))
      const next = files.map((file) => {
        const existing = stillUsed.get(file)
        if (existing) {
          stillUsed.delete(file)
          return existing
        }
        return { file, preview: URL.createObjectURL(file) }
      })
      // Revoke previews for files no longer in the list.
      for (const stale of stillUsed.values()) URL.revokeObjectURL(stale.preview)
      return next
    })
  }, [files])

  // Final cleanup on unmount.
  useEffect(() => {
    return () => {
      setPreviews((current) => {
        for (const p of current) URL.revokeObjectURL(p.preview)
        return []
      })
    }
  }, [])

  const handleDrop = useCallback(
    (dropped: File[]) => {
      const accepted: File[] = []
      for (const f of dropped) {
        if (f.size > MAX_BYTES) {
          toast.error(`${f.name}: file is over 10 MB`)
          continue
        }
        accepted.push(f)
      }
      if (accepted.length > 0) onChange([...files, ...accepted])
    },
    [files, onChange],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [], 'image/gif': [] },
    maxSize: MAX_BYTES,
    multiple: true,
  })

  function remove(idx: number) {
    onChange(files.filter((_, i) => i !== idx))
  }

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        tabIndex={0}
        className={`relative cursor-pointer rounded-lg border border-dashed p-6 text-center transition-colors outline-none focus-visible:ring-2 focus-visible:ring-violet-500 ${
          isDragActive
            ? 'border-violet-500 bg-violet-950/30'
            : 'border-zinc-700 bg-zinc-900/30 hover:border-zinc-600 hover:bg-zinc-900/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2 text-sm text-zinc-400">
          {isDragActive ? (
            <>
              <Upload className="h-6 w-6 text-violet-400" />
              <span>Drop the image here</span>
            </>
          ) : (
            <>
              <ImagePlus className="h-6 w-6 text-zinc-500" />
              <span>Drop, click, or paste an image</span>
              <span className="text-xs text-zinc-600">
                {previews.length > 0
                  ? `${previews.length} queued — first becomes primary on save`
                  : 'JPEG / PNG / WebP / GIF — up to 10 MB'}
              </span>
            </>
          )}
        </div>
      </div>
      {previews.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {previews.map((p, idx) => (
            <div key={`${p.file.name}-${idx}`} className="relative h-20 w-20 overflow-hidden rounded-md border border-zinc-700">
              <img src={p.preview} alt={p.file.name} className="h-full w-full object-cover" />
              {idx === 0 && (
                <span className="absolute left-0 top-0 rounded-br bg-violet-700 px-1 py-0.5 text-[9px] font-bold uppercase text-white">
                  primary
                </span>
              )}
              <button
                type="button"
                aria-label={`Remove ${p.file.name}`}
                onClick={(e) => { e.stopPropagation(); remove(idx) }}
                className="absolute right-0.5 top-0.5 rounded-full bg-zinc-900/90 p-0.5 text-zinc-300 hover:bg-rose-700 hover:text-white"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/** Used by the parent on submit to flush the queue after member creation. */
export async function flushPhotoQueue(opts: {
  files: File[]
  memberId: UUID
  universeId: UUID
  api: { postFormData: <T>(path: string, body: FormData) => Promise<T> }
}) {
  const { files, memberId, universeId, api } = opts
  if (files.length === 0) return { uploaded: 0, failed: 0 }
  let uploaded = 0
  let failed = 0
  for (const file of files) {
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('universe_id', universeId)
      fd.append('member_id', memberId)
      await api.postFormData('/media/', fd)
      uploaded++
    } catch {
      failed++
    }
  }
  if (uploaded > 0) {
    toast.success(uploaded === 1 ? 'Uploaded photo' : `Uploaded ${uploaded} photos`)
  }
  if (failed > 0) {
    toast.error(`${failed} photo${failed === 1 ? '' : 's'} failed to upload — retry from the Photos tab`)
  }
  return { uploaded, failed }
}

// Show a stable spinner alongside the section header while a queue is flushing.
export function PhotoFlushSpinner({ active }: { active: boolean }) {
  if (!active) return null
  return <Loader2 className="h-3.5 w-3.5 animate-spin text-violet-400" />
}
