/** UI ceiling only; the column is unbounded text. Long enough for a sentence
 *  or two of context, short enough that the tile and lightbox can show it. */
export const CAPTION_MAX_LENGTH = 500

/** Whitespace-only input means "no caption", stored as null rather than "". */
export function normalizeCaption(raw: string): string | null {
  const trimmed = raw.trim()
  return trimmed.length > 0 ? trimmed : null
}
