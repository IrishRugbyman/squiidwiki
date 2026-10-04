import {
  AtSign, BookOpen, FolderLock, Landmark, Link2, Lock, Map as MapIcon, Newspaper, Video,
  type LucideIcon,
} from 'lucide-react'
import type { LookupSystem, SourceKind } from '@/lib/types'

/** How each kind of source is labelled and drawn, in the order a record groups them. */
export const KIND_META: Record<SourceKind, { label: string; plural: string; icon: LucideIcon }> = {
  COURT: { label: 'Court & government', plural: 'Court & government', icon: Landmark },
  PRESS: { label: 'Press', plural: 'Press', icon: Newspaper },
  CUSTODY: { label: 'Custody record', plural: 'Custody records', icon: Lock },
  SOCIAL: { label: 'Social media', plural: 'Social media', icon: AtSign },
  VIDEO: { label: 'Video & music', plural: 'Video & music', icon: Video },
  WIKI: { label: 'Wiki & blog', plural: 'Wikis & blogs', icon: BookOpen },
  MAP: { label: 'Map', plural: 'Maps', icon: MapIcon },
  INTERNAL: { label: 'Research file', plural: 'Research files', icon: FolderLock },
  OTHER: { label: 'Other', plural: 'Other', icon: Link2 },
}

export const KIND_ORDER: SourceKind[] = [
  'COURT', 'PRESS', 'CUSTODY', 'SOCIAL', 'VIDEO', 'WIKI', 'MAP', 'INTERNAL', 'OTHER',
]

export const LOOKUP_LABEL: Record<LookupSystem, string> = {
  BOP: 'BOP register',
  MDOC_OTIS: 'MDOC',
  GDC: 'GDC',
}

/** True for a URL the browser can open; the research's own `research-file:` and
 *  `r2:` references are not. */
export function isValidUrl(url: string | null | undefined): url is string {
  if (!url) return false
  try {
    const u = new URL(url)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

/** The host without `www.`, or null. */
export function domainOf(url: string | null | undefined): string | null {
  if (!isValidUrl(url)) return null
  return new URL(url).hostname.replace(/^www\./, '') || null
}

/** Where a lookup record can be opened again from its number. Only the BOP
 *  locator answers a plain GET; OTIS and GDC keep the record in session state. */
export function lookupDeepLink(system: LookupSystem | null, locator: string | null): string | null {
  if (system === 'BOP' && locator && /^\d{5}-\d{3}$/.test(locator.trim())) {
    return `https://www.bop.gov/PublicInfo/execute/inmateloc?todo=query&output=json&inmateNum=${locator.trim()}&inmateNumType=IRN`
  }
  return null
}
