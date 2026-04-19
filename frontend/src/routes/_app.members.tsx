import { createFileRoute, Link } from '@tanstack/react-router'
import { Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { NoUniverse } from '@/components/NoUniverse'
import { PageHeader } from '@/components/PageHeader'
import { MemberStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useCreateMember, useMembers, useMemberSearch } from '@/lib/queries'
import { useUniverseStore } from '@/stores/universe'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import type { MemberStatus } from '@/lib/types'

export const Route = createFileRoute('/_app/members')({
  component: MembersPage,
})

function CreateMemberSheet({ universeId, open, onClose }: { universeId: string; open: boolean; onClose: () => void }) {
  const create = useCreateMember()
  const [nickname, setNickname] = useState('')
  const [legalName, setLegalName] = useState('')
  const [nicknameUnknown, setNicknameUnknown] = useState(false)
  const [status, setStatus] = useState<MemberStatus>('UNKNOWN')
  const [biography, setBiography] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      await create.mutateAsync({
        universe_id: universeId,
        nickname: nickname || null,
        legal_name: legalName || null,
        nickname_unknown: nicknameUnknown,
        status,
        biography,
      })
      setNickname(''); setLegalName(''); setNicknameUnknown(false); setStatus('UNKNOWN'); setBiography('')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create member')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title="Add Member" description="Create a new member profile">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="m-nickname">Nickname</Label>
            <Input id="m-nickname" value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="Street name" disabled={nicknameUnknown} />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="m-nku"
              type="checkbox"
              checked={nicknameUnknown}
              onChange={(e) => setNicknameUnknown(e.target.checked)}
              className="rounded border-zinc-700 bg-zinc-900 text-violet-600"
            />
            <label htmlFor="m-nku" className="text-sm text-zinc-300">Nickname unknown (use legal name as display)</label>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-legal">Legal Name</Label>
            <Input id="m-legal" value={legalName} onChange={(e) => setLegalName(e.target.value)} placeholder="Full legal name" />
          </div>
          <div className="space-y-1.5">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as MemberStatus)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {(['FREE', 'LOCKED', 'DEAD', 'UNKNOWN', 'ESCAPEE', 'ABSCONDER'] as MemberStatus[]).map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="m-bio">Biography</Label>
            <Textarea id="m-bio" value={biography} onChange={(e) => setBiography(e.target.value)} placeholder="Background notes…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={create.isPending} className="flex-1">
              {create.isPending ? 'Saving…' : 'Create Member'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}

function MembersPage() {
  const universe = useUniverseStore((s) => s.activeUniverse)
  const [q, setQ] = useState('')
  const [cursor, setCursor] = useState<string | undefined>(undefined)
  const [creating, setCreating] = useState(false)

  const { data, isLoading } = useMembers(universe?.id ?? null, cursor)
  const { data: searchResults } = useMemberSearch(universe?.id ?? null, q)

  if (!universe) return <NoUniverse />

  const items = q.length >= 2 ? (searchResults ?? []) : (data?.items ?? [])
  const total = data?.total

  return (
    <div>
      <PageHeader
        title="Members"
        description={total != null ? `${total} total` : undefined}
        action={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1.5 h-4 w-4" />Add Member</Button>}
      />

      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input className="pl-8" placeholder="Search members…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50">
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Name</th>
              <th className="px-4 py-2.5 text-left font-medium text-zinc-400">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {isLoading && !q
              ? Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={2}><Skeleton className="h-4 w-48" /></td>
                  </tr>
                ))
              : items.map((member) => (
                  <tr key={member.id} className="hover:bg-zinc-900/50 transition-colors">
                    <td className="px-4 py-3">
                      <Link to="/members/$id" params={{ id: member.id }} className="font-medium text-white hover:text-violet-400 transition-colors">
                        {member.display_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3"><MemberStatusBadge status={member.status} /></td>
                  </tr>
                ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={2} className="px-4 py-12 text-center text-sm text-zinc-500">No members found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!q && data?.next_cursor && (
        <div className="mt-4 flex justify-end">
          <Button variant="outline" size="sm" onClick={() => setCursor(data.next_cursor ?? undefined)}>Load more</Button>
        </div>
      )}

      <CreateMemberSheet universeId={universe.id} open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}
