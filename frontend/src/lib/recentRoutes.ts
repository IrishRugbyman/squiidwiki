import { AlertTriangle, FileText, MapPin, Network, NotebookText, Shield, Users, type LucideIcon } from 'lucide-react'
import type { RecentEntityType } from '@/stores/recents'

/** Icon and base route per recent-entity type, shared by the palette and the dashboard. */
export const RECENT_ICON: Record<RecentEntityType, LucideIcon> = {
  member: Users,
  set: Shield,
  alliance: Network,
  incident: AlertTriangle,
  source: FileText,
  municipality: MapPin,
  research: NotebookText,
}

export const RECENT_ROUTE = {
  member: '/members',
  set: '/sets',
  alliance: '/alliances',
  incident: '/incidents',
  source: '/sources',
  municipality: '/municipalities',
  research: '/research',
} as const satisfies Record<RecentEntityType, string>

/** The typed detail route for a recent entry, for `<Link to params>`. */
export type RecentDetailRoute = `${(typeof RECENT_ROUTE)[RecentEntityType]}/$id`
