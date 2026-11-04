import { createLazyFileRoute, useNavigate } from '@tanstack/react-router'
import { Gavel, Plus, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { CourtCaseRow } from '@/components/cases/CasesPanel'
import { EmptyState } from '@/components/EmptyState'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useDebounce } from '@/hooks/useDebounce'
import { JURISDICTION_LABEL, JURISDICTIONS } from '@/lib/courtCases'
import { useCourtCases } from '@/lib/queries'
import type { CourtJurisdiction } from '@/lib/types'
import { useUniverseStore } from '@/stores/universe'
import { CourtCaseFormSheet } from './_app.$universe.cases.index'

// The court cases list, in its own chunk; the route file keeps validateSearch
// and the form sheet, which the member, set, incident and alliance pages open.
export const Route = createLazyFileRoute('/_app/$universe/cases/')({
  component: CourtCasesPage,
})

const ALL = '__all__'
const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

function CourtCasesPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const search = Route.useSearch()
  const navigate = useNavigate({ from: '/$universe/cases/' })
  const { data: cases = [], isLoading } = useCourtCases(universe?.id ?? null)
  const [query, setQuery] = useState(search.q ?? '')
  const debounced = useDebounce(query, 150)
  const [jurisdiction, setJurisdiction] = useState<CourtJurisdiction | typeof ALL>(ALL)
  const [creating, setCreating] = useState(false)

  const shown = useMemo(() => {
    const q = fold(debounced.trim())
    return cases.filter((c) =>
      (jurisdiction === ALL || c.jurisdiction === jurisdiction)
      && (!q || fold([c.name, c.court, c.docket ?? ''].join(' ')).includes(q)),
    )
  }, [cases, debounced, jurisdiction])

  if (!universe) return <NoUniverse />

  function setQ(v: string) {
    setQuery(v)
    navigate({ search: (prev) => ({ ...prev, q: v || undefined }), replace: true })
  }

  return (
    <div className="space-y-4 pb-8">
      <PageHeader
        title="Court cases"
        description={isLoading ? undefined : `${cases.length.toLocaleString()} in ${universe.name}`}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-3.5 w-3.5" />New case</Button>}
      />
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-0 flex-1 sm:max-w-sm">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" aria-hidden />
          <Input value={query} onChange={(e) => setQ(e.target.value)} placeholder="Name, court or docket" className="pl-8" aria-label="Filter cases" />
          {query && (
            <button type="button" onClick={() => setQ('')} aria-label="Clear the filter" className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-zinc-500 hover:text-zinc-200">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <Select value={jurisdiction} onValueChange={(v) => { if (v) setJurisdiction(v as CourtJurisdiction | typeof ALL) }}>
          <SelectTrigger className="w-40" aria-label="Jurisdiction"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All jurisdictions</SelectItem>
            {JURISDICTIONS.map((j) => <SelectItem key={j} value={j}>{JURISDICTION_LABEL[j]}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}</div>
      ) : shown.length === 0 ? (
        <EmptyState
          icon={Gavel}
          title={cases.length === 0 ? 'No court cases yet' : 'No case matches'}
          description={cases.length === 0
            ? 'A case holds a prosecution: its court and docket, who was charged and how it ended, and the incidents it covers.'
            : 'Try another name, court or docket number.'}
          action={cases.length === 0 ? <Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-3.5 w-3.5" />New case</Button> : undefined}
        />
      ) : (
        <div className="divide-y divide-zinc-800/70 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/30">
          {shown.map((c) => <CourtCaseRow key={c.id} c={c} />)}
        </div>
      )}

      {creating && (
        <CourtCaseFormSheet
          universeId={universe.id}
          open
          onClose={() => setCreating(false)}
          onSaved={(c) => navigate({ to: '/$universe/cases/$id', params: { universe: universe.slug, id: c.slug ?? c.id } })}
        />
      )}
    </div>
  )
}
