import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { MediaAppearance } from '@/lib/types'
import { HttpResponse, http, server } from '@/test/msw'
import { renderWithClient } from '@/test/utils'
import { AppearsInStrip } from './AppearsInStrip'

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
const SET = '77777777-7777-4777-8777-777777777777'
const INCIDENT = '88888888-8888-4888-8888-888888888888'

function appearance(id: string, owner: MediaAppearance['owner'], over: Partial<MediaAppearance> = {}): MediaAppearance {
  return {
    id,
    universe_id: UNIVERSE,
    member_id: null,
    incident_id: null,
    source_id: null,
    set_id: null,
    alliance_id: null,
    municipality_id: null,
    kind: 'EXTERNAL_URL',
    r2_key: null,
    thumb_r2_key: null,
    external_url: `https://img.example/${id}.jpg`,
    original_filename: null,
    content_type: null,
    size_bytes: null,
    width: 800,
    height: 600,
    caption: null,
    is_primary: false,
    created_at: '2026-09-01T00:00:00Z',
    url: `https://img.example/${id}.jpg`,
    thumb_url: `https://img.example/${id}_t.jpg`,
    people: [],
    owner,
    ...over,
  }
}

function serve(items: MediaAppearance[]) {
  const seen: URLSearchParams[] = []
  server.use(
    http.get('/api/v1/media/appears-in', ({ request }) => {
      seen.push(new URL(request.url).searchParams)
      return HttpResponse.json(items)
    }),
  )
  return seen
}

describe('AppearsInStrip', () => {
  it('renders nothing when the member is tagged in no photo of another page', async () => {
    const seen = serve([])
    const { container } = renderWithClient(<AppearsInStrip memberId={MEMBER} universeId={UNIVERSE} />)
    await waitFor(() => expect(seen).toHaveLength(1))
    expect(seen[0].get('member_id')).toBe(MEMBER)
    expect(seen[0].get('universe_id')).toBe(UNIVERSE)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows a thumbnail per photo, each labelled with the page it sits on', async () => {
    serve([
      appearance('a1', { type: 'set', id: SET, name: 'Maple Street', slug: 'maple-street' }),
      appearance('b2', { type: 'incident', id: INCIDENT, name: '2022, 7 Mile', slug: null }),
    ])
    renderWithClient(<AppearsInStrip memberId={MEMBER} universeId={UNIVERSE} />)

    expect(await screen.findByRole('heading', { name: 'Appears in' })).toBeInTheDocument()
    expect(screen.getAllByRole('img')).toHaveLength(2)
    expect(screen.getByRole('link', { name: 'Maple Street' })).toHaveAttribute('href', '/$universe/sets/maple-street')
    expect(screen.getByRole('link', { name: '2022, 7 Mile' })).toHaveAttribute('href', `/$universe/incidents/${INCIDENT}`)
  })

  it('opens the viewer on the clicked photo with "On <owner>" linking back', async () => {
    serve([
      appearance('a1', { type: 'set', id: SET, name: 'Maple Street', slug: 'maple-street' }, { caption: 'Cookout' }),
    ])
    const user = userEvent.setup()
    renderWithClient(<AppearsInStrip memberId={MEMBER} universeId={UNIVERSE} />)

    await user.click(await screen.findByRole('button', { name: 'View photo on Maple Street' }))

    const viewer = await screen.findByRole('dialog')
    expect(viewer.querySelector('.yarl__slide_description')).toHaveTextContent('Cookout')
    const description = viewer.querySelector('.yarl__slide_description') as HTMLElement
    const link = within(description).getByRole('link', { name: 'Maple Street' })
    expect(link).toHaveAttribute('href', '/$universe/sets/maple-street')
    expect(link.closest('p')).toHaveTextContent(/^On Maple Street$/)
  })
})
