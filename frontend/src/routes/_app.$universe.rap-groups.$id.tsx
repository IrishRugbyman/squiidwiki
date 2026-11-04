import { createFileRoute } from '@tanstack/react-router'

// The page is in _app.$universe.rap-groups.$id.lazy.tsx, its own chunk.
export const Route = createFileRoute('/_app/$universe/rap-groups/$id')({})
