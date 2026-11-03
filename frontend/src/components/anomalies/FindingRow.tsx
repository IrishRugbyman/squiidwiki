// One row of the anomaly report: the entity with the problem, what is wrong,
// and the other record it contradicts, each linking to its page.

import { Link } from '@tanstack/react-router'
import type { Anomaly } from '@/lib/types'

const linkClass = 'text-violet-300 hover:text-violet-200 hover:underline'

function EntityLink({ type, id, slug, label }: { type: string; id: string; slug: string | null; label: string }) {
  const param = { id: slug ?? id }
  switch (type) {
    case 'member':
      return <Link from="/$universe" to="/$universe/members/$id" params={param} className={linkClass}>{label}</Link>
    case 'set':
      return <Link from="/$universe" to="/$universe/sets/$id" params={param} className={linkClass}>{label}</Link>
    case 'incident':
      return <Link from="/$universe" to="/$universe/incidents/$id" params={{ id }} className={linkClass}>{label}</Link>
    default:
      return <span className="text-zinc-200">{label}</span>
  }
}

export function FindingRow({ a }: { a: Anomaly }) {
  return (
    <li className="flex flex-col gap-0.5 px-4 py-2.5 sm:flex-row sm:items-baseline sm:gap-3">
      <span className="shrink-0 font-medium sm:w-56 sm:truncate">
        <EntityLink type={a.entity_type} id={a.entity_id} slug={a.slug} label={a.display_name} />
      </span>
      <span className="min-w-0 flex-1 text-xs text-zinc-300">{a.message}</span>
      {a.related_id && a.related_type && a.related_label && (
        <span className="shrink-0 text-xs">
          <EntityLink type={a.related_type} id={a.related_id} slug={null} label={a.related_label} />
        </span>
      )}
    </li>
  )
}

