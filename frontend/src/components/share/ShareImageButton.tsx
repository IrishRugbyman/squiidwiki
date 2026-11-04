import { lazy, Suspense, useCallback, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { ImageDown, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { useUniverseStore } from '@/stores/universe'
import type { UUID } from '@/lib/types'
import {
  canCopyImage, canShareFile, downloadBlob, prefersShareSheet, renderCardToPng, shareFileName,
} from '@/lib/shareImage'

// The cards are their own chunk: nothing about them loads until the button is used.
const CARDS = {
  member: lazy(() => import('./MemberShareCard')),
  set: lazy(() => import('./SetShareCard')),
  alliance: lazy(() => import('./AllianceShareCard')),
}

const READY_TIMEOUT_MS = 30_000

interface Deferred<T> { promise: Promise<T>; resolve: (v: T) => void; reject: (e: unknown) => void }
function deferred<T>(): Deferred<T> {
  let resolve!: (v: T) => void
  let reject!: (e: unknown) => void
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}

/**
 * Renders a member, set or alliance as one PNG holding everything the page does, then puts it
 * where a chat can take it: the system share sheet on a phone, the clipboard on a
 * desktop (paste it into the conversation), a download when neither is available.
 */
export function ShareImageButton({ kind, id, name }: { kind: keyof typeof CARDS; id: UUID; name: string }) {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [rendering, setRendering] = useState(false)
  const hostRef = useRef<HTMLDivElement>(null)
  const ready = useRef<Deferred<void> | null>(null)

  const onReady = useCallback(() => ready.current?.resolve(), [])

  async function capture(): Promise<Blob> {
    ready.current = deferred<void>()
    setRendering(true)
    const timeout = setTimeout(() => ready.current?.reject(new Error('timed out loading the data')), READY_TIMEOUT_MS)
    try {
      await ready.current.promise
      // One frame for React to commit the last data, one for layout.
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
      const node = hostRef.current?.firstElementChild as HTMLElement | null
      if (!node) throw new Error('nothing rendered')
      return await renderCardToPng(node)
    } finally {
      clearTimeout(timeout)
      setRendering(false)
    }
  }

  async function handleClick() {
    if (rendering || !universe) return
    const filename = shareFileName(name)
    const blob = deferred<Blob>()

    // A desktop clipboard write has to start inside the click, so it is handed
    // the PNG as a promise before the capture begins.
    const useClipboard = !prefersShareSheet() && canCopyImage()
    const copied = useClipboard
      ? navigator.clipboard.write([new ClipboardItem({ 'image/png': blob.promise })]).then(() => true, () => false)
      : Promise.resolve(false)

    let png: Blob
    try {
      png = await capture()
      blob.resolve(png)
    } catch (err) {
      blob.reject(err)
      toast.error(`Could not make the image: ${err instanceof Error ? err.message : 'unknown error'}`)
      return
    }

    if (useClipboard) {
      if (await copied) {
        toast.success('Image copied. Paste it into the chat.', {
          action: { label: 'Download', onClick: () => downloadBlob(png, filename) },
        })
      } else {
        downloadBlob(png, filename)
        toast.success('Image downloaded')
      }
      return
    }

    const file = new File([png], filename, { type: 'image/png' })
    if (!canShareFile(file)) {
      downloadBlob(png, filename)
      toast.success('Image downloaded')
      return
    }
    const share = async () => {
      try {
        await navigator.share({ files: [file] })
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        // The tap that started this expired while the image was being made:
        // offer a fresh tap rather than failing.
        if (err instanceof DOMException && err.name === 'NotAllowedError') {
          toast('Image ready', { action: { label: 'Share', onClick: () => { void share() } }, duration: 20_000 })
          return
        }
        downloadBlob(png, filename)
      }
    }
    await share()
  }

  const Card = CARDS[kind]
  return (
    <>
      <Button size="sm" variant="outline" onClick={handleClick} disabled={rendering || !universe} title="Share as image" aria-label="Share as image" className="px-2">
        {rendering ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImageDown className="h-4 w-4" />}
      </Button>
      {rendering && universe && createPortal(
        // Laid out at full size but off-screen: the capture reads real layout.
        <div ref={hostRef} aria-hidden style={{ position: 'fixed', left: -100_000, top: 0, pointerEvents: 'none' }}>
          <Suspense fallback={null}>
            <Card id={id} universeId={universe.id} universeName={universe.name} onReady={onReady} />
          </Suspense>
        </div>,
        document.body,
      )}
    </>
  )
}
