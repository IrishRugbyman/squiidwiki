import { useNavigate } from '@tanstack/react-router'
import { AlertTriangle, Clock, FileText, Globe, MapPin, Network, NotebookText, Plus, Shield, Users } from 'lucide-react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  useAllianceSearch, useIncidentSearch, useMemberSearch, useMunicipalitySearch,
  useSetSearch, useSourceSearch, useCreateUniverse,
} from '@/lib/queries'
import { useUniverseStore, type Universe } from '@/stores/universe'
import { useAuthStore } from '@/stores/auth'
import { useRecentsStore, type RecentEntityType } from '@/stores/recents'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import { Sheet, SheetContent, SheetClose } from '@/components/Sheet'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import type { FuzzyDateValue } from '@/components/FuzzyDate'

// ─── Universe creation sheet (moved here from UniverseSwitcher) ───────────────

function slugify(s: string): string {
  return s.toLowerCase().trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function CreateUniverseSheet({ open, onClose }: { open: boolean; onClose: (created?: Universe) => void }) {
  const create = useCreateUniverse()
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [slugDirty, setSlugDirty] = useState(false)
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleNameChange(v: string) {
    setName(v)
    if (!slugDirty) setSlug(slugify(v))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    try {
      const created = await create.mutateAsync({
        name: name.trim(),
        slug: slug.trim(),
        description: description.trim() || null,
      })
      setName(''); setSlug(''); setSlugDirty(false); setDescription('')
      onClose({ id: created.id, name: created.name, slug: created.slug })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create universe')
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent title="New Universe" description="Create an isolated workspace for a city or region">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="u-name">Name *</Label>
            <Input id="u-name" required value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="e.g. Metro Chicago" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-slug">Slug *</Label>
            <Input
              id="u-slug" required value={slug}
              onChange={(e) => { setSlug(e.target.value); setSlugDirty(true) }}
              placeholder="metro-chicago"
              pattern="[a-z0-9\-]+"
            />
            <p className="text-xs text-zinc-400">Lowercase letters, numbers, and hyphens only.</p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-desc">Description</Label>
            <Textarea id="u-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional overview…" />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={create.isPending || !name || !slug} className="flex-1">
              {create.isPending ? 'Creating…' : 'Create Universe'}
            </Button>
            <SheetClose asChild>
              <Button type="button" variant="outline" onClick={() => onClose()}>Cancel</Button>
            </SheetClose>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}

// ─── Fuzzy date formatter (inline, minimal) ───────────────────────────────────

function fmtDate(d: FuzzyDateValue | null): string {
  if (!d || d.precision === 'UNKNOWN') return ''
  if (d.precision === 'Y') return String(d.year)
  if (d.precision === 'YM') return `${d.year}/${String(d.month).padStart(2, '0')}`
  return `${d.year}/${String(d.month).padStart(2, '0')}/${String(d.day).padStart(2, '0')}`
}

// ─── Recent-entity icon mapping ───────────────────────────────────────────────

const RECENT_ICON: Record<RecentEntityType, typeof Users> = {
  member: Users,
  set: Shield,
  alliance: Network,
  incident: AlertTriangle,
  source: FileText,
  municipality: MapPin,
  research: NotebookText,
}

const RECENT_ROUTE: Record<RecentEntityType, string> = {
  member: '/members',
  set: '/sets',
  alliance: '/alliances',
  incident: '/incidents',
  source: '/sources',
  municipality: '/municipalities',
  research: '/research',
}

// ─── Global command palette ───────────────────────────────────────────────────

interface GlobalCommandPaletteProps {
  open: boolean
  onClose: () => void
}

export function GlobalCommandPalette({ open, onClose }: GlobalCommandPaletteProps) {
  const navigate = useNavigate()
  const { activeUniverse, setActiveUniverse } = useUniverseStore()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.global_role === 'ADMIN'
  const universeId = activeUniverse?.id ?? null

  const [q, setQ] = useState('')
  const [creating, setCreating] = useState(false)
  const recents = useRecentsStore((s) => s.entries)

  const { data: universeData } = useQuery({
    queryKey: ['universes'],
    queryFn: () => api.get<{ items: Universe[]; total: number }>('/universes/'),
    staleTime: 60_000,
  })

  const { data: memberResults } = useMemberSearch(universeId, q)
  const { data: setResults } = useSetSearch(universeId, q)
  const { data: allianceResults } = useAllianceSearch(universeId, q)
  const { data: incidentResults } = useIncidentSearch(universeId, q)
  const { data: sourceResults } = useSourceSearch(universeId, q)
  const { data: municipalityResults } = useMunicipalitySearch(universeId, q)

  const searching = q.length >= 2
  const hasResults = searching && (
    (memberResults?.length ?? 0) > 0 ||
    (setResults?.length ?? 0) > 0 ||
    (allianceResults?.length ?? 0) > 0 ||
    (incidentResults?.length ?? 0) > 0 ||
    (sourceResults?.length ?? 0) > 0 ||
    (municipalityResults?.length ?? 0) > 0
  )

  function go(path: string) {
    onClose()
    setQ('')
    navigate({ to: path as any })
  }

  function handleCreated(u?: Universe) {
    setCreating(false)
    if (u) {
      setActiveUniverse(u)
      onClose()
      setQ('')
    }
  }

  return (
    <>
      <CommandDialog
        open={open}
        shouldFilter={false}
        onOpenChange={(v) => {
          if (!v) { onClose(); setQ('') }
        }}
      >
        <CommandInput
          placeholder={universeId ? 'Search members, sets, alliances, incidents, sources, places…' : 'Search or switch universe…'}
          value={q}
          onValueChange={setQ}
        />
        <CommandList>
          {searching && !hasResults && <CommandEmpty>No results for "{q}"</CommandEmpty>}

          {/* Entity search results */}
          {searching && (memberResults?.length ?? 0) > 0 && (
            <CommandGroup heading="Members">
              {memberResults!.slice(0, 5).map((m) => (
                <CommandItem key={m.id} value={`member-${m.id}`} onSelect={() => go(`/members/${m.slug ?? m.id}`)}>
                  <Users className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                  <span>{m.display_name}</span>
                  <span className="ml-auto text-[10px] text-zinc-400">{m.status}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {searching && (setResults?.length ?? 0) > 0 && (
            <CommandGroup heading="Sets">
              {setResults!.slice(0, 5).map((s) => {
                const ql = q.toLowerCase()
                const matchedVariant = (s.name_variants ?? []).find((v) => {
                  if (!v || v.is_primary) return false
                  return [v.name, v.initials, v.number]
                    .filter(Boolean)
                    .some((x) => x!.toLowerCase().includes(ql))
                })
                const matchLabel = matchedVariant
                  ? [matchedVariant.name, matchedVariant.initials, matchedVariant.number].filter(Boolean).join(' · ')
                  : null
                return (
                  <CommandItem key={s.id} value={`set-${s.id}`} onSelect={() => go(`/sets/${s.slug ?? s.id}`)}>
                    <Shield className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                    <span>{s.name}</span>
                    {matchLabel && (
                      <span className="ml-2 text-[10px] text-zinc-400">a/k/a {matchLabel}</span>
                    )}
                    <span className="ml-auto text-[10px] text-zinc-400">{s.status}</span>
                  </CommandItem>
                )
              })}
            </CommandGroup>
          )}

          {searching && (allianceResults?.length ?? 0) > 0 && (
            <CommandGroup heading="Alliances">
              {allianceResults!.slice(0, 5).map((a) => (
                <CommandItem key={a.id} value={`alliance-${a.id}`} onSelect={() => go(`/alliances/${a.slug ?? a.id}`)}>
                  <Network className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                  <span>{a.name}</span>
                  <span className="ml-auto text-[10px] text-zinc-400">{a.status}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {searching && (incidentResults?.length ?? 0) > 0 && (
            <CommandGroup heading="Incidents">
              {incidentResults!.slice(0, 5).map((inc) => (
                <CommandItem key={inc.id} value={`incident-${inc.id}`} onSelect={() => go(`/incidents/${inc.id}`)}>
                  <AlertTriangle className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                  <span>{inc.type}</span>
                  {inc.date && <span className="ml-1.5 text-[10px] text-zinc-400">{fmtDate(inc.date)}</span>}
                  {inc.verified && <span className="ml-auto text-[10px] text-emerald-600">verified</span>}
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {searching && (municipalityResults?.length ?? 0) > 0 && (
            <CommandGroup heading="Municipalities">
              {municipalityResults!.slice(0, 5).map((m) => (
                <CommandItem key={m.id} value={`municipality-${m.id}`} onSelect={() => go(`/municipalities/${m.id}`)}>
                  <MapPin className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                  <span>{m.name}</span>
                  {m.incident_count > 0 && (
                    <span className="ml-auto text-[10px] text-zinc-400">{m.incident_count} incidents</span>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {searching && (sourceResults?.length ?? 0) > 0 && (
            <CommandGroup heading="Sources">
              {sourceResults!.slice(0, 5).map((src) => (
                <CommandItem key={src.id} value={`source-${src.id}`} onSelect={() => go(`/sources/${src.id}`)}>
                  <FileText className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                  <span className="truncate">{src.title}</span>
                  <span className="ml-auto text-[10px] text-zinc-400">{src.reliability}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {/* Universe switcher — always visible */}
          {(universeData?.items.length ?? 0) > 0 && (
            <>
              {searching && hasResults && <CommandSeparator />}
              <CommandGroup heading="Universes">
                {universeData!.items.map((u) => (
                  <CommandItem
                    key={u.id}
                    value={`universe-${u.name}`}
                    onSelect={() => { setActiveUniverse(u); onClose(); setQ('') }}
                  >
                    <Globe className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                    <span>{u.name}</span>
                    {activeUniverse?.id === u.id && (
                      <span className="ml-auto text-[10px] text-violet-400">active</span>
                    )}
                  </CommandItem>
                ))}
                {isAdmin && (
                  <CommandItem value="__create_universe__" onSelect={() => { onClose(); setQ(''); setCreating(true) }}>
                    <Plus className="mr-2 h-3.5 w-3.5 shrink-0" />
                    New universe…
                  </CommandItem>
                )}
              </CommandGroup>
            </>
          )}

          {/* Recently viewed — only when no search; below Universes so it doesn't
              get top billing while the user is picking a universe. */}
          {!searching && recents.length > 0 && (
            <>
              <CommandSeparator />
              <CommandGroup heading="Recent">
                {recents.map((r) => {
                  const Icon = RECENT_ICON[r.type]
                  const path = `${RECENT_ROUTE[r.type]}/${r.slug ?? r.id}`
                  return (
                    <CommandItem
                      key={`${r.type}-${r.id}`}
                      value={`recent-${r.type}-${r.id}`}
                      onSelect={() => go(path)}
                    >
                      <Icon className="mr-2 h-3.5 w-3.5 shrink-0 text-zinc-400" />
                      <span className="truncate">{r.label}</span>
                      <Clock className="ml-auto h-3 w-3 shrink-0 text-zinc-500" />
                    </CommandItem>
                  )
                })}
              </CommandGroup>
            </>
          )}
        </CommandList>
      </CommandDialog>

      <CreateUniverseSheet open={creating} onClose={handleCreated} />
    </>
  )
}
