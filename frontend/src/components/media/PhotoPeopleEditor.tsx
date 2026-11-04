import { ArrowDown, ArrowUp, X } from 'lucide-react'
import { useId, useState } from 'react'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Label } from '@/components/ui/label'
import { useDebounce } from '@/hooks/useDebounce'
import { useMemberSearch } from '@/lib/queries'
import type { UUID } from '@/lib/types'
import { move, rankPeople, type PersonDraft, type RankedPerson } from './people'

/**
 * How many hits the list renders. The list scrolls, so this is only a ceiling
 * against a two-letter query matching half the universe; past it the footer
 * asks for more letters.
 */
const RESULTS = 50

interface PhotoPeopleEditorProps {
  universeId: UUID
  drafts: PersonDraft[]
  /** True when the list is left to right; false saves every position as null. */
  ordered: boolean
  /** The member the photo belongs to: it is already on his page, so he is not offered. */
  ownerMemberId: UUID | null
  /** Sets the photo belongs to: their members are listed first, since they are who it shows. */
  photoSetIds?: ReadonlySet<UUID>
  disabled?: boolean
  onDraftsChange: (next: PersonDraft[]) => void
  onOrderedChange: (next: boolean) => void
}

/**
 * Who is in the photo: a member search, the tagged people in a list, with
 * up/down to put them left to right, remove, and an "order unknown" switch.
 */
export function PhotoPeopleEditor({
  universeId,
  drafts,
  ordered,
  ownerMemberId,
  photoSetIds = NO_SETS,
  disabled,
  onDraftsChange,
  onOrderedChange,
}: PhotoPeopleEditorProps) {
  const unknownId = useId()
  const [q, setQ] = useState('')
  const dq = useDebounce(q.trim(), 250)
  const results = useMemberSearch(universeId, dq).data

  const taken = new Set<UUID>(drafts.map((d) => d.member_id))
  if (ownerMemberId) taken.add(ownerMemberId)
  const ranked = rankPeople(
    (results ?? []).filter((m) => !taken.has(m.id)),
    dq,
    photoSetIds,
  )
  const shown = ranked.slice(0, RESULTS)
  const inSet = shown.filter((r) => r.inPhotoSet)
  const others = shown.filter((r) => !r.inPhotoSet)
  const searching = dq.length >= 2

  const add = (r: RankedPerson) => {
    onDraftsChange([...drafts, { member_id: r.member.id, display_name: r.member.display_name }])
    setQ('')
  }

  return (
    <div className="space-y-2">
      <Label>People in this photo</Label>

      <Command shouldFilter={false} className="h-auto rounded-md border border-zinc-800">
        <CommandInput
          placeholder="Search a member to add…"
          aria-label="Search members to tag"
          value={q}
          onValueChange={setQ}
          disabled={disabled}
        />
        {searching && (
          // Capped well below the dialog so the list scrolls on its own, with
          // the tagged people and Save still reachable under it on a phone.
          <CommandList className="max-h-[min(18rem,40vh)] overscroll-contain">
            {shown.length === 0 && <CommandEmpty>No members for "{dq}"</CommandEmpty>}
            {inSet.length > 0 && (
              <CommandGroup heading="In this photo's set">
                {inSet.map((r) => (
                  <PersonOption key={r.member.id} person={r} onSelect={() => add(r)} />
                ))}
              </CommandGroup>
            )}
            {others.length > 0 && (
              <CommandGroup heading={inSet.length > 0 ? 'Everyone else' : undefined}>
                {others.map((r) => (
                  <PersonOption key={r.member.id} person={r} onSelect={() => add(r)} />
                ))}
              </CommandGroup>
            )}
            {ranked.length > shown.length && (
              <p className="px-3 py-2 text-[11px] text-zinc-500">
                {ranked.length - shown.length} more match "{dq}": type more of the name.
              </p>
            )}
          </CommandList>
        )}
      </Command>

      {drafts.length > 0 && (
        <ul className="divide-y divide-zinc-800 rounded-md border border-zinc-800">
          {drafts.map((d, i) => (
            <li key={d.member_id} className="flex items-center gap-2 px-2.5 py-1.5 text-sm">
              {ordered && <span className="w-4 shrink-0 text-[11px] tabular-nums text-zinc-500">{i + 1}</span>}
              <span className="min-w-0 flex-1 truncate">{d.display_name}</span>
              {ordered && (
                <>
                  <button
                    type="button"
                    disabled={disabled || i === 0}
                    onClick={() => onDraftsChange(move(drafts, i, i - 1))}
                    aria-label={`Move ${d.display_name} up`}
                    title="Move left"
                    className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-30 disabled:hover:bg-transparent"
                  >
                    <ArrowUp className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    disabled={disabled || i === drafts.length - 1}
                    onClick={() => onDraftsChange(move(drafts, i, i + 1))}
                    aria-label={`Move ${d.display_name} down`}
                    title="Move right"
                    className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-30 disabled:hover:bg-transparent"
                  >
                    <ArrowDown className="h-3.5 w-3.5" />
                  </button>
                </>
              )}
              <button
                type="button"
                disabled={disabled}
                onClick={() => onDraftsChange(drafts.filter((x) => x.member_id !== d.member_id))}
                aria-label={`Remove ${d.display_name}`}
                title="Remove"
                className="rounded p-1 text-zinc-400 hover:bg-red-900/50 hover:text-red-200 disabled:opacity-30"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="flex items-center gap-2">
        <input
          id={unknownId}
          type="checkbox"
          checked={!ordered}
          disabled={disabled}
          onChange={(e) => onOrderedChange(!e.target.checked)}
          className="h-3.5 w-3.5 accent-violet-500"
        />
        <label htmlFor={unknownId} className="text-xs text-zinc-300">
          Order unknown
        </label>
        <span className="text-[11px] text-zinc-500">
          {ordered ? 'Listed left to right.' : 'Shown as "With …", alphabetically.'}
        </span>
      </div>

    </div>
  )
}

const NO_SETS: ReadonlySet<UUID> = new Set()

/** One search hit: face, name, set, so two men called Ken can be told apart. */
function PersonOption({ person, onSelect }: { person: RankedPerson; onSelect: () => void }) {
  const m = person.member
  const thumb = m.primary_photo_thumb_url ?? m.primary_photo_url
  const others = (m.affiliations ?? []).filter((a) => a.set_id !== m.primary_set_id && a.set_name).length
  return (
    <CommandItem value={`member-${m.id}`} onSelect={onSelect} className="gap-2.5 py-1.5">
      {thumb ? (
        <img src={thumb} alt="" loading="lazy" className="h-8 w-8 shrink-0 rounded-md object-cover ring-1 ring-zinc-800" />
      ) : (
        <span
          aria-hidden
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-zinc-800 text-xs font-medium text-zinc-400"
        >
          {m.display_name.slice(0, 1).toUpperCase()}
        </span>
      )}
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm">{m.display_name}</span>
        <span className="truncate text-[11px] text-zinc-500">
          {m.primary_set_name ?? 'No set'}
          {others > 0 && ` +${others}`}
          {m.aliases && m.aliases.length > 0 && ` · ${m.aliases.join(', ')}`}
        </span>
      </span>
    </CommandItem>
  )
}
