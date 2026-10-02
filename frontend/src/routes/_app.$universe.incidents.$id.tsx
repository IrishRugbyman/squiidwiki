import { createFileRoute } from '@tanstack/react-router'

// The page is in _app.$universe.incidents.$id.lazy.tsx, its own chunk.
export const Route = createFileRoute('/_app/$universe/incidents/$id')({})
