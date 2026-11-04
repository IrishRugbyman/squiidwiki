import { Link } from '@tanstack/react-router'
import { Archive, ChevronDown, ExternalLink, Quote } from 'lucide-react'
import { useState } from 'react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { LinkifiedText } from '@/components/LinkifiedText'
import { ReliabilityDot } from '@/components/sources/ReliabilityDot'
import { KIND_META, LOOKUP_LABEL, isValidUrl, lookupDeepLink } from '@/lib/sourceMeta'
import type { CitationRead, SourceSummary } from '@/lib/types'
import { cn } from '@/lib/utils'

interface SourceCardProps {
  source: SourceSummary
  /** The citation this card shows the source for: its locator, quote and note
   *  open under the card. Absent on a plain source listing. */
  citation?: Pick<CitationRead, 'locator' | 'quote' | 'note' | 'accessed_at'>
  /** Row actions, right-aligned (the panel's menu). */
  actions?: React.ReactNode
  className?: string
}

/**
 * One source, compact: what kind it is and where it lives, its title, who
 * published it and when, how reliable it is, and the ways to open it. The
 * citation's detail (where in the source, the quoted words, what it
 * supports here) unfolds beneath.
 */
export function SourceCard({ source, citation, actions, className }: SourceCardProps) {
  const [open, setOpen] = useState(false)
  const kind = KIND_META[source.kind] ?? KIND_META.OTHER
  const KindIcon = kind.icon
  const lookup = source.lookup_system
  const deepLink = lookupDeepLink(lookup, citation?.locator ?? null)
  const href = deepLink ?? (isValidUrl(source.url) ? source.url : null)
  const hasDetail = !!citation && !!(citation.quote || citation.note || (citation.accessed_at && !lookup))
  const where = citation?.locator
    ? lookup ? `${LOOKUP_LABEL[lookup]} ${citation.locator}` : citation.locator
    : null

  return (
    <div className={cn('group px-3 py-2.5 transition-colors hover:bg-zinc-900/50', className)}>
      <div className="flex items-start gap-3">
        <span
          className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-zinc-800/80 text-zinc-400"
          title={kind.label}
        >
          <KindIcon className="h-3.5 w-3.5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <ReliabilityDot reliability={source.reliability} />
            <Link
              from="/$universe"
              to="/$universe/sources/$id"
              params={{ id: source.id }}
              className="min-w-0 truncate text-sm text-zinc-100 hover:text-violet-400"
              title={source.title}
            >
              {source.title}
            </Link>
          </div>
          <div className="mt-0.5 flex flex-wrap items-center gap-x-1.5 text-xs text-zinc-400">
            {source.publication && <span className="truncate">{source.publication}</span>}
            {source.domain && source.domain !== source.publication?.toLowerCase() && (
              <>
                {source.publication && <span aria-hidden>·</span>}
                <span className="truncate text-zinc-500">{source.domain}</span>
              </>
            )}
            {source.published_at?.year && (
              <>
                <span aria-hidden>·</span>
                <FuzzyDate value={source.published_at} />
              </>
            )}
            {where && (
              <>
                <span aria-hidden>·</span>
                <span className="font-mono text-zinc-300">{where}</span>
              </>
            )}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-0.5">
          {hasDetail && (
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              aria-expanded={open}
              aria-label={open ? 'Hide what this source supports' : 'Show what this source supports'}
              className="rounded p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
            >
              {citation?.quote ? <Quote className="h-3.5 w-3.5" /> : (
                <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', open && 'rotate-180')} />
              )}
            </button>
          )}
          {source.archive_url && isValidUrl(source.archive_url) && (
            <a
              href={source.archive_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Open the archived copy of ${source.title}`}
              title="Archived copy"
              className="rounded p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
            >
              <Archive className="h-3.5 w-3.5" />
            </a>
          )}
          {href && (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Open ${source.title} in a new tab`}
              className="rounded p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
          {actions}
        </div>
      </div>
      {open && citation && (
        <div className="ml-9 mt-2 space-y-1.5 border-l-2 border-zinc-800 pl-3 text-sm">
          {citation.quote && (
            <blockquote className="whitespace-pre-wrap text-zinc-300 italic">“{citation.quote}”</blockquote>
          )}
          {citation.note && (
            <p className="whitespace-pre-wrap text-zinc-400">
              <LinkifiedText text={citation.note} />
            </p>
          )}
          {citation.accessed_at && (
            <p className="text-xs text-zinc-500">Read {citation.accessed_at}</p>
          )}
        </div>
      )}
    </div>
  )
}
