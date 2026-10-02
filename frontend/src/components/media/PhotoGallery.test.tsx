import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import type { MediaWithUrls } from '@/lib/types'
import { HttpResponse, http, server } from '@/test/msw'
import { renderWithClient } from '@/test/utils'
import { normalizeCaption } from './caption'
import { PhotoGallery } from './PhotoGallery'

const UNIVERSE = '11111111-1111-4111-8111-111111111111'
const MEMBER = '22222222-2222-4222-8222-222222222222'
const PHOTO = '33333333-3333-4333-8333-333333333333'

function photo(over: Partial<MediaWithUrls> = {}): MediaWithUrls {
  return {
    id: PHOTO,
    universe_id: UNIVERSE,
    member_id: MEMBER,
    incident_id: null,
    source_id: null,
    set_id: null,
    alliance_id: null,
    municipality_id: null,
    kind: 'R2',
    r2_key: `prod/member/${MEMBER}/${PHOTO}.jpg`,
    thumb_r2_key: `prod/member/${MEMBER}/${PHOTO}_thumb.jpg`,
    external_url: null,
    original_filename: 'scan.jpg',
    content_type: 'image/jpeg',
    size_bytes: 1024,
    width: 800,
    height: 600,
    caption: null,
    is_primary: true,
    created_at: '2026-09-01T00:00:00Z',
    url: 'https://r2.example/scan.jpg',
    thumb_url: 'https://r2.example/scan_thumb.jpg',
    ...over,
  }
}

/** Serves one photo and records the PATCH the gallery sends for it. */
function serveGallery(initial: MediaWithUrls) {
  let current = initial
  const patches: { url: string; body: Record<string, unknown> }[] = []
  server.use(
    http.get('/api/v1/media/', () => HttpResponse.json([current])),
    http.patch(`/api/v1/media/${PHOTO}`, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>
      patches.push({ url: request.url, body })
      current = { ...current, ...body }
      return HttpResponse.json(current)
    }),
  )
  return patches
}

function renderGallery() {
  return renderWithClient(
    <PhotoGallery entityType="member" entityId={MEMBER} universeId={UNIVERSE} hideUpload />,
  )
}

describe('normalizeCaption', () => {
  it('stores whitespace-only input as no caption, not as an empty string', () => {
    expect(normalizeCaption('')).toBeNull()
    expect(normalizeCaption('   \n\t')).toBeNull()
  })

  it('trims the edges and keeps the interior intact', () => {
    expect(normalizeCaption('  Mugshot, 2014  ')).toBe('Mugshot, 2014')
    expect(normalizeCaption('line one\nline two')).toBe('line one\nline two')
  })
})

describe('PhotoGallery captions', () => {
  it('lets a photo with no caption get one, and shows it on the tile once saved', async () => {
    // The backend has accepted a caption on PATCH since the media table was
    // added; this is the control the gallery never had.
    const patches = serveGallery(photo())
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent('Add caption')

    await user.type(screen.getByLabelText('Caption'), 'Mugshot, 2014')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(patches).toHaveLength(1))
    expect(patches[0].body).toEqual({ caption: 'Mugshot, 2014' })
    expect(new URL(patches[0].url).searchParams.get('universe_id')).toBe(UNIVERSE)

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(await screen.findByText('Mugshot, 2014')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit caption' })).toBeInTheDocument()
  })

  it('removing a caption sends null, so the column is cleared rather than emptied', async () => {
    const patches = serveGallery(photo({ caption: 'Old caption' }))
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Edit caption' }))
    expect(await screen.findByLabelText('Caption')).toHaveValue('Old caption')

    await user.click(screen.getByRole('button', { name: 'Remove caption' }))

    await waitFor(() => expect(patches).toHaveLength(1))
    expect(patches[0].body).toEqual({ caption: null })
    await waitFor(() => expect(screen.queryByText('Old caption')).not.toBeInTheDocument())
  })

  it('refuses to save an unchanged caption, so a stray click sends nothing', async () => {
    const patches = serveGallery(photo({ caption: 'Same' }))
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Edit caption' }))
    const field = await screen.findByLabelText('Caption')
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()

    // Only surrounding whitespace differs: still the same caption.
    await user.clear(field)
    await user.type(field, '  Same  ')
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()

    await user.type(field, '!')
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled()
    expect(patches).toHaveLength(0)
  })

  it('keeps the dialog and the draft open when the save fails', async () => {
    server.use(
      http.get('/api/v1/media/', () => HttpResponse.json([photo()])),
      http.patch(`/api/v1/media/${PHOTO}`, () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    await user.type(await screen.findByLabelText('Caption'), 'Lost otherwise')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    // Settle the failed mutation, then check nothing was thrown away.
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled())
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByLabelText('Caption')).toHaveValue('Lost otherwise')
  })
})
