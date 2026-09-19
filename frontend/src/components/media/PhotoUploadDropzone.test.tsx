import { act, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { HttpResponse, http, server } from '@/test/msw'
import { renderWithClient } from '@/test/utils'
import { PhotoUploadDropzone } from './PhotoUploadDropzone'

const UNIVERSE = '11111111-1111-4111-8111-111111111111'
const MEMBER = '22222222-2222-4222-8222-222222222222'
const OTHER = '44444444-4444-4444-8444-444444444444'

/** Counts media uploads, keyed by the entity each one was attached to. */
function serveUploads() {
  const uploads: string[] = []
  server.use(
    http.post('/api/v1/media/', async ({ request }) => {
      const form = await request.formData()
      uploads.push(String(form.get('member_id')))
      return HttpResponse.json({ id: 'm' }, { status: 201 })
    }),
  )
  return uploads
}

/** A real paste event carrying one PNG, dispatched on `target`. */
function pasteImage(target: EventTarget) {
  const file = new File([new Uint8Array([137, 80, 78, 71])], 'shot.png', { type: 'image/png' })
  // jsdom has no DataTransfer; this is the part of it the handler reads.
  const data = { items: [{ kind: 'file', type: file.type, getAsFile: () => file }] }
  const event = new Event('paste', { bubbles: true, cancelable: true }) as ClipboardEvent
  Object.defineProperty(event, 'clipboardData', { value: data })
  act(() => {
    target.dispatchEvent(event)
  })
  return event
}

describe('PhotoUploadDropzone paste', () => {
  it('uploads an image pasted on the page without focusing the zone first', async () => {
    const uploads = serveUploads()
    renderWithClient(<PhotoUploadDropzone entityType="member" entityId={MEMBER} universeId={UNIVERSE} />)
    const event = pasteImage(document.body)
    await waitFor(() => expect(uploads).toEqual([MEMBER]))
    expect(event.defaultPrevented).toBe(true)
  })

  it('leaves a paste into a text field alone', async () => {
    const uploads = serveUploads()
    renderWithClient(
      <>
        <input aria-label="caption" />
        <PhotoUploadDropzone entityType="member" entityId={MEMBER} universeId={UNIVERSE} />
      </>,
    )
    const event = pasteImage(screen.getByLabelText('caption'))
    await new Promise((r) => setTimeout(r, 50))
    expect(uploads).toEqual([])
    expect(event.defaultPrevented).toBe(false)
  })

  it('uploads once, to the most recently mounted zone, when two are on screen', async () => {
    const uploads = serveUploads()
    renderWithClient(
      <>
        <PhotoUploadDropzone entityType="member" entityId={OTHER} universeId={UNIVERSE} />
        <PhotoUploadDropzone entityType="member" entityId={MEMBER} universeId={UNIVERSE} />
      </>,
    )
    pasteImage(document.body)
    await waitFor(() => expect(uploads).toEqual([MEMBER]))
    await new Promise((r) => setTimeout(r, 50))
    expect(uploads).toEqual([MEMBER])
  })

  it('ignores a paste while a dialog that does not hold the zone is open', async () => {
    const uploads = serveUploads()
    renderWithClient(
      <>
        <PhotoUploadDropzone entityType="member" entityId={MEMBER} universeId={UNIVERSE} />
        <div role="dialog" data-state="open">
          <p>unrelated dialog</p>
        </div>
      </>,
    )
    pasteImage(screen.getByText('unrelated dialog'))
    await new Promise((r) => setTimeout(r, 50))
    expect(uploads).toEqual([])
  })
})
