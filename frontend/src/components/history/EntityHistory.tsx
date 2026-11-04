// The History tab: one entity's audit trail, newest first. Snapshot rows show
// column changes (long prose as a red/green word diff, everything else as
// old -> new); link rows show what was added to, removed from or changed in one
// of the entity's lists (a member's sets, an incident's participants), and rows
// written on another entity that touched this one ("Member A was added to this
// set") appear too, marked with where they came from.
//
// Default export so detail pages can React.lazy() it: the member page rides in
// the main bundle, and this is admin-only.

import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { History as HistoryIcon, Link2 } from 'lucide-react'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FuzzyDate, type FuzzyDateValue } from '@/components/FuzzyDate'
import { TabPanelSkeleton } from '@/components/skeletons'
import { Button } from '@/components/ui/button'
import { useEntityHistory } from '@/lib/queries'
import { wordDiff } from '@/lib/wordDiff'
import type {
  HistoryEntityType,
  HistoryEntry,
  HistoryFieldChange,
  HistoryLabel,
  HistoryLinkChanged,
} from '@/lib/types'

const PAGE = 25

type Labels = Record<string, HistoryLabel>

const ENTITY_NOUN: Record<string, string> = {
  member: 'member',
  set: 'set',
  alliance: 'alliance',
  incident: 'incident',
  source: 'source',
  gang: 'gang',
  municipality: 'municipality',
}

const LINK_TITLE: Record<string, string> = {
  sets: 'Sets',
  sources: 'Sources',
  cited_by: 'Cited by',
  participants: 'Participants',
  set_participants: 'Set participants',
  gangs: 'Gangs',
  alliances: 'Alliances',
}

function humanize(field: string): string {
  const s = field.replace(/_id$/, '').replace(/_/g, ' ')
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function isFuzzyDate(v: unknown): v is FuzzyDateValue {
  return !!v && typeof v === 'object' && !Array.isArray(v) && 'precision' in (v as object)
}

const linkClass = 'text-violet-300 hover:text-violet-200 hover:underline'

/** A link to any entity the history mentions, or plain text if we have no route for it. */
function EntityLink({ id, labels }: { id: string; labels: Labels }) {
  const l = labels[id]
  if (!l) return <span className="font-mono text-zinc-400">{id.slice(0, 8)}…</span>
  const param = { id: l.slug ?? id }
  switch (l.type) {
    case 'member':
      return <Link from="/$universe" to="/$universe/members/$id" params={param} className={linkClass}>{l.label}</Link>
    case 'set':
      return <Link from="/$universe" to="/$universe/sets/$id" params={param} className={linkClass}>{l.label}</Link>
    case 'alliance':
      return <Link from="/$universe" to="/$universe/alliances/$id" params={param} className={linkClass}>{l.label}</Link>
    case 'gang':
      return <Link from="/$universe" to="/$universe/gangs/$id" params={param} className={linkClass}>{l.label}</Link>
    case 'incident':
      return <Link from="/$universe" to="/$universe/incidents/$id" params={{ id }} className={linkClass}>{l.label}</Link>
    case 'source':
      return <Link from="/$universe" to="/$universe/sources/$id" params={{ id }} className={linkClass}>{l.label}</Link>
    case 'municipality':
      return <Link from="/$universe" to="/$universe/municipalities/$id" params={{ id }} className={linkClass}>{l.label}</Link>
    case 'rap_group':
      return <Link from="/$universe" to="/$universe/rap-groups/$id" params={param} className={linkClass}>{l.label}</Link>
    case 'court_case':
      return <Link from="/$universe" to="/$universe/cases/$id" params={param} className={linkClass}>{l.label}</Link>
    default:
      return <span className="text-zinc-200">{l.label}</span>
  }
}

function Value({ field, value, labels }: { field: string; value: unknown; labels: Labels }) {
  if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
    return <span className="text-zinc-500">—</span>
  }
  if (typeof value === 'string' && field.endsWith('_id') && labels[value]) {
    return <EntityLink id={value} labels={labels} />
  }
  if (typeof value === 'boolean') return <span>{value ? 'yes' : 'no'}</span>
  if (isFuzzyDate(value)) return <FuzzyDate value={value} fallback="unknown" />
  if (Array.isArray(value) && value.every((v) => typeof v === 'string' || typeof v === 'number')) {
    return <span className="break-words">{value.join(', ')}</span>
  }
  if (typeof value === 'object') {
    return <code className="break-all font-mono text-[11px] text-zinc-400">{JSON.stringify(value)}</code>
  }
  return <span className="break-words">{String(value)}</span>
}

function TextDiff({ oldText, newText }: { oldText: string; newText: string }) {
  const parts = wordDiff(oldText, newText)
  return (
    <p className="whitespace-pre-wrap break-words rounded border border-zinc-800 bg-zinc-950 p-2 text-xs leading-relaxed text-zinc-300">
      {parts.map((p, i) =>
        p.op === 'same' ? (
          <span key={i}>{p.text}</span>
        ) : p.op === 'add' ? (
          <ins key={i} className="rounded-sm bg-emerald-500/15 text-emerald-300 no-underline">{p.text}</ins>
        ) : (
          <del key={i} className="rounded-sm bg-rose-500/15 text-rose-300/90">{p.text}</del>
        ),
      )}
    </p>
  )
}

function FieldChanges({ changes, labels, created }: { changes: HistoryFieldChange[]; labels: Labels; created: boolean }) {
  return (
    <dl className="mt-2 space-y-1.5 text-xs">
      {changes.map((c) => (
        <div key={c.field} className="grid gap-1 sm:grid-cols-[9rem_minmax(0,1fr)] sm:gap-3">
          <dt className="text-zinc-400">{humanize(c.field)}</dt>
          <dd className="min-w-0 text-zinc-200">
            {c.kind === 'opaque' ? (
              <span className="text-zinc-400">changed</span>
            ) : c.kind === 'text' ? (
              <TextDiff oldText={typeof c.old === 'string' ? c.old : ''} newText={typeof c.new === 'string' ? c.new : ''} />
            ) : created ? (
              <Value field={c.field} value={c.new} labels={labels} />
            ) : (
              <span className="inline-flex flex-wrap items-baseline gap-1.5">
                <span className="text-rose-300/90 line-through decoration-rose-400/40"><Value field={c.field} value={c.old} labels={labels} /></span>
                <span className="text-zinc-500" aria-label="changed to">→</span>
                <span className="text-emerald-300"><Value field={c.field} value={c.new} labels={labels} /></span>
              </span>
            )}
          </dd>
        </div>
      ))}
    </dl>
  )
}

/** The non-key fields of a link row ("rank: CEO, primary"), skipping empties. */
function RowDetails({ row, keyField, labels }: { row: Record<string, unknown>; keyField: string; labels: Labels }) {
  const fields = Object.entries(row).filter(
    ([k, v]) => k !== keyField && k !== 'position' && v !== null && v !== undefined && v !== '' && v !== false,
  )
  if (fields.length === 0) return null
  return (
    <span className="text-zinc-400">
      {' ('}
      {fields.map(([k, v], i) => (
        <span key={k}>
          {i > 0 && ', '}
          {v === true ? humanize(k).toLowerCase() : <>{humanize(k).toLowerCase()} <Value field={k} value={v} labels={labels} /></>}
        </span>
      ))}
      {')'}
    </span>
  )
}

function Party({ id, entry, labels, self }: { id: string; entry: HistoryEntry; labels: Labels; self: { type: string; id: string } }) {
  // On a row written by another entity every far side is this page's entity.
  if (!entry.is_self || id === self.id) return <span className="text-zinc-200">this {ENTITY_NOUN[self.type] ?? 'entity'}</span>
  return <EntityLink id={id} labels={labels} />
}

function LinkChanges({ entry, labels, self }: { entry: HistoryEntry; labels: Labels; self: { type: string; id: string } }) {
  const key = entry.link_key ?? 'id'
  const title = LINK_TITLE[entry.link ?? ''] ?? humanize(entry.link ?? '')
  return (
    <ul className="mt-2 space-y-1 text-xs">
      {entry.added.map((r) => (
        <li key={`a-${String(r[key])}`}>
          <span className="mr-1.5 font-semibold text-emerald-400">+</span>
          <span className="text-zinc-400">{title}: </span>
          <Party id={String(r[key])} entry={entry} labels={labels} self={self} />
          <RowDetails row={r} keyField={key} labels={labels} />
        </li>
      ))}
      {entry.removed.map((r) => (
        <li key={`r-${String(r[key])}`}>
          <span className="mr-1.5 font-semibold text-rose-400">−</span>
          <span className="text-zinc-400">{title}: </span>
          <span className="line-through decoration-rose-400/40"><Party id={String(r[key])} entry={entry} labels={labels} self={self} /></span>
          <RowDetails row={r} keyField={key} labels={labels} />
        </li>
      ))}
      {entry.changed.map((c: HistoryLinkChanged) => (
        <li key={`c-${c.key}`}>
          <span className="mr-1.5 font-semibold text-amber-400">~</span>
          <span className="text-zinc-400">{title}: </span>
          <Party id={c.key} entry={entry} labels={labels} self={self} />
          <span className="ml-1.5 inline-flex flex-wrap gap-x-3">
            {Object.keys({ ...c.from, ...c.to }).map((f) => (
              <span key={f}>
                <span className="text-zinc-400">{humanize(f).toLowerCase()} </span>
                <span className="text-rose-300/90 line-through decoration-rose-400/40"><Value field={f} value={c.from[f]} labels={labels} /></span>
                <span className="mx-1 text-zinc-500">→</span>
                <span className="text-emerald-300"><Value field={f} value={c.to[f]} labels={labels} /></span>
              </span>
            ))}
          </span>
        </li>
      ))}
    </ul>
  )
}

const ACTION_CLASS: Record<string, string> = {
  CREATE: 'text-emerald-400',
  UPDATE: 'text-amber-400',
  DELETE: 'text-rose-400',
}

function EntryCard({ entry, labels, self }: { entry: HistoryEntry; labels: Labels; self: { type: string; id: string } }) {
  const when = new Date(entry.created_at)
  const verb = entry.link ? 'LINKS' : entry.action
  return (
    <li className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 text-xs">
        <time dateTime={entry.created_at} title={when.toISOString()} className="whitespace-nowrap tabular-nums text-zinc-400">
          {when.toLocaleString()}
        </time>
        <span className={`font-semibold ${entry.link ? 'text-sky-400' : (ACTION_CLASS[entry.action] ?? 'text-zinc-300')}`}>{verb}</span>
        <span className="text-zinc-300">{entry.actor?.email ?? (entry.actor ? `${entry.actor.id.slice(0, 8)}…` : 'system')}</span>
        {!entry.is_self && (
          <span className="inline-flex items-center gap-1 text-zinc-400">
            <Link2 className="h-3 w-3" />
            on {ENTITY_NOUN[entry.entity_type] ?? entry.entity_type} <EntityLink id={entry.entity_id} labels={labels} />
          </span>
        )}
      </div>
      {entry.baseline ? (
        <p className="mt-2 text-xs text-zinc-400">
          First recorded state. Changes before this were made outside the app (seeded or written in SQL) and were not logged.
        </p>
      ) : entry.link ? (
        <LinkChanges entry={entry} labels={labels} self={self} />
      ) : entry.action === 'DELETE' ? (
        <p className="mt-2 text-xs text-zinc-400">Deleted.</p>
      ) : (
        <FieldChanges changes={entry.changes} labels={labels} created={entry.action === 'CREATE'} />
      )}
    </li>
  )
}

export default function EntityHistory({
  entityType,
  entityId,
  universeId,
}: {
  entityType: HistoryEntityType
  entityId: string
  universeId: string | null
}) {
  const [offset, setOffset] = useState(0)
  const { data, isLoading, isError, refetch, isFetching } = useEntityHistory(entityType, entityId, universeId, offset, true)

  if (isLoading) return <TabPanelSkeleton />
  if (isError) return <ErrorState message="Could not load the history." onRetry={() => refetch()} />
  const items = data?.items ?? []
  const total = data?.total ?? 0
  if (total === 0) {
    return (
      <EmptyState
        icon={HistoryIcon}
        title="No recorded changes"
        description="Edits made through the app since the audit log began appear here."
      />
    )
  }
  const self = { type: entityType, id: entityId }
  const atStart = offset === 0
  const atEnd = offset + PAGE >= total
  return (
    <div className={isFetching ? 'opacity-70 transition-opacity' : undefined}>
      <ol className="space-y-2">
        {items.map((e) => (
          <EntryCard key={e.id} entry={e} labels={data?.labels ?? {}} self={self} />
        ))}
      </ol>
      {total > PAGE && (
        <div className="mt-3 flex items-center justify-between text-xs text-zinc-400">
          <span className="tabular-nums">
            {offset + 1}–{Math.min(offset + PAGE, total)} of {total}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" aria-disabled={atStart} disabled={atStart} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
              Newer
            </Button>
            <Button variant="outline" size="sm" aria-disabled={atEnd} disabled={atEnd} onClick={() => setOffset(offset + PAGE)}>
              Older
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
