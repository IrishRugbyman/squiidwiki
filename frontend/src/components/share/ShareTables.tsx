import type { ReactNode } from 'react'
import { formatFuzzyDate } from '@/components/FuzzyDate'
import { INCIDENT_TYPE_CHIP, INCIDENT_TYPE_LABEL } from '@/lib/incidentColors'
import { CASE_KIND_LABEL, courtAndDocket, DISPOSITION_CHIP, DISPOSITION_LABEL, formatSentence } from '@/lib/courtCases'
import type { CourtCaseListItem, IncidentListItem } from '@/lib/types'
import { Dash, Panel } from './ShareCardParts'

const TH = 'px-4 py-2.5 font-medium'

/** Location and municipality, without saying the municipality twice. */
function placeOf(inc: IncidentListItem): string {
  const loc = inc.location_text?.trim() ?? ''
  const muni = inc.municipality_name ?? ''
  if (!loc) return muni
  return muni && !loc.toLowerCase().includes(muni.toLowerCase()) ? `${loc}, ${muni}` : loc
}
const TD = 'px-4 py-2.5'

/** Every incident, one row each. `role` renders the viewer's part on a member card;
 *  a set card leaves it out and the shooters column says who did it. */
export function IncidentsTable({ incidents, role }: {
  incidents: IncidentListItem[]
  role?: (inc: IncidentListItem) => ReactNode
}) {
  return (
    <Panel className="overflow-hidden">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-800 bg-zinc-900 text-xs uppercase tracking-wider text-zinc-400">
            <th className={TH}>Date</th>
            <th className={TH}>Type</th>
            {role && <th className={TH}>Role</th>}
            <th className={TH}>Where</th>
            <th className={TH}>Victims</th>
            <th className={TH}>Shooters</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800">
          {incidents.map((inc) => (
            <tr key={inc.id} className="align-top">
              <td className={`${TD} whitespace-nowrap tabular-nums text-zinc-100`}>
                <span className="inline-flex items-center gap-2">
                  <span className={`h-2 w-2 shrink-0 rounded-full ${inc.verified ? 'bg-emerald-500' : 'bg-transparent'}`} />
                  {formatFuzzyDate(inc.date) ?? 'Undated'}
                </span>
              </td>
              <td className={TD}>
                <span className={`whitespace-nowrap rounded-md border px-2 py-0.5 text-xs font-medium ${INCIDENT_TYPE_CHIP[inc.type]}`}>
                  {INCIDENT_TYPE_LABEL[inc.type]}
                </span>
              </td>
              {role && <td className={TD}>{role(inc)}</td>}
              <td className={`${TD} text-zinc-300`}>
                {placeOf(inc) || <Dash />}
              </td>
              <td className={`${TD} text-zinc-200`}>{inc.victim_names.length ? inc.victim_names.join(', ') : <Dash />}</td>
              <td className={`${TD} text-zinc-200`}>{inc.shooter_names.length ? inc.shooter_names.join(', ') : <Dash />}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {incidents.some((i) => i.verified) && (
        <p className="flex items-center gap-2 border-t border-zinc-800 px-4 py-2 text-xs text-zinc-500">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />Verified
        </p>
      )}
    </Panel>
  )
}

/** Every court case: name, court and docket, and on a member card what it did with him. */
export function CourtCasesTable({ cases }: { cases: CourtCaseListItem[] }) {
  return (
    <Panel className="divide-y divide-zinc-800 overflow-hidden">
      {cases.map((c) => {
        const sentence = formatSentence(c.viewer_sentence_months, c.viewer_life_sentence)
        return (
          <div key={c.id} className="flex items-start gap-4 px-5 py-3">
            <div className="min-w-0 flex-1">
              <p className="text-[15px] font-medium text-zinc-100">{c.name}</p>
              {c.viewer_lead_charge && (
                <p className="text-sm text-zinc-300">
                  {c.viewer_lead_charge}
                  {formatFuzzyDate(c.viewer_offense_date) && <span className="text-zinc-400"> · {formatFuzzyDate(c.viewer_offense_date)}</span>}
                </p>
              )}
              <p className="text-sm text-zinc-400">
                {courtAndDocket(c)}
                {c.kind !== 'CRIMINAL' && <> · {CASE_KIND_LABEL[c.kind]}</>}
                {formatFuzzyDate(c.filed_at) && <> · filed {formatFuzzyDate(c.filed_at)}</>}
                {c.defendant_count > 1 && <> · {c.defendant_count} defendants</>}
              </p>
            </div>
            {c.viewer_disposition && (
              <div className="flex shrink-0 flex-col items-end gap-1">
                <span className={`rounded-md border px-2 py-0.5 text-xs font-medium ${DISPOSITION_CHIP[c.viewer_disposition]}`}>
                  {DISPOSITION_LABEL[c.viewer_disposition]}
                </span>
                {sentence && <span className="text-sm tabular-nums text-zinc-300">{sentence}</span>}
              </div>
            )}
          </div>
        )
      })}
    </Panel>
  )
}
