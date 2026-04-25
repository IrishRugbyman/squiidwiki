import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Pencil, Save, Trash2, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { CopyButton } from '@/components/CopyButton'
import { DetailHeaderSkeleton } from '@/components/skeletons'
import { ErrorState } from '@/components/ErrorState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useDeleteResearchNote, useResearchNote, useUpdateResearchNote } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { useEditShortcut } from '@/hooks/useKeymap'
import { useRecordRecent } from '@/stores/recents'

export const Route = createFileRoute('/_app/research/$id')({
  validateSearch: (s: Record<string, unknown>) => ({
    edit: s.edit === 1 || s.edit === '1' ? 1 : undefined,
  }),
  component: ResearchDetailPage,
})

const URL_RE = /(https?:\/\/[^\s)]+)/g

function renderContent(text: string): React.ReactNode[] {
  if (!text) return []
  const out: React.ReactNode[] = []
  const parts = text.split(URL_RE)
  parts.forEach((part, i) => {
    if (URL_RE.test(part)) {
      out.push(
        <a
          key={i}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-400 hover:text-violet-300 underline decoration-violet-700 underline-offset-2 break-all"
        >
          {part}
        </a>,
      )
    } else {
      out.push(part)
    }
  })
  return out
}

function ResearchDetailPage() {
  const { id } = Route.useParams()
  const { edit } = Route.useSearch()
  const navigate = useNavigate()
  const universe = useUniverseStore((s) => s.activeUniverse)

  const { data: note, isLoading, isError, refetch } = useResearchNote(id, universe?.id ?? null)
  const update = useUpdateResearchNote(id, universe?.id ?? '')
  const del = useDeleteResearchNote(universe?.id ?? '')

  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [deleting, setDeleting] = useState(false)
  const seededRef = useRef<string | null>(null)

  // Seed local state when the note loads or changes id, and start in edit mode
  // when ?edit=1 is set (used by the "+ New note" flow).
  useEffect(() => {
    if (!note) return
    if (seededRef.current === note.id) return
    seededRef.current = note.id
    setTitle(note.title)
    setContent(note.content)
    if (edit === 1) setEditing(true)
  }, [note, edit])

  useEditShortcut(() => note && setEditing(true))
  useRecordRecent(note ? { type: 'research', id: note.id, slug: null, label: note.title || 'Untitled note' } : null)

  if (isError) return <ErrorState title="Note not found" onRetry={() => refetch()} />

  async function handleSave() {
    if (!note) return
    const cleanTitle = title.trim() || 'Untitled note'
    await update.mutateAsync({ title: cleanTitle, content })
    setEditing(false)
    if (edit === 1) {
      // Drop the ?edit=1 from URL after first save so refresh doesn't re-enter edit
      navigate({ to: '/research/$id', params: { id }, search: { edit: undefined }, replace: true })
    }
  }

  function handleCancel() {
    if (!note) return
    setTitle(note.title)
    setContent(note.content)
    setEditing(false)
  }

  async function handleDelete() {
    if (!note) return
    try {
      await del.mutateAsync(note.id)
      toast.success('Note deleted')
      navigate({ to: '/research' })
    } catch {
      setDeleting(false)
    }
  }

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Research', to: '/research' }, { label: note?.title || 'Note' }]} />

      {isLoading ? (
        <DetailHeaderSkeleton />
      ) : note ? (
        <>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              {editing ? (
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Title"
                  className="text-xl font-bold h-auto py-1.5"
                  autoFocus
                />
              ) : (
                <div className="flex items-center gap-1.5">
                  <h1 className="text-2xl font-bold text-white">{note.title || 'Untitled note'}</h1>
                  <CopyButton value={window.location.href} label="Copy link to this note" className="opacity-60 hover:opacity-100" />
                </div>
              )}
              <p className="mt-1 text-xs text-zinc-600">
                Updated {new Date(note.updated_at).toLocaleString()}
              </p>
            </div>

            <div className="flex shrink-0 items-center gap-2">
              {editing ? (
                <>
                  <Button size="sm" variant="outline" onClick={handleCancel} disabled={update.isPending}>
                    <X className="mr-1.5 h-3.5 w-3.5" />Cancel
                  </Button>
                  <Button size="sm" onClick={handleSave} disabled={update.isPending}>
                    <Save className="mr-1.5 h-3.5 w-3.5" />
                    {update.isPending ? 'Saving…' : 'Save'}
                  </Button>
                </>
              ) : (
                <>
                  <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                    <Pencil className="mr-1.5 h-3.5 w-3.5" />Edit
                  </Button>
                  <Button size="sm" variant="destructive" onClick={() => setDeleting(true)}>
                    <Trash2 className="mr-1.5 h-3.5 w-3.5" />Delete
                  </Button>
                </>
              )}
            </div>
          </div>

          {editing ? (
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Type or paste anything — text, links, observations… URLs become clickable when you save."
              className="min-h-[60vh] font-mono text-sm leading-relaxed"
            />
          ) : note.content.trim() ? (
            <div className="whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 text-sm leading-relaxed text-zinc-200">
              {renderContent(note.content)}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-zinc-800 p-8 text-center">
              <p className="text-sm text-zinc-500">This note is empty.</p>
              <Button size="sm" variant="outline" className="mt-3" onClick={() => setEditing(true)}>
                <Pencil className="mr-1.5 h-3.5 w-3.5" />Start writing
              </Button>
            </div>
          )}

          <ConfirmDialog
            open={deleting}
            title="Delete note"
            description={`Permanently delete "${note.title || 'this note'}"? This cannot be undone.`}
            confirmLabel="Delete"
            destructive
            pending={del.isPending}
            onConfirm={handleDelete}
            onCancel={() => setDeleting(false)}
          />
        </>
      ) : null}
    </div>
  )
}
