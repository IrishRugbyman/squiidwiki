import { useEffect, useRef } from 'react'

/**
 * Ctrl/Cmd-V anywhere on the page hands pasted images to `onImages`.
 *
 * A paste event only reaches the element that has focus, so a handler on the
 * drop zone itself fired only after the zone had been clicked (or right-clicked)
 * first: pasting straight after landing on the Media tab did nothing. This
 * listens on the document instead, with three guards:
 *
 * - A paste into a text field is left alone, so captions and form fields still
 *   receive pasted text, and a pasted image there is not uploaded.
 * - Only the most recently mounted owner receives it. The member form's photo
 *   section can be open over a detail page's Media tab; one paste must not
 *   upload the same picture to both.
 * - While a dialog is open, only an owner inside that dialog receives it, so a
 *   picture pasted into an unrelated dialog does not land on the page behind.
 */
const owners: symbol[] = []

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  if (target.isContentEditable) return true
  if (target instanceof HTMLTextAreaElement) return true
  if (target instanceof HTMLInputElement) {
    return !['button', 'checkbox', 'color', 'file', 'radio', 'range', 'reset', 'submit'].includes(
      target.type,
    )
  }
  return false
}

export function imagesFrom(data: DataTransfer | null): File[] {
  const files: File[] = []
  for (const item of data?.items ?? []) {
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) files.push(file)
    }
  }
  return files
}

export function usePageImagePaste<T extends HTMLElement>(onImages: (files: File[]) => void) {
  const ref = useRef<T | null>(null)
  const handler = useRef(onImages)
  useEffect(() => {
    handler.current = onImages
  }, [onImages])

  useEffect(() => {
    const id = Symbol('image-paste-owner')
    owners.push(id)

    function onPaste(e: ClipboardEvent) {
      if (owners[owners.length - 1] !== id) return
      if (isEditable(e.target)) return
      const dialogs = document.querySelectorAll('[role="dialog"][data-state="open"]')
      const top = dialogs[dialogs.length - 1]
      if (top && !(ref.current && top.contains(ref.current))) return
      const files = imagesFrom(e.clipboardData)
      if (files.length === 0) return
      e.preventDefault()
      handler.current(files)
    }

    document.addEventListener('paste', onPaste)
    return () => {
      document.removeEventListener('paste', onPaste)
      owners.splice(owners.indexOf(id), 1)
    }
  }, [])

  return ref
}
