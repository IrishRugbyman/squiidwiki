import Lightbox from 'yet-another-react-lightbox'
import 'yet-another-react-lightbox/styles.css'
import type { MediaWithUrls } from '@/lib/types'

interface PhotoLightboxProps {
  items: MediaWithUrls[]
  index: number
  open: boolean
  onClose: () => void
}

export function PhotoLightbox({ items, index, open, onClose }: PhotoLightboxProps) {
  const slides = items
    .filter((m) => m.url)
    .map((m) => ({
      src: m.url!,
      alt: m.caption ?? m.original_filename ?? 'photo',
      title: m.caption ?? undefined,
      width: m.width ?? undefined,
      height: m.height ?? undefined,
    }))

  return (
    <Lightbox
      open={open}
      close={onClose}
      slides={slides}
      index={index}
      controller={{ closeOnBackdropClick: true }}
    />
  )
}
