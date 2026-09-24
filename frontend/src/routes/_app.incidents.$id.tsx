import { createFileRoute } from '@tanstack/react-router'

// The page is in _app.incidents.$id.lazy.tsx, its own chunk.
export const Route = createFileRoute('/_app/incidents/$id')({})
