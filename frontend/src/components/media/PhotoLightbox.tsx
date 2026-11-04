import Lightbox from 'yet-another-react-lightbox'
import Captions from 'yet-another-react-lightbox/plugins/captions'
import 'yet-another-react-lightbox/styles.css'
import 'yet-another-react-lightbox/plugins/captions.css'
import type { MediaOwner, MediaWithUrls } from '@/lib/types'
import { OwnerLink, PhotoPeople } from './PhotoPeople'

/** A photo to show; `owner` is set when it belongs to another page than the one open. */
export type LightboxItem = MediaWithUrls & { owner?: MediaOwner }

interface PhotoLightboxProps {
  items: LightboxItem[]
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
      // Rendered by the Captions plugin below the image. Without the plugin
      // the field is silently ignored, which is how captions used to vanish
      // between the tile and the viewer.
      description:
        m.caption || m.people.length > 0 || m.owner ? (
          <div className="space-y-1">
            {m.caption && <p>{m.caption}</p>}
            <PhotoPeople people={m.people} onNavigate={onClose} />
            {m.owner && (
              <p>
                On <OwnerLink owner={m.owner} onNavigate={onClose} />
              </p>
            )}
          </div>
        ) : undefined,
      width: m.width ?? undefined,
      height: m.height ?? undefined,
    }))

  return (
    <Lightbox
      open={open}
      close={onClose}
      slides={slides}
      index={index}
      plugins={[Captions]}
      captions={{ descriptionTextAlign: 'center', descriptionMaxLines: 4 }}
      controller={{ closeOnBackdropClick: true }}
    />
  )
}
