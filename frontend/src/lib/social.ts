// Social accounts on a member.
//
// A platform key holds either one account or several. Duce has four Instagram
// handles across the years and the single-string shape could only ever carry the
// last one, so both shapes are accepted: `"handle"` and `["handle", "handle"]`.
// Everything here flattens to one entry per account so the UI can list them.
//
// Lives in lib/ rather than beside the member detail route because the member
// form sheet needs the type too, and that route already imports the sheet.

export type SocialMap = Record<string, string | string[]> | null | undefined

export interface SocialEntry {
  platform: string
  raw: string
  /** Stable React key: several accounts share a platform, so the index is part of it. */
  key: string
}

export function socialEntries(social: SocialMap): SocialEntry[] {
  if (!social) return []
  const out: SocialEntry[] = []
  for (const [platform, value] of Object.entries(social)) {
    const list = Array.isArray(value) ? value : [value]
    list.forEach((v, i) => {
      const raw = typeof v === 'string' ? v.trim() : ''
      if (raw) out.push({ platform, raw, key: `${platform}-${i}` })
    })
  }
  return out
}

const SOCIAL_HOST_REGEX = /^https?:\/\/([^/]+)/i

export function extractHost(url: string): string | null {
  return url.match(SOCIAL_HOST_REGEX)?.[1] ?? null
}

export type SocialPlatform = 'facebook' | 'instagram' | 'twitter'

const SOCIAL_HOSTS: Record<SocialPlatform, RegExp> = {
  facebook: /^(?:https?:\/\/)?(?:www\.|m\.)?facebook\.com\//i,
  instagram: /^(?:https?:\/\/)?(?:www\.)?instagram\.com\//i,
  twitter: /^(?:https?:\/\/)?(?:www\.)?(?:twitter|x)\.com\//i,
}

export const SOCIAL_BASE: Record<SocialPlatform, string> = {
  facebook: 'https://facebook.com/',
  instagram: 'https://instagram.com/',
  twitter: 'https://x.com/',
}

/**
 * A Facebook account that never took a vanity URL is addressable only as
 * `profile.php?id=<numeric id>`. The id is the whole address, so it has to
 * survive normalization and be recognisable on display.
 */
const FACEBOOK_NUMERIC_ID = /(?:^|[?&])id=(\d+)/

function facebookNumericId(value: string): string | undefined {
  if (!/profile\.php/i.test(value)) return undefined
  return value.match(FACEBOOK_NUMERIC_ID)?.[1]
}

/**
 * Strip protocol/host/@ to a bare handle. Empty input -> empty output.
 *
 * Everything after the first `/`, `?` or `#` is query junk on every other form
 * of profile URL (`?locale=`, `?mibextid=`, a `/photos` suffix), so it goes. The
 * one exception is `profile.php?id=N`, where cutting at the `?` leaves
 * `profile.php`, which addresses nobody.
 */
export function normalizeHandle(platform: SocialPlatform, raw: string): string {
  const trimmed = raw.trim()
  if (!trimmed) return ''
  const path = trimmed.replace(SOCIAL_HOSTS[platform], '').replace(/^@/, '')
  const numericId = facebookNumericId(path)
  if (numericId) return `profile.php?id=${numericId}`
  return path.replace(/[/?#].*$/, '')
}

/**
 * Label for one account chip. With several accounts under a single platform the
 * platform name is the one thing that cannot tell them apart, so the handle is
 * what gets shown. URLs are reduced to their last path segment.
 */
export function socialHandle(value: string): string {
  const v = value.trim()
  // The numeric id is what tells two vanity-less accounts apart; `profile.php`
  // is shared by all of them and identifies none.
  const numericId = facebookNumericId(v)
  if (numericId) return `@${numericId}`
  if (!v.startsWith('http')) return `@${v.replace(/^@/, '')}`
  try {
    const segments = new URL(v).pathname.split('/').filter(Boolean)
    const last = segments[segments.length - 1]
    // A segment with a dot is a file (profile.php), not a handle.
    if (last && !last.includes('.')) return `@${last}`
  } catch {
    return v
  }
  return extractHost(v) ?? v
}

/** Comma-separated input, because handles cannot contain a comma. */
export function splitSocial(value: string): string[] {
  return value.split(',').map((v) => v.trim()).filter(Boolean)
}
