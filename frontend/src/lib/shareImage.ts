/**
 * Turning a share card into a PNG, and getting that PNG into a chat.
 *
 * Photos are presigned R2 URLs, and R2 sends no CORS headers, so a canvas that
 * drew them directly would be tainted and refuse to export. Cards therefore
 * render their photos as `<img data-share-src>` with no `src`, and
 * `inlineShareImages` fills each one with a data URL fetched through the
 * backend's same-origin `/media/proxy` before the capture runs.
 */

const PROXY = '/api/v1/media/proxy?url='
const FETCH_CONCURRENCY = 8

/** iOS Safari refuses a canvas over 16,777,216 pixels; stay under it everywhere. */
const MAX_CANVAS_AREA = 16_000_000
const MAX_SCALE = 2

/** Card background, painted under everything so no edge is transparent. */
export const SHARE_BG = '#09090b'

async function toDataUrl(url: string): Promise<string> {
  const token = localStorage.getItem('access_token')
  const res = await fetch(PROXY + encodeURIComponent(url), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`photo ${res.status}`)
  const blob = await res.blob()
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(blob)
  })
}

/** Load every `img[data-share-src]` under `root` from this origin. A photo that
 *  fails is dropped from the card rather than failing the whole image. */
export async function inlineShareImages(root: HTMLElement): Promise<void> {
  const imgs = Array.from(root.querySelectorAll<HTMLImageElement>('img[data-share-src]'))
  const cache = new Map<string, Promise<string>>()
  let next = 0
  async function worker() {
    while (next < imgs.length) {
      const img = imgs[next++]
      const src = img.dataset.shareSrc!
      try {
        if (!cache.has(src)) cache.set(src, toDataUrl(src))
        img.src = await cache.get(src)!
        await img.decode()
      } catch {
        img.removeAttribute('src')
        img.style.visibility = 'hidden'
      }
    }
  }
  await Promise.all(Array.from({ length: Math.min(FETCH_CONCURRENCY, imgs.length) }, worker))
}

/** Rasterise a mounted card. The scale is as sharp as the canvas limit allows. */
export async function renderCardToPng(node: HTMLElement): Promise<Blob> {
  const { domToBlob } = await import('modern-screenshot')
  await inlineShareImages(node)
  await document.fonts.ready
  const width = node.offsetWidth
  const height = node.offsetHeight
  const scale = Math.min(MAX_SCALE, Math.sqrt(MAX_CANVAS_AREA / (width * height)))
  return await domToBlob(node, { scale, width, height, backgroundColor: SHARE_BG, type: 'image/png' })
}

export function shareFileName(name: string): string {
  const safe = name.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  return `${safe || 'card'}.png`
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

/** A phone or tablet, where the system share sheet is the way into a chat app. */
export function prefersShareSheet(): boolean {
  return typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches
}

export function canShareFile(file: File): boolean {
  return typeof navigator.canShare === 'function' && navigator.canShare({ files: [file] })
}

/** True where an image can be put on the clipboard from a click. */
export function canCopyImage(): boolean {
  return typeof ClipboardItem !== 'undefined' && !!navigator.clipboard?.write
}
