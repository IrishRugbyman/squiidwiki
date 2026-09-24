import { createFileRoute } from '@tanstack/react-router'

// The page is in _app.alliances.$id.lazy.tsx, its own chunk.
export const Route = createFileRoute('/_app/alliances/$id')({})
