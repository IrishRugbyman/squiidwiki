import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useUpdateCitation } from '@/lib/queries'
import { LOOKUP_LABEL } from '@/lib/sourceMeta'
import type { CitableType, CitationRead, UUID } from '@/lib/types'

/** Edit what a citation says: where in the source, the words, what it supports. */
export function CitationEditDialog({ universeId, entityType, citation, onClose }: {
  universeId: UUID
  entityType: CitableType
  citation: CitationRead
  onClose: () => void
}) {
  const update = useUpdateCitation(universeId, entityType)
  const [locator, setLocator] = useState(citation.locator ?? '')
  const [quote, setQuote] = useState(citation.quote ?? '')
  const [note, setNote] = useState(citation.note ?? '')
  const [accessed, setAccessed] = useState(citation.accessed_at ?? '')
  const lookup = citation.source.lookup_system

  async function save(e: React.FormEvent) {
    e.preventDefault()
    await update.mutateAsync({
      id: citation.id,
      locator: locator.trim() || null,
      quote: quote.trim() || null,
      note: note.trim() || null,
      accessed_at: accessed || null,
    })
    onClose()
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit citation</DialogTitle>
          <DialogDescription className="truncate">{citation.source.title}</DialogDescription>
        </DialogHeader>
        <form onSubmit={save} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="ce-locator">{lookup ? `${LOOKUP_LABEL[lookup]} number` : 'Where in the source'}</Label>
            <Input id="ce-locator" value={locator} onChange={(e) => setLocator(e.target.value)} placeholder="p. 12, ¶ 4, 01:23…" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ce-quote">Quote</Label>
            <Textarea id="ce-quote" rows={3} value={quote} onChange={(e) => setQuote(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ce-note">What it supports here</Label>
            <Textarea id="ce-note" rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ce-accessed">Read on</Label>
            <Input id="ce-accessed" type="date" value={accessed} onChange={(e) => setAccessed(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={update.isPending}>{update.isPending ? 'Saving…' : 'Save'}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
