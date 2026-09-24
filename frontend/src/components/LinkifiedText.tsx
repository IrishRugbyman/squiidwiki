const URL_SPLIT_RE = /(https?:\/\/[^\s)]+)/g
const URL_TEST_RE = /^https?:\/\/[^\s)]+$/

/**
 * Plain text with its URLs made clickable. Free-text fields (descriptions,
 * bios, narratives, research notes) often end with the link they came from.
 * No markdown: this app deliberately renders prose as typed.
 */
export function LinkifiedText({ text }: { text: string }) {
  return (
    <>
      {text.split(URL_SPLIT_RE).map((part, i) =>
        URL_TEST_RE.test(part) ? (
          <a key={i} href={part} target="_blank" rel="noopener noreferrer"
            className="break-all text-violet-400 underline decoration-violet-700 underline-offset-2 hover:text-violet-300">
            {part}
          </a>
        ) : (
          part
        ),
      )}
    </>
  )
}
