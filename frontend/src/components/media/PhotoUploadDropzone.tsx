import { useCallback, useState } from 'react'
import type React from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, ImagePlus, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useUploadMedia } from '@/lib/queries'
import type { MediaEntityType, UUID } from '@/lib/types'

interface PhotoUploadDropzoneProps {
  entityType: MediaEntityType
  entityId: UUID
  universeId: UUID
}

const MAX_BYTES = 10 * 1024 * 1024

export function PhotoUploadDropzone({ entityType, entityId, universeId }: PhotoUploadDropzoneProps) {
  const upload = useUploadMedia(entityType, entityId, universeId)
  const [pasteHover, setPasteHover] = useState(false)

  const handleFiles = useCallback(
    async (files: File[]) => {
      // Sequential uploads — server enforces 10MB cap and image/* mime; the
      // global mutation onError toasts any failures via sonner.
      for (const file of files) {
        if (file.size > MAX_BYTES) {
          toast.error(`${file.name}: file is over 10 MB`)
          continue
        }
        await upload.mutateAsync({ file }).catch(() => undefined)
      }
    },
    [upload],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFiles,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [], 'image/gif': [] },
    maxSize: MAX_BYTES,
    noKeyboard: false,
    multiple: true,
  })

  const onPaste = useCallback(
    (e: React.ClipboardEvent<HTMLDivElement>) => {
      const items = e.clipboardData?.items
      if (!items) return
      const files: File[] = []
      for (const item of items) {
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          const f = item.getAsFile()
          if (f) files.push(f)
        }
      }
      if (files.length > 0) {
        e.preventDefault()
        void handleFiles(files)
      }
    },
    [handleFiles],
  )

  const isUploading = upload.isPending

  return (
    <div
      {...getRootProps()}
      onPaste={onPaste}
      onMouseEnter={() => setPasteHover(true)}
      onMouseLeave={() => setPasteHover(false)}
      tabIndex={0}
      className={`relative rounded-lg border border-dashed transition-colors p-6 text-center cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-violet-500 ${
        isDragActive
          ? 'border-violet-500 bg-violet-950/30'
          : 'border-zinc-700 bg-zinc-900/30 hover:border-zinc-600 hover:bg-zinc-900/50'
      }`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-2 text-sm text-zinc-400">
        {isUploading ? (
          <>
            <Loader2 className="h-6 w-6 animate-spin text-violet-400" />
            <span>Uploading…</span>
          </>
        ) : isDragActive ? (
          <>
            <Upload className="h-6 w-6 text-violet-400" />
            <span>Drop the image here</span>
          </>
        ) : (
          <>
            <ImagePlus className="h-6 w-6 text-zinc-500" />
            <span>
              Drop, click, {pasteHover ? <span className="text-violet-300">or paste (⌘/Ctrl-V)</span> : 'or paste an image'}
            </span>
            <span className="text-xs text-zinc-600">JPEG / PNG / WebP / GIF — up to 10 MB</span>
          </>
        )}
      </div>
    </div>
  )
}
