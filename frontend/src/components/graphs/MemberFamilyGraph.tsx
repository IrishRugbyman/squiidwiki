import { useMemo, useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  MarkerType,
  type Edge,
  type Node,
  type NodeProps,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useNavigate } from '@tanstack/react-router'
import { useQueries } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { familyDictToEntries, ROLE_LABEL, type FamilyRole } from '@/routes/_app.members.index'
import type { MemberListItem, MemberRead, UUID } from '@/lib/types'

const ROLE_TINT: Record<FamilyRole, string> = {
  father: 'bg-amber-950/60 border-amber-700 text-amber-200',
  son: 'bg-sky-950/60 border-sky-700 text-sky-200',
  brother: 'bg-violet-950/60 border-violet-700 text-violet-200',
  cousin: 'bg-emerald-950/60 border-emerald-700 text-emerald-200',
  uncle: 'bg-orange-950/60 border-orange-700 text-orange-200',
  nephew: 'bg-pink-950/60 border-pink-700 text-pink-200',
}

type FamilyNodeData = {
  label: string
  variant: 'center' | 'direct' | 'indirect'
  role: FamilyRole | null
  slug: string | null
}

function FamilyNode({ data }: NodeProps<FamilyNodeData>) {
  const cls =
    data.variant === 'center'
      ? 'bg-violet-950/80 border-violet-500 text-violet-100'
      : data.variant === 'direct' && data.role
        ? ROLE_TINT[data.role]
        : 'bg-zinc-900/80 border-zinc-700 text-zinc-300'
  return (
    <div className={`rounded-lg border px-3 py-2 text-xs font-medium shadow-md ${cls}`}>
      <Handle type="target" position={Position.Left} className="!bg-zinc-700 !border-zinc-700" />
      <Handle type="source" position={Position.Right} className="!bg-zinc-700 !border-zinc-700" />
      {data.label}
    </div>
  )
}

const nodeTypes = { family: FamilyNode }

interface MemberFamilyGraphProps {
  centerMember: MemberRead
  universeId: UUID
  allMembers: MemberListItem[]
}

export function MemberFamilyGraph({ centerMember, universeId, allMembers }: MemberFamilyGraphProps) {
  const navigate = useNavigate()

  const memberMap = useMemo(() => {
    const m: Record<string, MemberListItem> = {}
    for (const x of allMembers) m[x.id] = x
    return m
  }, [allMembers])

  // Hop 1 — direct relations from the center.
  const hop1 = useMemo(
    () => familyDictToEntries(centerMember.family as Record<string, unknown> | null),
    [centerMember.family],
  )
  const hop1Ids = useMemo(() => Array.from(new Set(hop1.map((e) => e.memberId))), [hop1])

  // Fetch hop-1 detail in parallel to read their family for hop-2.
  const hop1Queries = useQueries({
    queries: hop1Ids.map((id) => ({
      queryKey: ['members', id],
      queryFn: () => api.get<MemberRead>(`/members/${id}?universe_id=${universeId}`),
      enabled: !!universeId && !!id,
    })),
  })

  const { nodes, edges } = useMemo(() => {
    const nodes: Node<FamilyNodeData>[] = []
    const edges: Edge[] = []
    const placed = new Set<string>([centerMember.id])
    const knownInHop1 = new Set(hop1Ids)

    nodes.push({
      id: centerMember.id,
      type: 'family',
      position: { x: 0, y: 0 },
      data: {
        label: centerMember.display_name,
        variant: 'center',
        role: null,
        slug: centerMember.slug,
      },
    })

    const HOP1_RADIUS = 240
    const HOP2_RADIUS = 480

    hop1.forEach((entry, idx) => {
      if (placed.has(entry.memberId)) return
      placed.add(entry.memberId)
      const angle = (idx / Math.max(hop1.length, 1)) * Math.PI * 2 - Math.PI / 2
      const x = Math.cos(angle) * HOP1_RADIUS
      const y = Math.sin(angle) * HOP1_RADIUS
      const m = memberMap[entry.memberId]
      nodes.push({
        id: entry.memberId,
        type: 'family',
        position: { x, y },
        data: {
          label: m?.display_name ?? entry.memberId.slice(0, 8) + '…',
          variant: 'direct',
          role: entry.role,
          slug: m?.slug ?? null,
        },
      })
      edges.push({
        id: `${centerMember.id}-${entry.memberId}-${entry.role}`,
        source: centerMember.id,
        target: entry.memberId,
        label: ROLE_LABEL[entry.role],
        labelStyle: { fontSize: 10, fill: '#a1a1aa' },
        labelBgStyle: { fill: '#18181b' },
        labelBgPadding: [4, 2],
        style: { stroke: '#52525b', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#52525b' },
      })
    })

    // Hop 2 — pulled from each loaded hop-1 member's family.
    const hop2Entries: { from: UUID; entry: { role: FamilyRole; memberId: UUID } }[] = []
    for (const q of hop1Queries) {
      const detail = q.data
      if (!detail) continue
      const sub = familyDictToEntries(detail.family as Record<string, unknown> | null)
      for (const entry of sub) {
        if (entry.memberId === centerMember.id) continue
        if (knownInHop1.has(entry.memberId)) continue
        hop2Entries.push({ from: detail.id, entry })
      }
    }
    // De-dup by target id (first reference wins).
    const seenHop2 = new Set<string>()
    const hop2Unique = hop2Entries.filter((h) => {
      if (seenHop2.has(h.entry.memberId)) return false
      seenHop2.add(h.entry.memberId)
      return true
    })

    hop2Unique.forEach((h, idx) => {
      if (placed.has(h.entry.memberId)) {
        edges.push({
          id: `${h.from}-${h.entry.memberId}-${h.entry.role}`,
          source: h.from,
          target: h.entry.memberId,
          label: ROLE_LABEL[h.entry.role],
          labelStyle: { fontSize: 10, fill: '#71717a' },
          labelBgStyle: { fill: '#18181b' },
          labelBgPadding: [4, 2],
          style: { stroke: '#3f3f46', strokeWidth: 1, strokeDasharray: '4 3' },
        })
        return
      }
      placed.add(h.entry.memberId)
      const angle = (idx / Math.max(hop2Unique.length, 1)) * Math.PI * 2 - Math.PI / 2
      const x = Math.cos(angle) * HOP2_RADIUS
      const y = Math.sin(angle) * HOP2_RADIUS
      const m = memberMap[h.entry.memberId]
      nodes.push({
        id: h.entry.memberId,
        type: 'family',
        position: { x, y },
        data: {
          label: m?.display_name ?? h.entry.memberId.slice(0, 8) + '…',
          variant: 'indirect',
          role: null,
          slug: m?.slug ?? null,
        },
      })
      edges.push({
        id: `${h.from}-${h.entry.memberId}-${h.entry.role}`,
        source: h.from,
        target: h.entry.memberId,
        label: ROLE_LABEL[h.entry.role],
        labelStyle: { fontSize: 10, fill: '#71717a' },
        labelBgStyle: { fill: '#18181b' },
        labelBgPadding: [4, 2],
        style: { stroke: '#3f3f46', strokeWidth: 1, strokeDasharray: '4 3' },
      })
    })

    return { nodes, edges }
  }, [centerMember, hop1, hop1Ids, hop1Queries, memberMap])

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node<FamilyNodeData>) => {
      if (node.id === centerMember.id) return
      const id = node.data.slug ?? node.id
      navigate({ to: '/members/$id', params: { id } })
    },
    [navigate, centerMember.id],
  )

  if (hop1.length === 0) {
    return <p className="py-6 text-sm text-zinc-400">No family links to graph.</p>
  }

  const hop2Loading = hop1Queries.some((q) => q.isLoading)

  return (
    <div className="relative h-[480px] overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        onNodeClick={onNodeClick}
        proOptions={{ hideAttribution: true }}
        panOnScroll
        zoomOnScroll={false}
        nodesDraggable={false}
        className="bg-zinc-950"
      >
        <Background color="#27272a" gap={20} size={1} />
        <Controls className="!bg-zinc-900 !border-zinc-700 [&>button]:!bg-zinc-900 [&>button]:!border-zinc-700 [&>button]:!text-zinc-400 [&>button:hover]:!bg-zinc-800" />
      </ReactFlow>
      <div className="pointer-events-none absolute bottom-2 right-2 rounded-md border border-zinc-800 bg-zinc-950/90 px-2 py-1 text-[10px] text-zinc-400">
        {hop2Loading ? 'Loading hop 2…' : 'Solid = direct · Dashed = grand-relation'}
      </div>
    </div>
  )
}

export default MemberFamilyGraph
