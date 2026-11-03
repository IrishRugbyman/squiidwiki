import { createLazyFileRoute } from '@tanstack/react-router'
import { ChevronDown, ChevronRight, ShieldCheck } from 'lucide-react'
import { useMemo, useState } from 'react'
import { FindingRow } from '@/components/anomalies/FindingRow'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { TabPanelSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { useAnomalies } from '@/lib/queries'
import type { Anomaly } from '@/lib/types'
import { useAuthStore } from '@/stores/auth'
import { useUniverseStore } from '@/stores/universe'

export const Route = createLazyFileRoute('/_app/$universe/anomalies')({
  component: AnomaliesPage,
})

function AnomaliesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.global_role === 'ADMIN'
  const { data, isLoading, isError, refetch, isFetching } = useAnomalies(isAdmin ? universe?.id ?? null : null)
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  const byKind = useMemo(() => {
    const out: Record<string, Anomaly[]> = {}
    for (const a of data?.items ?? []) (out[a.kind] ??= []).push(a)
    return out
  }, [data])

  if (!universe) return <NoUniverse />
  if (!isAdmin) return <ErrorState title="Admins only" message="The anomaly report reads every record in the universe." />

  const total = data?.items.length ?? 0
  const withFindings = (data?.checks ?? []).filter((c) => c.count > 0)
  const clean = (data?.checks ?? []).filter((c) => c.count === 0)

  return (
    <div>
      <PageHeader
        title="Data anomalies"
        description={`Records in ${universe.name} that contradict each other. Each finding links to the page to fix it on.`}
        action={
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            {isFetching ? 'Checking…' : 'Re-run checks'}
          </Button>
        }
      />
      {isLoading ? (
        <TabPanelSkeleton rows={6} />
      ) : isError ? (
        <ErrorState message="Could not run the checks." onRetry={() => refetch()} />
      ) : total === 0 ? (
        <EmptyState icon={ShieldCheck} title="No anomalies" description={`All ${data?.checks.length ?? 0} checks came back clean.`} />
      ) : (
        <div className="space-y-4">
          {withFindings.map((c) => {
            const open = !collapsed[c.kind]
            return (
              <section key={c.kind} className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
                <button
                  type="button"
                  onClick={() => setCollapsed((s) => ({ ...s, [c.kind]: open }))}
                  aria-expanded={open}
                  className="flex w-full items-center gap-2 px-4 py-3 text-left hover:bg-zinc-900/60"
                >
                  {open ? <ChevronDown className="h-4 w-4 text-zinc-400" /> : <ChevronRight className="h-4 w-4 text-zinc-400" />}
                  <span className="text-sm font-medium text-zinc-100">{c.title}</span>
                  <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-amber-300">{c.count}</span>
                  <code className="ml-auto hidden font-mono text-[10px] text-zinc-500 sm:inline">{c.kind}</code>
                </button>
                {open && (
                  <ul className="divide-y divide-zinc-800 border-t border-zinc-800">
                    {(byKind[c.kind] ?? []).map((a, i) => (
                      <FindingRow key={`${a.entity_id}-${a.related_id ?? ''}-${i}`} a={a} />
                    ))}
                  </ul>
                )}
              </section>
            )
          })}
          {clean.length > 0 && (
            <p className="text-xs text-zinc-400">
              Clean: {clean.map((c) => c.title).join(' · ')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
