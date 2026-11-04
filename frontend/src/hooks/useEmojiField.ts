import { useMemo } from 'react'
import { MAX_EMOJIS, isLikelyEmoji, parseEmojiInput } from '@/lib/emoji'

/** The glyphs in an emoji field, and why they cannot be saved if they cannot. */
export function useEmojiField(text: string, noun: string): { emojis: string[]; error: string | null } {
  return useMemo(() => {
    const emojis = parseEmojiInput(text)
    const bad = emojis.filter((e) => !isLikelyEmoji(e))
    if (bad.length) return { emojis, error: `Not emojis: ${bad.join(' ')}, plain text belongs in a name variant` }
    if (emojis.length > MAX_EMOJIS) return { emojis, error: `At most ${MAX_EMOJIS} emojis per ${noun} (got ${emojis.length})` }
    return { emojis, error: null }
  }, [text, noun])
}
