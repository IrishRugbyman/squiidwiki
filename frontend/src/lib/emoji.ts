// Emojis a set is known by.
//
// A set is recognised on sight by its glyphs long before its name is read, and
// members signal affiliation with them in bios and display names. So the list is
// two things at once: a badge for scanning the wiki, and the lookup table that
// turns an emoji seen in a handle back into a set.
//
// The rules here mirror `_normalize_emojis` in backend/app/schemas/gang_set.py.
// Keep them in step: the backend is the authority and will 422 anything this
// lets through, but catching it here gives the error next to the field.

/** Longest single entry, in UTF-16 code units. A ZWJ sequence is the long case. */
export const MAX_EMOJI_LENGTH = 16
export const MAX_EMOJIS = 12

/**
 * True if `value` could be a glyph rather than text.
 *
 * The test is that it cannot be *entirely* ASCII. No emoji is, not even the
 * keycaps (`1️⃣` is an ASCII digit plus two non-ASCII code points),
 * while `BO` and `752` are, and those belong in name variants where they are
 * searchable as names.
 */
export function isLikelyEmoji(value: string): boolean {
  const v = value.trim()
  if (!v || v.length > MAX_EMOJI_LENGTH) return false
  // eslint-disable-next-line no-control-regex
  return !/^[\x00-\x7F]*$/.test(v)
}

/**
 * Split a typed field into entries.
 *
 * Emojis are pasted in every shape - space separated, comma separated, or run
 * together straight out of a bio - so all three are accepted. Run-together input
 * is split by grapheme, which is what keeps a flag or a ZWJ family as one entry
 * instead of shattering into surrogate halves.
 */
export function parseEmojiInput(raw: string): string[] {
  const out: string[] = []
  for (const chunk of raw.split(/[\s,]+/)) {
    if (!chunk) continue
    for (const grapheme of splitGraphemes(chunk)) {
      const g = grapheme.trim()
      if (g && !out.includes(g)) out.push(g)
    }
  }
  return out
}

/** Grapheme clusters, so multi-code-point emoji survive as single entries. */
function splitGraphemes(value: string): string[] {
  const Seg = (Intl as unknown as { Segmenter?: typeof Intl.Segmenter }).Segmenter
  if (Seg) {
    return Array.from(new Seg(undefined, { granularity: 'grapheme' }).segment(value),
      (s: { segment: string }) => s.segment)
  }
  // Array.from splits by code point, which keeps surrogate pairs intact but not
  // ZWJ sequences. Only reached on engines without Intl.Segmenter.
  return Array.from(value)
}

/** Back to a field value. Space separated, which is how they are usually pasted. */
export function formatEmojiInput(emojis: string[]): string {
  return emojis.join(' ')
}

/** The one shown as the badge wherever the set is listed. */
export function setBadge(emojis: string[] | null | undefined): string | null {
  return emojis?.[0] ?? null
}
