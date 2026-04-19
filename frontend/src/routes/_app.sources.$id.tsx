import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { FuzzyDate } from '@/components/FuzzyDate'
import { ReliabilityBadge } from '@/components/StatusBadge'
import { ErrorState } from '@/components/ErrorState'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { useSource } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'

export const Route = createFileRoute('/_app/sources/$id')({
  component: SourceDetailPage,
})

function SourceDetailPage() {
  const { id } = Route.useParams()
  const universe = useUniverseStore((s) => s.activeUniverse)
  const { data: source, isLoading, isError, refetch } = useSource(id, universe?.id ?? null)

  if (isError) return <ErrorState title="Source not found" onRetry={() => refetch()} />

  return (
    <div>
      <Link to="/sources" className="mb-4 inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Sources
      </Link>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-24" />
        </div>
      ) : source ? (
        <>
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white">{source.title}</h1>
              {source.publication && <p className="text-sm text-zinc-400">{source.publication}</p>}
              <div className="mt-2 flex items-center gap-2">
                <ReliabilityBadge reliability={source.reliability} />
                {source.published_at && (
                  <span className="text-xs text-zinc-500">
                    Published <FuzzyDate value={source.published_at} />
                  </span>
                )}
              </div>
            </div>
            <a href={source.url} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" size="sm" className="shrink-0 gap-1.5">
                <ExternalLink className="h-3.5 w-3.5" /> Open
              </Button>
            </a>
          </div>

          {source.notes && (
            <div className="mb-4 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{source.notes}</p>
            </div>
          )}

          {source.archive_url && (
            <a
              href={source.archive_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <ExternalLink className="h-3 w-3" /> Archived version
            </a>
          )}
        </>
      ) : null}
    </div>
  )
}
