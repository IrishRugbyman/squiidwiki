import { Check, ChevronsUpDown, Plus, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { cn } from '@/lib/utils'

export interface ComboboxItem {
  id: string
  name: string
  hint?: string
  /** Tailwind bg-* class for a small status dot */
  dotClass?: string
}

interface AffiliationComboboxProps {
  label: string
  /** Currently selected id, or empty string for none */
  value: string
  onChange: (id: string) => void
  items: ComboboxItem[]
  placeholder?: string
  /** When provided, "Create new — X" footer appears when query has no exact match */
  onCreateRequest?: (name: string) => void
  /** Disable the trigger */
  disabled?: boolean
  /** Loading state for create action */
  creating?: boolean
}

/**
 * Searchable combobox for picking an affiliation (Set / Alliance / Gang) with an
 * optional inline create footer. Built on cmdk for keyboard navigation.
 */
export function AffiliationCombobox({
  label,
  value,
  onChange,
  items,
  placeholder = 'None',
  onCreateRequest,
  disabled,
  creating,
}: AffiliationComboboxProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const containerRef = useRef<HTMLDivElement | null>(null)
  const triggerRef = useRef<HTMLButtonElement | null>(null)

  const selected = useMemo(() => items.find((i) => i.id === value) ?? null, [items, value])
  const trimmed = query.trim()
  const exactMatch = useMemo(
    () => items.some((i) => i.name.toLowerCase() === trimmed.toLowerCase()),
    [items, trimmed],
  )
  const showCreate = !!onCreateRequest && trimmed.length > 0 && !exactMatch

  // Close on outside click
  useEffect(() => {
    if (!open) return
    function onDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  function pick(id: string) {
    onChange(id)
    setOpen(false)
    setQuery('')
    triggerRef.current?.focus()
  }

  function clear(e: React.MouseEvent) {
    e.stopPropagation()
    onChange('')
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        className={cn(
          'flex h-9 w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 ring-offset-zinc-950 placeholder:text-zinc-400',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 focus-visible:ring-offset-1',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'hover:border-zinc-600 transition-colors',
        )}
      >
        <span className="flex min-w-0 items-center gap-2">
          {selected?.dotClass && <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${selected.dotClass}`} />}
          <span className={cn('truncate', !selected && 'text-zinc-400')}>
            {selected ? selected.name : placeholder}
          </span>
        </span>
        <span className="flex shrink-0 items-center gap-1 text-zinc-400">
          {selected && !disabled && (
            <span
              role="button"
              tabIndex={-1}
              onClick={clear}
              aria-label={`Clear ${label}`}
              className="rounded p-0.5 hover:bg-zinc-800 hover:text-zinc-200"
            >
              <X className="h-3.5 w-3.5" />
            </span>
          )}
          <ChevronsUpDown className="h-3.5 w-3.5" />
        </span>
      </button>

      {open && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-md border border-zinc-700 bg-zinc-950 shadow-2xl shadow-black/50">
          <Command shouldFilter className="max-h-[300px]">
            <CommandInput
              placeholder={`Search ${label.toLowerCase()}…`}
              value={query}
              onValueChange={setQuery}
              autoFocus
            />
            <CommandList>
              <CommandEmpty>
                {showCreate
                  ? <span className="text-zinc-400">No match. Create one below</span>
                  : 'No results.'}
              </CommandEmpty>
              <CommandGroup>
                {items.map((item) => {
                  const isSelected = item.id === value
                  return (
                    <CommandItem
                      key={item.id}
                      value={`${item.name} ${item.hint ?? ''}`}
                      onSelect={() => pick(item.id)}
                      className="flex items-center gap-2"
                    >
                      {item.dotClass && <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${item.dotClass}`} />}
                      <span className="truncate">{item.name}</span>
                      {item.hint && <span className="ml-auto text-[11px] text-zinc-400">{item.hint}</span>}
                      {isSelected && <Check className={cn('h-3.5 w-3.5 text-violet-400', item.hint && 'ml-1')} />}
                    </CommandItem>
                  )
                })}
              </CommandGroup>
              {showCreate && (
                <div className="border-t border-zinc-800 p-1">
                  <button
                    type="button"
                    disabled={creating}
                    onClick={() => onCreateRequest?.(trimmed)}
                    className={cn(
                      'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-violet-300',
                      'hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50',
                    )}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    {creating ? `Creating "${trimmed}"…` : <>Create new {label.toLowerCase()} &mdash; <span className="font-medium">"{trimmed}"</span></>}
                  </button>
                </div>
              )}
            </CommandList>
          </Command>
        </div>
      )}
    </div>
  )
}
