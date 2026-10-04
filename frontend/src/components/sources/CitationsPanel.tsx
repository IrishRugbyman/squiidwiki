import { ArrowDown, ArrowUp, FileText, MoreHorizontal, Pencil, Plus, Unlink } from 'lucide-react'
import { useMemo, useState } from 'react'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { PanelHeading } from '@/components/detail/DetailParts'
import { CitationEditDialog } from '@/components/sources/CitationEditDialog'
import { SourceCard } from '@/components/sources/SourceCard'
import { SourcePicker } from '@/components/sources/SourcePicker'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useDeleteCitation, useReorderCitations } from '@/lib/queries'
import { KIND_META, KIND_ORDER } from '@/lib/sourceMeta'
import type { CitableType, CitationRead, SourceKind, UUID } from '@/lib/types'

interface CitationsPanelProps {
  universeId: UUID
  entityType: CitableType
  entityId: UUID
  citations: CitationRead[]
  /** False hides the Cite button and row menus (reserved sets, read-only views). */
  editable?: boolean
  title?: string
}

/**
 * A record's sources, the same on every page: grouped by kind (court records
 * before press before social posts), in the order the record cites them, each
 * opening onto what it supports here. Cite, edit, reorder and detach in place.
 */
export function CitationsPanel({
  universeId, entityType, entityId, citations, editable = true, title = 'Sources',
}: CitationsPanelProps) {
  const [citing, setCiting] = useState(false)
  const [editing, setEditing] = useState<CitationRead | null>(null)
  const [detaching, setDetaching] = useState<CitationRead | null>(null)
  const detach = useDeleteCitation(universeId, entityType)
  const reorder = useReorderCitations(universeId, entityType, entityId)

  const ordered = useMemo(
    () => [...citations].sort((a, b) => a.position - b.position || a.created_at.localeCompare(b.created_at)),
    [citations],
  )
  const groups = useMemo(() => {
    const by = new Map<SourceKind, CitationRead[]>()
    for (const c of ordered) {
      const k = (c.source.kind in KIND_META ? c.source.kind : 'OTHER') as SourceKind
      by.set(k, [...(by.get(k) ?? []), c])
    }
    return KIND_ORDER.filter((k) => by.has(k)).map((k) => ({ kind: k, items: by.get(k)! }))
  }, [ordered])

  function move(c: CitationRead, delta: -1 | 1) {
    const ids = ordered.map((x) => x.id)
    const i = ids.indexOf(c.id)
    const j = i + delta
    if (j < 0 || j >= ids.length) return
    ;[ids[i], ids[j]] = [ids[j], ids[i]]
    reorder.mutate(ids)
  }

  return (
    <section>
      <PanelHeading
        action={editable && (
          <Button size="sm" variant="ghost" className="h-7 px-2 text-xs text-zinc-300" onClick={() => setCiting(true)}>
            <Plus className="mr-1 h-3.5 w-3.5" /> Cite
          </Button>
        )}
      >
        {title}
        {ordered.length > 0 && <span className="ml-1.5 text-zinc-500">({ordered.length})</span>}
      </PanelHeading>

      {ordered.length === 0 ? (
        <button
          type="button"
          disabled={!editable}
          onClick={() => setCiting(true)}
          className="flex w-full items-center gap-2 rounded-lg border border-dashed border-zinc-800 px-3 py-3 text-left text-sm text-zinc-500 transition-colors enabled:hover:border-zinc-700 enabled:hover:text-zinc-300"
        >
          <FileText className="h-4 w-4" />
          {editable ? 'Nothing cited yet. Cite a source…' : 'Nothing cited.'}
        </button>
      ) : (
        <div className="space-y-3">
          {groups.map(({ kind, items }) => (
            <div key={kind}>
              {groups.length > 1 && (
                <div className="mb-1 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                  {KIND_META[kind].plural}
                </div>
              )}
              <div className="divide-y divide-zinc-800 overflow-hidden rounded-lg border border-zinc-800">
                {items.map((c) => {
                  const index = ordered.indexOf(c)
                  return (
                    <SourceCard
                      key={c.id}
                      source={c.source}
                      citation={c}
                      actions={editable && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <button
                              type="button"
                              aria-label="Citation actions"
                              className="rounded p-1 text-zinc-500 opacity-60 transition hover:bg-zinc-800 hover:text-zinc-200 group-hover:opacity-100"
                            >
                              <MoreHorizontal className="h-3.5 w-3.5" />
                            </button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => setEditing(c)}>
                              <Pencil className="mr-2 h-3.5 w-3.5" /> Edit what it supports
                            </DropdownMenuItem>
                            <DropdownMenuItem disabled={index === 0 || reorder.isPending} onClick={() => move(c, -1)}>
                              <ArrowUp className="mr-2 h-3.5 w-3.5" /> Move up
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              disabled={index === ordered.length - 1 || reorder.isPending}
                              onClick={() => move(c, 1)}
                            >
                              <ArrowDown className="mr-2 h-3.5 w-3.5" /> Move down
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-red-400 focus:text-red-300" onClick={() => setDetaching(c)}>
                              <Unlink className="mr-2 h-3.5 w-3.5" /> Detach
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    />
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {citing && (
        <SourcePicker
          universeId={universeId}
          entityType={entityType}
          entityId={entityId}
          citedSourceIds={ordered.map((c) => c.source_id)}
          open
          onClose={() => setCiting(false)}
        />
      )}
      {editing && (
        <CitationEditDialog
          universeId={universeId}
          entityType={entityType}
          citation={editing}
          onClose={() => setEditing(null)}
        />
      )}
      <ConfirmDialog
        open={!!detaching}
        title="Detach this source?"
        description={detaching ? `"${detaching.source.title}" will no longer be cited here.` : ''}
        impact={detaching && (detaching.quote || detaching.note || detaching.locator)
          ? 'Its locator, quote and note on this record are deleted with it.'
          : undefined}
        confirmLabel="Detach"
        destructive
        pending={detach.isPending}
        onConfirm={async () => {
          if (detaching) await detach.mutateAsync(detaching.id)
          setDetaching(null)
        }}
        onCancel={() => setDetaching(null)}
      />
    </section>
  )
}
