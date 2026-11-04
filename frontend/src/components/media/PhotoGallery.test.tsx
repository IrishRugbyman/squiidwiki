import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { MediaPerson, MediaWithUrls } from '@/lib/types'
import { HttpResponse, http, server } from '@/test/msw'
import { renderWithClient } from '@/test/utils'
import { normalizeCaption } from './caption'
import { PhotoGallery } from './PhotoGallery'

// The gallery links to members; a real router is not needed to read where.
vi.mock('@tanstack/react-router', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@tanstack/react-router')>()),
  Link: ({ to, params, children, className, onClick }: {
    to: string
    params: Record<string, string>
    children: React.ReactNode
    className?: string
    onClick?: () => void
  }) => (
    <a href={to.replace('$id', params.id)} className={className} onClick={onClick}>
      {children}
    </a>
  ),
}))

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
    people: [],
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

const TAY = '55555555-5555-4555-8555-555555555555'
const DOE = '66666666-6666-4666-8666-666666666666'

function person(over: Partial<MediaPerson> & Pick<MediaPerson, 'member_id' | 'display_name'>): MediaPerson {
  return { slug: null, nickname: over.display_name, legal_name: null, position: null, ...over }
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

describe('PhotoGallery people', () => {
  it('lists an ordered photo as "Tay, Doe", each name a link to the member', async () => {
    serveGallery(
      photo({
        people: [
          person({ member_id: TAY, display_name: 'Tay', slug: 'tay', position: 0 }),
          person({ member_id: DOE, display_name: 'Doe', position: 1 }),
        ],
      }),
    )
    renderGallery()

    const line = await screen.findByTestId('photo-people')
    expect(line).toHaveTextContent(/^Tay, Doe$/)
    expect(screen.getByRole('link', { name: 'Tay' })).toHaveAttribute('href', '/$universe/members/tay')
    // No slug: the link falls back to the id.
    expect(screen.getByRole('link', { name: 'Doe' })).toHaveAttribute('href', `/$universe/members/${DOE}`)
  })

  it('prefixes "With" when the order is unknown', async () => {
    serveGallery(
      photo({
        people: [
          person({ member_id: TAY, display_name: 'Tay', position: null }),
          person({ member_id: DOE, display_name: 'Doe', position: null }),
        ],
      }),
    )
    renderGallery()
    expect(await screen.findByTestId('photo-people')).toHaveTextContent(/^With Tay, Doe$/)
  })

  it('shows no people line for a photo nobody is tagged in', async () => {
    serveGallery(photo({ caption: 'Alone' }))
    renderGallery()
    await screen.findByText('Alone')
    expect(screen.queryByTestId('photo-people')).not.toBeInTheDocument()
  })
})

/** Serves the gallery, a member search, and records the PUT .../people the dialog sends. */
function servePeople(initial: MediaWithUrls, searchResults: { id: string; display_name: string }[] = []) {
  let current = initial
  const puts: { body: { universe_id: string; people: { member_id: string; position: number | null }[] } }[] = []
  const patches: Record<string, unknown>[] = []
  server.use(
    http.get('/api/v1/media/', () => HttpResponse.json([current])),
    http.patch(`/api/v1/media/${PHOTO}`, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>
      patches.push(body)
      current = { ...current, ...body }
      return HttpResponse.json(current)
    }),
    http.put(`/api/v1/media/${PHOTO}/people`, async ({ request }) => {
      const body = (await request.json()) as (typeof puts)[number]['body']
      puts.push({ body })
      current = {
        ...current,
        people: body.people.map((p) =>
          person({
            member_id: p.member_id,
            display_name: p.member_id === TAY ? 'Tay' : 'Doe',
            position: p.position,
          }),
        ),
      }
      return HttpResponse.json(current)
    }),
    http.get('/api/v1/members/search', () => HttpResponse.json(searchResults)),
  )
  return { puts, patches }
}

describe('PhotoCaptionDialog people editor', () => {
  it('tags a member found by search, in order, with one PUT and no caption PATCH', async () => {
    const { puts, patches } = servePeople(photo(), [
      { id: TAY, display_name: 'Tay' },
      { id: DOE, display_name: 'Doe' },
    ])
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    expect(screen.getByText('People in this photo')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()

    for (const name of ['Tay', 'Doe']) {
      await user.type(screen.getByLabelText('Search members to tag'), name)
      await user.click(await screen.findByRole('option', { name: new RegExp(name) }))
    }
    expect(screen.getByRole('button', { name: 'Move Tay down' })).toBeEnabled()
    await user.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(puts).toHaveLength(1))
    expect(puts[0].body).toEqual({
      universe_id: UNIVERSE,
      people: [
        { member_id: TAY, position: 0 },
        { member_id: DOE, position: 1 },
      ],
    })
    expect(patches).toHaveLength(0)
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(await screen.findByTestId('photo-people')).toHaveTextContent(/^Tay, Doe$/)
  })

  it('reorders with up/down and removes a person', async () => {
    const { puts } = servePeople(
      photo({
        people: [
          person({ member_id: TAY, display_name: 'Tay', position: 0 }),
          person({ member_id: DOE, display_name: 'Doe', position: 1 }),
        ],
      }),
    )
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    // The first cannot go further up, the last further down.
    expect(screen.getByRole('button', { name: 'Move Tay up' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Move Doe down' })).toBeDisabled()

    await user.click(screen.getByRole('button', { name: 'Move Doe up' }))
    await user.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(puts).toHaveLength(1))
    expect(puts[0].body.people).toEqual([
      { member_id: DOE, position: 0 },
      { member_id: TAY, position: 1 },
    ])

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    await user.click(await screen.findByRole('button', { name: 'Remove Doe' }))
    await user.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(puts).toHaveLength(2))
    expect(puts[1].body.people).toEqual([{ member_id: TAY, position: 0 }])
  })

  it('"Order unknown" saves every position as null', async () => {
    const { puts } = servePeople(
      photo({
        people: [
          person({ member_id: TAY, display_name: 'Tay', position: 0 }),
          person({ member_id: DOE, display_name: 'Doe', position: 1 }),
        ],
      }),
    )
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    await user.click(screen.getByLabelText('Order unknown'))
    // With no order there is nothing to move.
    expect(screen.queryByRole('button', { name: 'Move Tay down' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(puts).toHaveLength(1))
    expect(puts[0].body.people).toEqual([
      { member_id: TAY, position: null },
      { member_id: DOE, position: null },
    ])
    expect(await screen.findByTestId('photo-people')).toHaveTextContent(/^With /)
  })

  it('does not offer the member the photo belongs to, nor one already tagged', async () => {
    servePeople(
      photo({ people: [person({ member_id: DOE, display_name: 'Doe', position: 0 })] }),
      [
        { id: MEMBER, display_name: 'Owner Man' },
        { id: DOE, display_name: 'Doe Again' },
        { id: TAY, display_name: 'Tay Fresh' },
      ],
    )
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    await user.type(screen.getByLabelText('Search members to tag'), 'ta')
    expect(await screen.findByRole('option', { name: /Tay Fresh/ })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /Owner Man/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /Doe Again/ })).not.toBeInTheDocument()
  })

  it('sends only the caption when only the caption changed', async () => {
    const { puts, patches } = servePeople(
      photo({ people: [person({ member_id: TAY, display_name: 'Tay', position: 0 })] }),
    )
    const user = userEvent.setup()
    renderGallery()

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    await user.type(screen.getByLabelText('Caption'), 'Block party')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(patches).toEqual([{ caption: 'Block party' }]))
    expect(puts).toHaveLength(0)
  })
})

describe('PhotoCaptionDialog people search', () => {
  it('lists the member of the photo set first, under its own heading, and every match after', async () => {
    const SET = '77777777-7777-4777-8777-777777777777'
    const many = Array.from({ length: 12 }, (_, i) => ({
      id: `88888888-8888-4888-8888-${String(i).padStart(12, '0')}`,
      display_name: `Ken ${String.fromCharCode(65 + i)}`,
      aliases: null,
      affiliations: [],
    }))
    const setKen = {
      id: TAY,
      display_name: 'Kenny',
      aliases: null,
      affiliations: [{ set_id: SET, set_name: 'Craft', is_primary: true }],
      primary_set_id: SET,
      primary_set_name: 'Craft',
    }
    server.use(
      http.get('/api/v1/media/', () =>
        HttpResponse.json([photo({ member_id: null, set_id: SET, r2_key: `prod/set/${SET}/x.jpg` })]),
      ),
      // The backend returns matches unordered: the set's man comes last here.
      http.get('/api/v1/members/search', () => HttpResponse.json([...many, setKen])),
    )
    const user = userEvent.setup()
    renderWithClient(<PhotoGallery entityType="set" entityId={SET} universeId={UNIVERSE} hideUpload />)

    await user.click(await screen.findByRole('button', { name: 'Add caption' }))
    await user.type(screen.getByLabelText('Search members to tag'), 'ken')
    const options = await screen.findAllByRole('option')
    expect(options).toHaveLength(13)
    expect(options[0]).toHaveTextContent('Kenny')
    expect(options[0]).toHaveTextContent('Craft')
    expect(screen.getByText("In this photo's set")).toBeInTheDocument()
    expect(screen.getByText('Everyone else')).toBeInTheDocument()
  })
})
