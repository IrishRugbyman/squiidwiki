import { useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { formatEmojiInput, isLikelyEmoji, parseEmojiInput } from '@/lib/emoji'

/** Shared by the set and alliance forms: paste glyphs, see them as chips, the
 *  first marked as the badge and anything that is not a glyph marked red. */
export function EmojiField({ id, value, onChange, noun }: {
  id: string
  value: string
  onChange: (text: string) => void
  noun: string
}) {
  const emojis = useMemo(() => parseEmojiInput(value), [value])
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>Emojis</Label>
      <Input
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={() => onChange(formatEmojiInput(parseEmojiInput(value)))}
        placeholder={`Paste the glyphs this ${noun} uses…`}
      />
      <p className="text-[11px] text-zinc-500">
        First is the badge shown in lists. The rest are the other glyphs members
        signal the {noun} with, so an emoji in a handle can be traced back here.
      </p>
      {emojis.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
          {emojis.map((e, i) => {
            const ok = isLikelyEmoji(e)
            return (
              <span
                key={`${e}-${i}`}
                title={!ok ? 'Not an emoji, this will be rejected on save' : i === 0 ? 'Badge' : undefined}
                className={
                  'rounded px-1.5 py-0.5 text-base leading-none ' +
                  (!ok ? 'bg-red-950 ring-1 ring-red-700' : i === 0 ? 'bg-zinc-800 ring-1 ring-violet-600' : 'bg-zinc-800')
                }
              >
                {e}
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}
