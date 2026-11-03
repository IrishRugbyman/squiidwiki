// The pieces a detail page needs for a History tab without paying for it in its
// own chunk: a two-way Overview / History switch built on the shared Tabs
// primitive, and the panel itself, lazy-loaded because only admins open it.
// The set page has tabs of its own and mounts EntityHistory there directly.

import { lazy, Suspense } from 'react'
import { History as HistoryIcon, ListTree } from 'lucide-react'
import { TabPanelSkeleton } from '@/components/skeletons'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { HistoryEntityType } from '@/lib/types'

const EntityHistory = lazy(() => import('./EntityHistory'))

export type DetailView = 'overview' | 'history'

export function DetailViewTabs({ value, onChange }: { value: DetailView; onChange: (v: DetailView) => void }) {
  return (
    <Tabs value={value} onValueChange={(v) => onChange(v as DetailView)}>
      <TabsList className="h-auto w-max bg-zinc-950/50 p-0.5">
        <TabsTrigger value="overview"><ListTree className="mr-1.5 h-3.5 w-3.5" />Overview</TabsTrigger>
        <TabsTrigger value="history"><HistoryIcon className="mr-1.5 h-3.5 w-3.5" />History</TabsTrigger>
      </TabsList>
    </Tabs>
  )
}

export function HistoryPanel(props: { entityType: HistoryEntityType; entityId: string; universeId: string | null }) {
  return (
    <Suspense fallback={<TabPanelSkeleton />}>
      <EntityHistory {...props} />
    </Suspense>
  )
}
