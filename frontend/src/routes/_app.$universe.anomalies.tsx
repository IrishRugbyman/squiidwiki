import { createFileRoute } from '@tanstack/react-router'

// Admin-only data-anomaly report. The page is in _app.$universe.anomalies.lazy.tsx,
// its own chunk, so the main bundle does not carry a page only admins open.
export const Route = createFileRoute('/_app/$universe/anomalies')({})
