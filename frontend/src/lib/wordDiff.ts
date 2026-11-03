// Word-level diff for the History tab's long text fields (biographies,
// narratives). A plain LCS over word-and-whitespace tokens: biographies are a
// few hundred words, so the quadratic table is small. Past MAX_CELLS the
// result is the whole old text removed and the whole new text added, which is
// still correct, only coarser.

export interface DiffPart {
  op: 'same' | 'add' | 'del'
  text: string
}

const MAX_CELLS = 4_000_000

function tokens(s: string): string[] {
  return s.split(/(\s+)/).filter((t) => t !== '')
}

function push(out: DiffPart[], op: DiffPart['op'], text: string) {
  const last = out[out.length - 1]
  if (last && last.op === op) last.text += text
  else out.push({ op, text })
}

export function wordDiff(oldText: string, newText: string): DiffPart[] {
  const a = tokens(oldText)
  const b = tokens(newText)
  if (a.length * b.length > MAX_CELLS) {
    const out: DiffPart[] = []
    if (oldText) out.push({ op: 'del', text: oldText })
    if (newText) out.push({ op: 'add', text: newText })
    return out
  }
  // lcs[i][j] = length of the LCS of a[i:] and b[j:]
  const lcs: Uint32Array[] = Array.from({ length: a.length + 1 }, () => new Uint32Array(b.length + 1))
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }
  const out: DiffPart[] = []
  let i = 0
  let j = 0
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      push(out, 'same', a[i])
      i++
      j++
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      push(out, 'del', a[i++])
    } else {
      push(out, 'add', b[j++])
    }
  }
  while (i < a.length) push(out, 'del', a[i++])
  while (j < b.length) push(out, 'add', b[j++])
  return out
}
