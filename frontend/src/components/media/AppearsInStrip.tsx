import { useState } from 'react'
import { PanelHeading } from '@/components/detail/DetailParts'
import { useMediaAppearsIn } from '@/lib/queries'
import type { UUID } from '@/lib/types'
import { OwnerLink } from './PhotoPeople'
import { PhotoLightbox } from './PhotoLightbox'

interface AppearsInStripProps {
  memberId: UUID
  universeId: UUID
}

/**
 * Photos a member is tagged in that sit on other pages (a set's, an incident's,
 * another member's). Thumbnails open the same viewer as the gallery, which says
 * whose photo it is and links there. Renders nothing while loading or when there
 * are none, so a member nobody is tagged with shows no empty block.
 */
export function AppearsInStrip({ memberId, universeId }: AppearsInStripProps) {
  const { data } = useMediaAppearsIn(memberId, universeId)
  const [index, setIndex] = useState<number | null>(null)
  const photos = data ?? []
  if (photos.length === 0) return null

  return (
    <section id="appears-in" className="scroll-mt-4" aria-label="Appears in">
      <PanelHeading>Appears in</PanelHeading>
      <ul className="flex gap-3 overflow-x-auto pb-1">
        {photos.map((m, i) => {
          const src = m.thumb_url ?? m.url
          return (
            <li key={m.id} className="w-28 shrink-0 space-y-1">
              <button
                type="button"
                onClick={() => setIndex(i)}
                aria-label={`View photo on ${m.owner.name}`}
                className="block aspect-square w-full overflow-hidden rounded-lg bg-zinc-900 ring-1 ring-zinc-800 transition hover:ring-zinc-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
              >
                {src ? (
                  <img
                    src={src}
                    alt={m.caption ?? `Photo on ${m.owner.name}`}
                    loading="lazy"
                    decoding="async"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="flex h-full w-full items-center justify-center text-xs text-zinc-400">no thumbnail</span>
                )}
              </button>
              <p className="truncate text-[11px] text-zinc-400">
                On <OwnerLink owner={m.owner} />
              </p>
            </li>
          )
        })}
      </ul>

      <PhotoLightbox
        items={photos}
        index={index ?? 0}
        open={index !== null}
        onClose={() => setIndex(null)}
      />
    </section>
  )
}
